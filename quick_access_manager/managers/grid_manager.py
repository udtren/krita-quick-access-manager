from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QInputDialog
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ..widgets.grid_container import ClickableGridWidget, DraggableGridContainer
from ..utils.config_utils import get_spacing_between_grids, get_spacing_between_buttons, get_brush_icon_size

class GridManager:
    """Manages grid operations and layout"""
    
    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
    
    def add_grid_ui(self, grid_info):
        """Add UI elements for a grid"""
        grid_container = DraggableGridContainer(grid_info, self.parent_docker)
        container_layout = QVBoxLayout()
        container_layout.setSpacing(1)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header layout with grid name
        header_layout = QHBoxLayout()
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(grid_info['name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(name_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        
        container_layout.addLayout(header_layout)
        
        # Store references
        grid_info['container'] = grid_container
        grid_info['name_label'] = name_label
        
        # Setup label click handlers
        self.setup_label_handlers(name_label, grid_info)
        
        # Create grid widget
        grid_widget = ClickableGridWidget(grid_info, self.parent_docker)
        icon_size = get_brush_icon_size()
        grid_widget.setFixedHeight(icon_size + 4)
        grid_widget.setMinimumHeight(icon_size + 4)
        
        # Create grid layout
        from PyQt5.QtWidgets import QGridLayout
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        grid_layout.setSpacing(get_spacing_between_buttons())
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        grid_widget.setLayout(grid_layout)
        container_layout.addWidget(grid_widget)
        grid_container.setLayout(container_layout)
        
        # Store references
        grid_info['widget'] = grid_widget
        grid_info['layout'] = grid_layout
        
        # Add to main layout
        self.parent_docker.main_grid_layout.addWidget(grid_container)
        self.parent_docker.update_grid(grid_info)
    
    def setup_label_handlers(self, name_label, grid_info):
        """Setup mouse handlers for grid name label"""
        def name_label_mousePressEvent(event):
            mods = QApplication.keyboardModifiers()
            
            # Shift + Left click: Move up
            if event.button() == Qt.LeftButton and mods == Qt.ShiftModifier:
                self.parent_docker.move_grid(grid_info, -1)
            # Shift + Right click: Move down
            elif event.button() == Qt.RightButton and mods == Qt.ShiftModifier:
                self.parent_docker.move_grid(grid_info, 1)
            # Normal left click: Activate
            elif event.button() == Qt.LeftButton:
                self.parent_docker.set_active_grid(grid_info)
            # Alt + Right click: Rename
            elif event.button() == Qt.RightButton and mods == Qt.AltModifier:
                self.rename_grid(grid_info)
            # Ctrl+Alt+Shift+Right click: Delete
            elif (event.button() == Qt.RightButton and
                  (mods & (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)) == 
                  (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)):
                self.remove_grid(grid_info)
        
        name_label.mousePressEvent = name_label_mousePressEvent
    
    def rename_grid(self, grid_info):
        """Rename a grid"""
        new_name, ok = QInputDialog.getText(
            self.parent_docker,
            "Rename Grid",
            "Enter new grid name:",
            text=grid_info['name']
        )
        
        if ok and new_name.strip():
            grid_info['name'] = new_name.strip()
            grid_info['name_label'].setText(grid_info['name'])
            self.parent_docker.save_grids_data()
    
    def remove_grid(self, grid_info):
        """Remove a grid"""
        if grid_info in self.parent_docker.grids:
            # Remove from layout
            container = grid_info.get('container')
            if container:
                self.parent_docker.main_grid_layout.removeWidget(container)
                container.setParent(None)
                container.deleteLater()
            
            self.parent_docker.grids.remove(grid_info)
            
            # Reset active grid
            if self.parent_docker.grids:
                self.parent_docker.set_active_grid(self.parent_docker.grids[0])
            else:
                self.parent_docker.active_grid = None
            
            self.parent_docker.save_grids_data()