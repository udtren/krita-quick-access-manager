from krita import Krita  # type: ignore

from ..compat import QApplication, QEvent, QObject, Qt
from ..focus_utils import is_text_input_focused

_KEY_EVENT_TYPES = frozenset((QEvent.KeyPress, QEvent.KeyRelease))

_ALL_MODIFIERS = (
    Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier
)

# Pressing a modifier key reports that same modifier in event.modifiers(), so it
# has to be masked out before comparing against the configured combo.
_SELF_MODIFIER = {
    Qt.Key_Shift: Qt.ShiftModifier,
    Qt.Key_Control: Qt.ControlModifier,
    Qt.Key_Alt: Qt.AltModifier,
    Qt.Key_Meta: Qt.MetaModifier,
}

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
    """Convert a key name string to a Qt key code."""
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


class HeldKeyListener(QObject):
    """Base for the application-wide "do X while this key is held" listeners.

    Subclasses implement `on_activate()` / `on_deactivate()`. Set
    `cancel_on_other_key` to deactivate as soon as another key joins the press,
    which is what the erase / preserve-alpha toggles want.
    """

    cancel_on_other_key = False

    def __init__(self, key_string: str = ""):
        super().__init__()
        self._modifier_flags, self._key_code = (
            _parse_combo(key_string) if key_string else (None, None)
        )
        self._key_active = False
        self._combo_detected = False
        self._installed = False
        if self._key_code is not None and self._should_install():
            QApplication.instance().installEventFilter(self)
            self._installed = True

    def _should_install(self):
        return True

    def remove(self):
        if not self._installed:
            return
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self._installed = False

    def on_activate(self):
        raise NotImplementedError

    def on_deactivate(self):
        raise NotImplementedError

    def _matches(self, event):
        if event.key() != self._key_code:
            return False
        # Compare the full modifier state so a plain "A" binding does not also
        # fire on Ctrl+A, ignoring the bit contributed by the key itself.
        expected = self._modifier_flags or Qt.NoModifier
        actual = event.modifiers() & _ALL_MODIFIERS
        self_modifier = _SELF_MODIFIER.get(self._key_code)
        if self_modifier is not None:
            actual = actual & (_ALL_MODIFIERS ^ self_modifier)
        return actual == expected

    def eventFilter(self, _, event):
        t = event.type()
        if t not in _KEY_EVENT_TYPES:
            return False
        if event.isAutoRepeat():
            return False

        if t == QEvent.KeyPress:
            # A release is never gated, otherwise a held key could get stuck on
            # when focus moves into a text field mid-press.
            if not self._key_active and is_text_input_focused():
                return False
            if self._matches(event):
                if not self._key_active:
                    self._key_active = True
                    self._combo_detected = False
                    self.on_activate()
            elif (
                self.cancel_on_other_key
                and self._key_active
                and not self._combo_detected
            ):
                self._combo_detected = True
                self.on_deactivate()

        elif t == QEvent.KeyRelease and event.key() == self._key_code:
            if self._key_active:
                self._key_active = False
                if not self._combo_detected:
                    self.on_deactivate()

        return False


class _CheckableActionListener(HeldKeyListener):
    """Holds a checkable Krita action on while the configured key is held."""

    action_id = ""
    cancel_on_other_key = True

    def _action(self):
        return Krita.instance().action(self.action_id)

    def _set_checked(self, checked):
        action = self._action()
        if action:
            action.setChecked(checked)

    def on_activate(self):
        self._set_checked(True)

    def on_deactivate(self):
        self._set_checked(False)


class AltEraseListener(_CheckableActionListener):
    """Activates Krita's erase mode while a configurable key is held - but only
    when no other key is pressed simultaneously.
    """

    action_id = "erase_action"


class PreserveAlphaListener(_CheckableActionListener):
    """Temporarily enables Krita's Preserve Alpha mode while a configurable key is held."""

    action_id = "preserve_alpha"


class TempBrushSetListener(HeldKeyListener):
    """Temporarily switches to a configured brush preset while a combo key is held,
    then restores the original brush on release.
    """

    def __init__(
        self, key_string: str = "", brush_name: str = "", size_scale: float = 0.0
    ):
        self._brush_name = brush_name
        self._size_scale = size_scale
        self._original_preset = None
        self._original_size = None
        super().__init__(key_string)

    def _should_install(self):
        return bool(self._brush_name)

    def on_activate(self):
        self._switch_to_temp_brush()

    def on_deactivate(self):
        self._restore_original_brush()

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


class SelectOutlineListener(HeldKeyListener):
    """Switches to the Freehand Selection tool while a configurable key is held,
    then returns to the Brush tool on release.
    """

    def _trigger(self, action_id):
        action = Krita.instance().action(action_id)
        if action:
            action.trigger()

    def on_activate(self):
        self._trigger("KisToolSelectOutline")

    def on_deactivate(self):
        self._trigger("KritaShape/KisToolBrush")
