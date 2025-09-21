from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QDrag
from ..utils.config_utils import get_brush_icon_size

class ClickableGridWidget(QWidget):
    """A clickable and droppable grid widget for brush presets"""
    
    def __init__(self, grid_info, parent_docker):
        super().__init__()
        self.grid_info = grid_info
        self.parent_docker = parent_docker
        self.drag_start_position = QPoint()
        self.setAcceptDrops(True)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for grid dragging"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Only start grid drag if clicking on empty space (not on brush buttons)
        widget_under_mouse = self.childAt(event.pos())
        if widget_under_mouse and hasattr(widget_under_mouse, 'preset'):
            return
        
        self.start_grid_drag()
    
    def start_grid_drag(self):
        """Start grid drag operation"""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"grid:{self.grid_info['name']}")
        drag.setMimeData(mime_data)
        
        drop_action = drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("brush_preset:"):
                event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("brush_preset:"):
                self.handle_brush_drop(event, text)
    
    def handle_brush_drop(self, event, text):
        """Handle brush preset drop"""
        preset_name = text.split(":", 1)[1]
        
        # Find the source preset and grid
        source_preset, source_grid, source_index = self.find_source_preset(preset_name)
        
        if source_preset and source_grid:
            drop_pos = event.pos()
            target_index = self.calculate_drop_position(drop_pos)
            
            # Remove from old position
            source_grid['brush_presets'].pop(source_index)
            
            if source_grid == self.grid_info:
                # Reorder within same grid
                target_index = min(target_index, len(source_grid['brush_presets']))
                source_grid['brush_presets'].insert(target_index, source_preset)
                self.parent_docker.update_grid(source_grid)
            else:
                # Move between grids
                target_index = min(target_index, len(self.grid_info['brush_presets']))
                self.grid_info['brush_presets'].insert(target_index, source_preset)
                self.parent_docker.update_grid(source_grid)
                self.parent_docker.update_grid(self.grid_info)
            
            self.parent_docker.save_grids_data()
            event.acceptProposedAction()
    
    def find_source_preset(self, preset_name):
        """Find source preset in grids"""
        for grid in self.parent_docker.grids:
            for i, preset in enumerate(grid['brush_presets']):
                if preset.name() == preset_name:
                    return preset, grid, i
        return None, None, -1
    
    def calculate_drop_position(self, drop_pos):
        """Calculate target position for drop"""
        from ..utils.config_utils import get_dynamic_columns
        
        columns = get_dynamic_columns()
        button_size = get_brush_icon_size()
        spacing = 2
        
        col = min(drop_pos.x() // (button_size + spacing), columns - 1)
        row = drop_pos.y() // (button_size + spacing)
        return row * columns + col

class DraggableGridContainer(QWidget):
    """Container for draggable grids"""
    
    def __init__(self, grid_info, parent_docker):
        super().__init__()
        self.grid_info = grid_info
        self.parent_docker = parent_docker