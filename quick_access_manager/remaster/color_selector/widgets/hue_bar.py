from ...compat import QColor, QLinearGradient, QPainter, Qt, QWidget, pyqtSignal


class HueBar(QWidget):
    """Vertical hue bar - full spectrum top to bottom."""

    hueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(30)
        self.setMinimumHeight(100)
        self._hue = 0
        self._pressed = False

    def hue(self):
        return self._hue

    def setHue(self, h):
        self._hue = max(0, min(359, h))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, 0, h)
        for i in range(7):
            grad.setColorAt(i / 6, QColor.fromHsv(int(i * 360 / 6) % 360, 255, 255))
        painter.fillRect(0, 0, w, h, grad)

        marker_y = int((self._hue / 360.0) * h)
        painter.setPen(Qt.white)
        painter.drawRect(0, marker_y - 2, w - 1, 4)
        painter.setPen(Qt.black)
        painter.drawRect(1, marker_y - 1, w - 3, 2)
        painter.end()

    def _pick(self, pos):
        h = self.height()
        y = max(0, min(pos.y(), h - 1))
        self._hue = int((y / h) * 360) % 360
        self.update()
        self.hueChanged.emit(self._hue)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._pick(event.pos())

    def mouseReleaseEvent(self, event):
        self._pressed = False
