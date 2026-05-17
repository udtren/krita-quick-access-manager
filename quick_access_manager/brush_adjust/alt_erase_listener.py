from ..compat import QObject, QEvent, Qt, QApplication
from krita import Krita  # type: ignore

_KEY_EVENT_TYPES = frozenset((QEvent.KeyPress, QEvent.KeyRelease))

# Map of key name strings to Qt key codes
_KEY_MAP = {
    "Alt": Qt.Key_Alt,
    "Shift": Qt.Key_Shift,
    "Ctrl": Qt.Key_Control,
    "Meta": Qt.Key_Meta,
    "Tab": Qt.Key_Tab,
    "Space": Qt.Key_Space,
    "Backspace": Qt.Key_Backspace,
    "Escape": Qt.Key_Escape,
    "Return": Qt.Key_Return,
    "Enter": Qt.Key_Enter,
    **{chr(c): getattr(Qt, f"Key_{chr(c)}") for c in range(ord("A"), ord("Z") + 1)},
    **{str(d): getattr(Qt, f"Key_{d}") for d in range(10)},
    **{f"F{i}": getattr(Qt, f"Key_F{i}") for i in range(1, 13)},
}

_MODIFIER_MAP = {
    "Alt": Qt.AltModifier,
    "Ctrl": Qt.ControlModifier,
    "Shift": Qt.ShiftModifier,
    "Meta": Qt.MetaModifier,
}


def resolve_key(key_string: str) -> int:
    """Convert a key name string to a Qt key code.

    Args:
        key_string: Key name (e.g., "Alt", "Shift", "A", "F1")

    Returns:
        Qt key code, or Qt.Key_Alt if the key name is unrecognised
    """
    return _KEY_MAP.get(key_string, Qt.Key_Alt)


def _parse_combo(key_string: str):
    """Parse a combo key string into (modifier_flags, key_code).

    Supports plain keys ("A", "F1", "Alt") and combos ("Alt+1", "Ctrl+F1", "Ctrl+Alt+A").
    A single modifier name ("Alt", "Shift") is treated as a plain key press, not a modifier.
    Returns (None, None) for empty or unrecognised input.
    """
    if not key_string:
        return None, None
    parts = [p.strip() for p in key_string.split("+")]
    modifier_flags = Qt.NoModifier
    key_code = None
    for part in parts:
        if part in _MODIFIER_MAP and len(parts) > 1:
            modifier_flags = modifier_flags | _MODIFIER_MAP[part]
        elif part in _KEY_MAP:
            key_code = _KEY_MAP[part]
    return modifier_flags, key_code


class AltEraseListener(QObject):
    """Application-level event filter that activates Krita's erase mode while
    a configurable key is held — but only when no other key is pressed simultaneously.

    Behaviour:
    - Key pressed alone  : always enable erase.
    - Another key pressed while held : immediately cancel erase activation.
    - Key released : always disable erase (unless combo cancelled it already).
    """

    def __init__(self, key_string: str = ""):
        super().__init__()
        self._modifier_flags, self._key_code = _parse_combo(key_string) if key_string else (None, None)
        self._key_active = False
        self._combo_detected = False
        if self._key_code is not None:
            QApplication.instance().installEventFilter(self)

    def remove(self):
        """Uninstall the event filter. Call this when the owner widget is destroyed."""
        QApplication.instance().removeEventFilter(self)

    def _erase_action(self):
        return Krita.instance().action("erase_action")

    def eventFilter(self, _, event):
        t = event.type()
        if t not in _KEY_EVENT_TYPES:
            return False

        if t == QEvent.KeyPress and not event.isAutoRepeat():
            key_matches = event.key() == self._key_code
            if self._modifier_flags != Qt.NoModifier:
                key_matches = key_matches and event.modifiers() == self._modifier_flags
            if key_matches:
                if not self._key_active:
                    self._key_active = True
                    self._combo_detected = False
                    action = self._erase_action()
                    if action:
                        action.setChecked(True)
            elif self._key_active and not self._combo_detected:
                self._combo_detected = True
                action = self._erase_action()
                if action:
                    action.setChecked(False)

        elif t == QEvent.KeyRelease and not event.isAutoRepeat() and event.key() == self._key_code:
            if self._key_active:
                self._key_active = False
                if not self._combo_detected:
                    action = self._erase_action()
                    if action:
                        action.setChecked(False)

        return False


class PreserveAlphaListener(QObject):
    """Temporarily enables Krita's Preserve Alpha mode while a configurable key is held.

    Behaviour mirrors AltEraseListener: key held alone enables, another key
    pressed simultaneously cancels, key release disables.
    Empty key_string disables the listener entirely.
    """

    def __init__(self, key_string: str = ""):
        super().__init__()
        self._modifier_flags, self._key_code = _parse_combo(key_string) if key_string else (None, None)
        self._key_active = False
        self._combo_detected = False
        if self._key_code is not None:
            QApplication.instance().installEventFilter(self)

    def remove(self):
        QApplication.instance().removeEventFilter(self)

    def _action(self):
        return Krita.instance().action("preserve_alpha")

    def eventFilter(self, _, event):
        t = event.type()
        if t not in _KEY_EVENT_TYPES:
            return False

        if t == QEvent.KeyPress and not event.isAutoRepeat():
            key_matches = event.key() == self._key_code
            if self._modifier_flags != Qt.NoModifier:
                key_matches = key_matches and event.modifiers() == self._modifier_flags
            if key_matches:
                if not self._key_active:
                    self._key_active = True
                    self._combo_detected = False
                    action = self._action()
                    if action:
                        action.setChecked(True)
            elif self._key_active and not self._combo_detected:
                self._combo_detected = True
                action = self._action()
                if action:
                    action.setChecked(False)

        elif t == QEvent.KeyRelease and not event.isAutoRepeat() and event.key() == self._key_code:
            if self._key_active:
                self._key_active = False
                if not self._combo_detected:
                    action = self._action()
                    if action:
                        action.setChecked(False)

        return False


class TempBrushSetListener(QObject):
    """Temporarily switches to a configured brush preset while a combo key is held,
    then restores the original brush on release.

    Supports plain keys ("A", "F1") and combos ("Alt+1", "Ctrl+F1").
    Empty key_string or brush_name disables the listener entirely.
    """

    def __init__(self, key_string: str = "", brush_name: str = "", size_scale: float = 0.0):
        super().__init__()
        self._modifier_flags, self._key_code = _parse_combo(key_string) if key_string else (None, None)
        self._brush_name = brush_name
        self._size_scale = size_scale
        self._key_active = False
        self._original_preset = None
        self._original_size = None
        if self._key_code is not None and self._brush_name:
            QApplication.instance().installEventFilter(self)

    def remove(self):
        QApplication.instance().removeEventFilter(self)

    def eventFilter(self, _, event):
        t = event.type()
        if t not in _KEY_EVENT_TYPES:
            return False

        if t == QEvent.KeyPress and not event.isAutoRepeat():
            if event.key() == self._key_code and event.modifiers() == self._modifier_flags:
                if not self._key_active:
                    self._key_active = True
                    self._switch_to_temp_brush()

        elif t == QEvent.KeyRelease and not event.isAutoRepeat():
            if event.key() == self._key_code and self._key_active:
                self._key_active = False
                self._restore_original_brush()

        return False

    def _switch_to_temp_brush(self):
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            self._original_preset = view.currentBrushPreset()
            if self._size_scale > 0:
                self._original_size = view.brushSize()
            target = app.resources("preset").get(self._brush_name)
            if target:
                view.setCurrentBrushPreset(target)
                if self._size_scale > 0:
                    view.setBrushSize(self._original_size * self._size_scale)

    def _restore_original_brush(self):
        if self._original_preset is None:
            return
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            view.setCurrentBrushPreset(self._original_preset)
            if self._size_scale > 0 and self._original_size is not None:
                view.setBrushSize(self._original_size)
        self._original_preset = None
        self._original_size = None


class SelectOutlineListener(QObject):
    """Switches to the Freehand Selection tool while a configurable key is held,
    then returns to the Brush tool on release.

    Combos (other keys pressed simultaneously) are allowed.
    Empty key_string disables the listener entirely.
    """

    def __init__(self, key_string: str = ""):
        super().__init__()
        self._modifier_flags, self._key_code = _parse_combo(key_string) if key_string else (None, None)
        self._key_active = False
        if self._key_code is not None:
            QApplication.instance().installEventFilter(self)

    def remove(self):
        QApplication.instance().removeEventFilter(self)

    def eventFilter(self, _, event):
        t = event.type()
        if t not in _KEY_EVENT_TYPES:
            return False

        if t == QEvent.KeyPress and not event.isAutoRepeat():
            key_matches = event.key() == self._key_code
            if self._modifier_flags != Qt.NoModifier:
                key_matches = key_matches and event.modifiers() == self._modifier_flags
            if key_matches and not self._key_active:
                self._key_active = True
                action = Krita.instance().action("KisToolSelectOutline")
                if action:
                    action.trigger()

        elif t == QEvent.KeyRelease and not event.isAutoRepeat() and event.key() == self._key_code:
            if self._key_active:
                self._key_active = False
                action = Krita.instance().action("KritaShape/KisToolBrush")
                if action:
                    action.trigger()

        return False
