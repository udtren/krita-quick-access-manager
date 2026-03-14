from PyQt5.QtCore import QObject, QEvent, Qt
from PyQt5.QtWidgets import QApplication
from krita import Krita  # type: ignore


class AltEraseListener(QObject):
    """Application-level event filter that temporarily activates Krita's erase
    mode while the Alt key is held.

    Behaviour:
    - Alt pressed  : record original erase state; activate erase if it was off.
    - Alt released : if erase was originally off, deactivate it again.
                     If it was already on before Alt, leave it on.
    """

    def __init__(self):
        super().__init__()
        self._alt_active = False
        self._was_erasing = False
        QApplication.instance().installEventFilter(self)

    def remove(self):
        """Uninstall the event filter. Call this when the owner widget is destroyed."""
        QApplication.instance().removeEventFilter(self)

    def _erase_action(self):
        return Krita.instance().action("erase_action")

    def eventFilter(self, obj, event):
        t = event.type()

        if t == QEvent.KeyPress and not event.isAutoRepeat() and event.key() == Qt.Key_Alt:
            if not self._alt_active:
                self._alt_active = True
                action = self._erase_action()
                if action:
                    self._was_erasing = action.isChecked()
                    if not self._was_erasing:
                        action.setChecked(True)

        elif t == QEvent.KeyRelease and not event.isAutoRepeat() and event.key() == Qt.Key_Alt:
            if self._alt_active:
                self._alt_active = False
                if not self._was_erasing:
                    action = self._erase_action()
                    if action:
                        action.setChecked(False)

        return False  # never consume the event
