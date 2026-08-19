import math

from ...compat import QBrush, QColor, QPainter, QPen, Qt, QWidget, pyqtSignal


class CircularRotationWidget(QWidget):
    """Custom circular rotation control widget"""

    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.value = 0
        self.dragging = False
        self.setMouseTracking(True)

    def setValue(self, value):
        self.value = max(0, min(360, value))
        self.update()

    def getValue(self):
        return self.value

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 5

        painter.setPen(QPen(QColor(128, 128, 128), 2))
        painter.setBrush(QBrush(QColor(167, 167, 167)))
        painter.drawEllipse(
            center_x - radius, center_y - radius, radius * 2, radius * 2
        )

        angle_rad = math.radians(-self.value)
        end_x = center_x + (radius - 10) * math.cos(angle_rad)
        end_y = center_y + (radius - 10) * math.sin(angle_rad)

        painter.setPen(QPen(QColor(10, 45, 80), 3))
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))

        painter.setBrush(QBrush(QColor(10, 45, 80)))
        painter.setPen(QPen(QColor(10, 45, 80)))
        painter.drawEllipse(center_x - 3, center_y - 3, 6, 6)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.updateValueFromMouse(event.pos())

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.updateValueFromMouse(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def updateValueFromMouse(self, pos):
        center_x = self.width() // 2
        center_y = self.height() // 2

        dx = pos.x() - center_x
        dy = pos.y() - center_y

        angle_rad = math.atan2(dy, dx)
        angle_deg = -math.degrees(angle_rad) + 90

        if angle_deg < 0:
            angle_deg += 360
        elif angle_deg >= 360:
            angle_deg -= 360

        old_value = self.value
        self.value = int(angle_deg)

        if old_value != self.value:
            self.update()
            self.valueChanged.emit(self.value)
