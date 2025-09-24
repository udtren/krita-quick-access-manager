from PyQt5.QtWidgets import QPushButton, QApplication
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QDrag, QIcon, QPixmap
from ..utils.config_utils import get_brush_icon_size


class DraggableBrushButton(QPushButton):
    """A draggable button for brush presets"""

    def __init__(self, preset, grid_info, parent_docker):
        super().__init__()
        self.preset = preset
        self.grid_info = grid_info
        self.parent_docker = parent_docker
        self.drag_start_position = QPoint()

        self.setup_button()
        self.setup_connections()

    def setup_button(self):
        """Setup button appearance and properties"""
        icon_size = get_brush_icon_size()
        self.setToolTip(self.preset.name())
        self.setFixedSize(icon_size, icon_size)

        # Set brush preset icon
        if self.preset.image():
            pixmap = QPixmap.fromImage(self.preset.image())
            icon = QIcon(pixmap)
            self.setIcon(icon)
            self.setIconSize(self.size())
        else:
            self.setText(self.preset.name()[:2])  # Fallback text

    def setup_connections(self):
        """Setup button connections"""
        self.clicked.connect(
            lambda: self.parent_docker.select_brush_preset(self.preset)
        )

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if (
            event.button() == Qt.LeftButton
            and QApplication.keyboardModifiers() == Qt.ControlModifier
        ):
            self.drag_start_position = event.pos()

        # Ctrl+Right click to delete
        if (
            event.button() == Qt.RightButton
            and QApplication.keyboardModifiers() == Qt.ControlModifier
        ):
            self.remove_from_grid()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if not (event.buttons() & Qt.LeftButton):
            return

        if QApplication.keyboardModifiers() != Qt.ControlModifier:
            return

        if (
            event.pos() - self.drag_start_position
        ).manhattanLength() < QApplication.startDragDistance():
            return

        self.start_drag()

    def start_drag(self):
        """Start drag operation"""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"brush_preset:{self.preset.name()}")
        drag.setMimeData(mime_data)

        # Set drag pixmap
        if self.preset.image():
            pixmap = QPixmap.fromImage(self.preset.image()).scaled(
                32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.gray)

        drag.setPixmap(self.icon().pixmap(32, 32))
        drag.setHotSpot(QPoint(16, 16))

        drop_action = drag.exec_(Qt.MoveAction)

    def remove_from_grid(self):
        """Remove this preset from the grid"""
        for i, p in enumerate(self.grid_info["brush_presets"]):
            if p.name() == self.preset.name():
                self.grid_info["brush_presets"].pop(i)
                self.parent_docker.update_grid(self.grid_info)
                self.parent_docker.save_grids_data()
                break
