from ...compat import QColor, QPainter, Qt, QWidget, pyqtSignal


class FgBgColorWidget(QWidget):
    """Stacked foreground/background color swatch. Click either to swap them."""

    swapRequested = pyqtSignal()

    _SWATCH = 22
    _OFFSET = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fg = QColor(0, 0, 0)
        self._bg = QColor(255, 255, 255)
        total = self._SWATCH + self._OFFSET
        self.setFixedSize(total, total)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to swap foreground / background")

    def setColors(self, fg, bg):
        if fg == self._fg and bg == self._bg:
            return
        self._fg = fg
        self._bg = bg
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        sw = self._SWATCH
        off = self._OFFSET
        painter.fillRect(off, off, sw, sw, self._bg)
        painter.setPen(Qt.black)
        painter.drawRect(off, off, sw - 1, sw - 1)
        painter.fillRect(0, 0, sw, sw, self._fg)
        painter.setPen(Qt.black)
        painter.drawRect(0, 0, sw - 1, sw - 1)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.swapRequested.emit()
