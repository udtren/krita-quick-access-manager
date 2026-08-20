from ...compat import QColor, QLinearGradient, QPainter, QPoint, Qt, QWidget, pyqtSignal


class SVBox(QWidget):
    """Saturation (x-axis) / Value (y-axis) picker box."""

    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 100)
        self._hue = 0
        self._sat = 255
        self._val = 255
        self._pressed = False

    def setHue(self, h):
        if h == self._hue:
            return
        self._hue = h
        self.update()

    def setSatVal(self, s, v):
        self._sat = s
        self._val = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        grad_s = QLinearGradient(0, 0, w, 0)
        grad_s.setColorAt(0, Qt.white)
        grad_s.setColorAt(1, QColor.fromHsv(self._hue, 255, 255))
        painter.fillRect(0, 0, w, h, grad_s)

        grad_v = QLinearGradient(0, 0, 0, h)
        grad_v.setColorAt(0, QColor(0, 0, 0, 0))
        grad_v.setColorAt(1, QColor(0, 0, 0, 255))
        painter.fillRect(0, 0, w, h, grad_v)

        cx = int((self._sat / 255.0) * (w - 1))
        cy = int(((255 - self._val) / 255.0) * (h - 1))
        for color, radius in [(Qt.black, 6), (Qt.white, 5)]:
            painter.setPen(color)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(cx, cy), radius, radius)

        painter.end()

    def _pick(self, pos):
        w, h = self.width(), self.height()
        x = max(0, min(pos.x(), w - 1))
        y = max(0, min(pos.y(), h - 1))
        self._sat = int((x / (w - 1)) * 255) if w > 1 else 255
        self._val = 255 - (int((y / (h - 1)) * 255) if h > 1 else 0)
        self.update()
        self.colorChanged.emit(QColor.fromHsv(self._hue, self._sat, self._val))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._pick(event.pos())

    def mouseReleaseEvent(self, event):
        self._pressed = False
