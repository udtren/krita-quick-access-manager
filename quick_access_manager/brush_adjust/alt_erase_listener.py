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
    """Application-level event filter that activates Krita's erase mode while
    a configurable key is held.

    Behaviour:
    - Key pressed : always enable erase.
    - Key released : always disable erase.
    """

    def __init__(self, key_string: str = "Alt"):
        super().__init__()
        self._key_code = resolve_key(key_string)
        self._key_active = False
        QApplication.instance().installEventFilter(self)

    def remove(self):
        """Uninstall the event filter. Call this when the owner widget is destroyed."""
        QApplication.instance().removeEventFilter(self)

    def _erase_action(self):
        return Krita.instance().action("erase_action")

    def eventFilter(self, obj, event):
        t = event.type()

        if t == QEvent.KeyPress and not event.isAutoRepeat() and event.key() == self._key_code:
            if not self._key_active:
                self._key_active = True
                action = self._erase_action()
                if action:
                    action.setChecked(True)

        elif t == QEvent.KeyRelease and not event.isAutoRepeat() and event.key() == self._key_code:
            if self._key_active:
                self._key_active = False
                action = self._erase_action()
                if action:
                    action.setChecked(False)

        return False  # never consume the event
