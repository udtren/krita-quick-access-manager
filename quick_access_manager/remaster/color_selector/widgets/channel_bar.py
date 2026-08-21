from ...compat import QColor, QLinearGradient, QPainter, Qt, QWidget, pyqtSignal


class ChannelBar(QWidget):
    """Horizontal gradient bar for a single color channel (H/S/V/R/G/B)."""

    valueChanged = pyqtSignal(int)

    def __init__(self, channel, parent=None):
        super().__init__(parent)
        self._channel = channel
        self._h = 0
        self._s = 100
        self._v = 100
        self._r = 100
        self._g = 0
        self._b = 0
        self._value = 0
        self._pressed = False
        self.setFixedHeight(16)
        self.setMinimumWidth(80)

    def _max_value(self):
        return 359 if self._channel == "H" else 100

    def setColor(self, h, s, v, r, g, b):
        self._h, self._s, self._v = h, s, v
        self._r, self._g, self._b = r, g, b
        ch = self._channel
        if ch == "H":
            self._value = h
        elif ch == "S":
            self._value = s
        elif ch == "V":
            self._value = v
        elif ch == "R":
            self._value = r
        elif ch == "G":
            self._value = g
        elif ch == "B":
            self._value = b
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        def q(x):
            return round(x * 255 / 100)

        s255, v255 = q(self._s), q(self._v)
        r255, g255, b255 = q(self._r), q(self._g), q(self._b)

        grad = QLinearGradient(0, 0, w, 0)
        ch = self._channel
        if ch == "H":
            for i in range(7):
                grad.setColorAt(
                    i / 6, QColor.fromHsv(int(i * 360 / 6) % 360, s255, v255)
                )
        elif ch == "S":
            grad.setColorAt(0, QColor.fromHsv(self._h, 0, v255))
            grad.setColorAt(1, QColor.fromHsv(self._h, 255, v255))
        elif ch == "V":
            grad.setColorAt(0, QColor.fromHsv(self._h, s255, 0))
            grad.setColorAt(1, QColor.fromHsv(self._h, s255, 255))
        elif ch == "R":
            grad.setColorAt(0, QColor(0, g255, b255))
            grad.setColorAt(1, QColor(255, g255, b255))
        elif ch == "G":
            grad.setColorAt(0, QColor(r255, 0, b255))
            grad.setColorAt(1, QColor(r255, 255, b255))
        elif ch == "B":
            grad.setColorAt(0, QColor(r255, g255, 0))
            grad.setColorAt(1, QColor(r255, g255, 255))
        painter.fillRect(0, 0, w, h, grad)

        max_val = self._max_value()
        marker_x = int((self._value / max_val) * (w - 1)) if max_val > 0 else 0
        painter.setPen(Qt.white)
        painter.drawRect(marker_x - 2, 0, 4, h - 1)
        painter.setPen(Qt.black)
        painter.drawRect(marker_x - 1, 1, 2, h - 3)
        painter.end()

    def _pick(self, pos):
        w = self.width()
        x = max(0, min(pos.x(), w - 1))
        max_val = self._max_value()
        self._value = int((x / (w - 1)) * max_val) if w > 1 else 0
        self.update()
        self.valueChanged.emit(self._value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._pick(event.pos())

    def mouseReleaseEvent(self, event):
        self._pressed = False
