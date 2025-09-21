from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
import math


class CircularRotationWidget(QWidget):
    """Custom circular rotation control widget"""

    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)  # Fixed square size
        self.value = 0  # 0-360 degrees
        self.dragging = False
        self.setMouseTracking(True)

    def setValue(self, value):
        """Set the rotation value (0-360)"""
        self.value = max(0, min(360, value))
        self.update()

    def getValue(self):
        """Get the current rotation value"""
        return self.value

    def paintEvent(self, event):
        """Custom paint event to draw the circular control"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get widget center and radius
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 5

        # Draw outer circle (track)
        painter.setPen(QPen(QColor(128, 128, 128), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(
            center_x - radius, center_y - radius, radius * 2, radius * 2
        )

        # Draw rotation indicator line
        angle_rad = math.radians(self.value - 90)  # -90 to start from top
        end_x = center_x + (radius - 10) * math.cos(angle_rad)
        end_y = center_y + (radius - 10) * math.sin(angle_rad)

        painter.setPen(QPen(QColor(50, 150, 250), 3))
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))

        # Draw center dot
        painter.setBrush(QBrush(QColor(50, 150, 250)))
        painter.setPen(QPen(QColor(50, 150, 250)))
        painter.drawEllipse(center_x - 3, center_y - 3, 6, 6)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.updateValueFromMouse(event.pos())

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.dragging:
            self.updateValueFromMouse(event.pos())

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def updateValueFromMouse(self, pos):
        """Update rotation value based on mouse position"""
        center_x = self.width() // 2
        center_y = self.height() // 2

        # Calculate angle from center to mouse position
        dx = pos.x() - center_x
        dy = pos.y() - center_y

        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) + 90  # +90 to start from top

        # Normalize to 0-360
        if angle_deg < 0:
            angle_deg += 360
        elif angle_deg >= 360:
            angle_deg -= 360

        old_value = self.value
        self.value = int(angle_deg)

        if old_value != self.value:
            self.update()
            self.valueChanged.emit(self.value)
