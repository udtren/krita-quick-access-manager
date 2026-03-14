from PyQt5.QtCore import QObject, QEvent, Qt
from PyQt5.QtWidgets import QApplication
from krita import Krita  # type: ignore

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


def resolve_key(key_string: str) -> int:
    """Convert a key name string to a Qt key code.

    Args:
        key_string: Key name (e.g., "Alt", "Shift", "A", "F1")

    Returns:
        Qt key code, or Qt.Key_Alt if the key name is unrecognised
    """
    return _KEY_MAP.get(key_string, Qt.Key_Alt)


class AltEraseListener(QObject):
    """Application-level event filter that temporarily activates Krita's erase
    mode while a configurable key is held — but only when no other key is
    pressed simultaneously.

    Behaviour:
    - Key pressed alone : record original erase state; activate erase if it was off.
    - Another key pressed while held : cancel the erase activation immediately.
    - Key released : if no combo was detected and erase was originally off,
                     deactivate erase. Otherwise leave erase state unchanged.
    """

    def __init__(self, key_string: str = "Alt"):
        super().__init__()
        self._key_code = resolve_key(key_string)
        self._key_active = False
        self._was_erasing = False
        self._combo_detected = False  # another key pressed while ours was held
        QApplication.instance().installEventFilter(self)

    def remove(self):
        """Uninstall the event filter. Call this when the owner widget is destroyed."""
        QApplication.instance().removeEventFilter(self)

    def _erase_action(self):
        return Krita.instance().action("erase_action")

    def eventFilter(self, obj, event):
        t = event.type()

        if t == QEvent.KeyPress and not event.isAutoRepeat():
            if event.key() == self._key_code:
                if not self._key_active:
                    self._key_active = True
                    self._combo_detected = False
                    action = self._erase_action()
                    if action:
                        self._was_erasing = action.isChecked()
                        if not self._was_erasing:
                            action.setChecked(True)
            elif self._key_active and not self._combo_detected:
                # Another key pressed while ours is held — cancel erase activation
                self._combo_detected = True
                if not self._was_erasing:
                    action = self._erase_action()
                    if action:
                        action.setChecked(False)

        elif t == QEvent.KeyRelease and not event.isAutoRepeat() and event.key() == self._key_code:
            if self._key_active:
                self._key_active = False
                if not self._combo_detected and not self._was_erasing:
                    action = self._erase_action()
                    if action:
                        action.setChecked(False)

        return False  # never consume the event
