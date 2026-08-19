from krita import (
    Krita,  # type: ignore  # noqa: F401 (kept for parity with legacy import)
)

from ....compat import QEvent, QObject


class ntAdjustToSubwindowFilter(QObject):
    """Event filter: keep a target widget positioned to the current view when
    the subwindow area moves, resizes, or is activated."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target = None

    def eventFilter(self, obj, e):
        if self.target and (
            e.type() == QEvent.Move
            or e.type() == QEvent.Resize
            or e.type() == QEvent.WindowActivate
        ):
            self.target.adjustToView()

        return False

    def setTargetWidget(self, wdgt):
        self.target = wdgt
