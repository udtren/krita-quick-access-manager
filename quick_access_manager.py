import os
import json
from krita import Extension, DockWidgetFactory, DockWidgetFactoryBase, Krita
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QDockWidget, QScrollArea, QHBoxLayout, QInputDialog, QApplication
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QDrag
from .data_manager import load_grids_data, save_grids_data
from .shortcut_manager import ShortcutAccessSection

class DraggableBrushButton(QPushButton):
    def __init__(self, preset, grid_info, parent_docker):
        super().__init__()
        self.preset = preset
        self.grid_info = grid_info
        self.parent_docker = parent_docker
        self.drag_start_position = QPoint()
        
        self.setToolTip(preset.name())
        self.setFixedSize(48, 48)
        
        # Set brush preset icon
        if preset.image():
            pixmap = QPixmap.fromImage(preset.image())
            icon = QIcon(pixmap)
            self.setIcon(icon)
            self.setIconSize(self.size())
        else:
            self.setText(preset.name()[:2])  # Fallback text
        
        self.clicked.connect(lambda: self.parent_docker.select_brush_preset(preset))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(f"brush_preset:{self.preset.name()}")
        drag.setMimeData(mimeData)
        
        # Set drag pixmap
        if self.preset.image():
            pixmap = QPixmap.fromImage(self.preset.image()).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.gray)
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(16, 16))
        
        dropAction = drag.exec_(Qt.MoveAction)

class ClickableGridWidget(QWidget):
    def __init__(self, grid_info, parent_docker):
        super().__init__()
        self.grid_info = grid_info
        self.parent_docker = parent_docker
        self.drag_start_position = QPoint()
        self.setAcceptDrops(True)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Only start grid drag if clicking on empty space (not on brush buttons)
        widget_under_mouse = self.childAt(event.pos())
        if widget_under_mouse and isinstance(widget_under_mouse, DraggableBrushButton):
            return
        
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(f"grid:{self.grid_info['name']}")
        drag.setMimeData(mimeData)
        
        dropAction = drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("brush_preset:"):
                event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("brush_preset:"):
                preset_name = text.split(":", 1)[1]
                
                # Find the source preset and grid
                source_preset = None
                source_grid = None
                source_index = -1
                
                for grid in self.parent_docker.grids:
                    for i, preset in enumerate(grid['brush_presets']):
                        if preset.name() == preset_name:
                            source_preset = preset
                            source_grid = grid
                            source_index = i
                            break
                    if source_preset:
                        break
                
                if source_preset and source_grid:
                    # Calculate drop position in grid
                    drop_pos = event.pos()
                    columns = self.parent_docker.get_dynamic_columns()
                    button_size = 48
                    spacing = 2
                    
                    col = min(drop_pos.x() // (button_size + spacing), columns - 1)
                    row = drop_pos.y() // (button_size + spacing)
                    target_index = row * columns + col
                    
                    # If dropping on the same grid, reorder
                    if source_grid == self.grid_info:
                        # Remove from old position
                        source_grid['brush_presets'].pop(source_index)
                        # Insert at new position
                        target_index = min(target_index, len(source_grid['brush_presets']))
                        if source_index < target_index:
                            target_index -= 1
                        source_grid['brush_presets'].insert(target_index, source_preset)
                    else:
                        # Move between grids
                        source_grid['brush_presets'].pop(source_index)
                        target_index = min(target_index, len(self.grid_info['brush_presets']))
                        self.grid_info['brush_presets'].insert(target_index, source_preset)
                        self.parent_docker.update_grid(source_grid)
                    
                    self.parent_docker.update_grid(self.grid_info)
                    self.parent_docker.save_grids_data()
                    event.acceptProposedAction()

class DraggableGridContainer(QWidget):
    def __init__(self, grid_info, parent_docker):
        super().__init__()
        self.grid_info = grid_info
        self.parent_docker = parent_docker

class QuickAccessDockerWidget(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Access Manager")
        self.grids = []  # Store multiple grids
        self.active_grid = None  # Currently active grid
        self.scroll_widget = None
        self.main_grid_layout = None
        self.grid_counter = 0
        self.data_file = os.path.join(os.path.dirname(__file__), "grids_data.json")
        self.preset_dict = Krita.instance().resources('preset')
        self.grids, self.grid_counter = load_grids_data(self.data_file, self.preset_dict)
        self.init_ui()

    def save_grids_data(self):
        save_grids_data(self.data_file, self.grids)

    def load_grids_data(self):
        self.grids, self.grid_counter = load_grids_data(self.data_file, self.preset_dict)

    def init_ui(self):
        # Create a central widget for the dock
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Section 1: Quick Brush Access
        title_label = QLabel("Quick Brush Access")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # First button row (horizontal)
        button_layout_1 = QHBoxLayout()
        
        # Add Brush button
        add_brush_button = QPushButton("AddBrush")
        add_brush_button.clicked.connect(self.add_current_brush)
        button_layout_1.addWidget(add_brush_button)
        
        # Add Grid button
        add_grid_button = QPushButton("AddGrid")
        add_grid_button.clicked.connect(self.add_new_grid)
        button_layout_1.addWidget(add_grid_button)
        
        main_layout.addLayout(button_layout_1)
        
        # Second button row (horizontal)
        button_layout_2 = QHBoxLayout()
        
        # Remove Brush button
        remove_brush_button = QPushButton("RemoveBrush")
        remove_brush_button.clicked.connect(self.remove_current_brush)
        button_layout_2.addWidget(remove_brush_button)
        
        main_layout.addLayout(button_layout_2)
        
        # Scroll area for brush presets grids
        scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.main_grid_layout = QVBoxLayout()
        self.main_grid_layout.setSpacing(2)  # Minimize spacing between grids
        self.main_grid_layout.setContentsMargins(2, 2, 2, 2)  # Minimize margins
        self.scroll_widget.setLayout(self.main_grid_layout)
        scroll_area.setWidget(self.scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        main_layout.addWidget(scroll_area)
        
        # Section 2: Quick Shortcut Access
        shortcut_section = ShortcutAccessSection(self)
        main_layout.addWidget(shortcut_section)
        
        central_widget.setLayout(main_layout)
        self.setWidget(central_widget)
        
        # Add initial grid(s) from loaded data
        if not self.grids:
            self.add_new_grid()
        else:
            for grid_info in self.grids:
                self._add_grid_ui(grid_info)
            # Set first grid active
            if self.grids:
                self.set_active_grid(self.grids[0])

    def _add_grid_ui(self, grid_info):
        grid_container = DraggableGridContainer(grid_info, self)
        container_layout = QVBoxLayout()
        container_layout.setSpacing(2)
        container_layout.setContentsMargins(2, 2, 2, 2)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(2)
        header_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(grid_info['name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(name_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()

        # ↑↓Rename Activeボタン追加
        up_btn = QPushButton("↑")
        up_btn.setFixedSize(24, 20)
        up_btn.setStyleSheet("font-size: 10px;")
        down_btn = QPushButton("↓")
        down_btn.setFixedSize(24, 20)
        down_btn.setStyleSheet("font-size: 10px;")
        rename_button = QPushButton("Rename")
        rename_button.setFixedSize(50, 20)
        rename_button.setStyleSheet("font-size: 10px;")
        active_btn = QPushButton("Active")
        active_btn.setFixedSize(50, 20)
        active_btn.setStyleSheet("font-size: 10px;")
        header_layout.addWidget(up_btn)
        header_layout.addWidget(down_btn)
        header_layout.addWidget(rename_button)
        header_layout.addWidget(active_btn)
        container_layout.addLayout(header_layout)
        grid_info['container'] = grid_container
        grid_info['name_label'] = name_label
        grid_info['rename_button'] = rename_button
        grid_info['active_btn'] = active_btn

        up_btn.clicked.connect(lambda: self.move_grid(grid_info, -1))
        down_btn.clicked.connect(lambda: self.move_grid(grid_info, 1))
        rename_button.clicked.connect(lambda: self.rename_grid(grid_info))
        active_btn.clicked.connect(lambda: self.set_active_grid(grid_info))

        grid_widget = ClickableGridWidget(grid_info, self)
        grid_widget.setFixedHeight(48 + 4)
        grid_widget.setMinimumHeight(48 + 4)
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_widget.setLayout(grid_layout)
        container_layout.addWidget(grid_widget)
        grid_container.setLayout(container_layout)
        grid_info['widget'] = grid_widget
        grid_info['layout'] = grid_layout
        self.main_grid_layout.addWidget(grid_container)
        self.update_grid(grid_info)

    def move_grid(self, grid_info, direction):
        idx = self.grids.index(grid_info)
        new_idx = idx + direction
        if 0 <= new_idx < len(self.grids):
            self.grids.pop(idx)
            self.grids.insert(new_idx, grid_info)
            self.rebuild_grid_layout()
            self.save_grids_data()

    def add_new_grid(self):
        self.grid_counter += 1
        grid_name = f"Grid {self.grid_counter}"
        grid_info = {
            'container': None,
            'widget': None,
            'layout': None,
            'name_label': None,
            'rename_button': None,
            'active_btn': None,
            'name': grid_name,
            'brush_presets': [],
            'is_active': False
        }
        self.grids.append(grid_info)
        self._add_grid_ui(grid_info)
        if len(self.grids) == 1:
            self.set_active_grid(grid_info)
        self.save_grids_data()

    def rename_grid(self, grid_info):
        # Show input dialog for new grid name
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Grid",
            "Enter new grid name:",
            text=grid_info['name']
        )
        
        if ok and new_name.strip():
            grid_info['name'] = new_name.strip()
            grid_info['name_label'].setText(grid_info['name'])
            self.save_grids_data()

    def get_dynamic_columns(self):
        # Calculate columns based on docker width
        docker_width = self.width()
        button_size = 48
        margin = 20
        min_columns = 2
        
        available_width = docker_width - margin
        columns = max(min_columns, available_width // button_size)
        return int(columns)
    
    def add_current_brush(self):
        # Get current brush preset
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            current_preset = app.activeWindow().activeView().currentBrushPreset()
            if current_preset and self.active_grid:
                # Add to the active grid instead of the last grid
                active_grid = self.active_grid
                
                # Check if preset already exists in any grid
                all_presets = []
                for grid in self.grids:
                    all_presets.extend([p.name() for p in grid['brush_presets']])
                
                if current_preset.name() not in all_presets:
                    active_grid['brush_presets'].append(current_preset)
                    self.update_grid(active_grid)
                    self.save_grids_data()
    
    def remove_current_brush(self):
        # Get current brush preset
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView() and self.active_grid:
            current_preset = app.activeWindow().activeView().currentBrushPreset()
            if current_preset:
                # Find and remove the preset from active grid
                active_grid = self.active_grid
                preset_name = current_preset.name()
                
                # Remove preset if it exists in the active grid
                for i, preset in enumerate(active_grid['brush_presets']):
                    if preset.name() == preset_name:
                        active_grid['brush_presets'].pop(i)
                        self.update_grid(active_grid)
                        self.save_grids_data()
                        break
    
    def update_grid(self, grid_info):
        # Clear existing buttons in this grid
        layout = grid_info['layout']
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        
        # Get dynamic column count
        columns = self.get_dynamic_columns()
        
        # Calculate required rows
        preset_count = len(grid_info['brush_presets'])
        required_rows = (preset_count + columns - 1) // columns if preset_count > 0 else 1
        
        # Update grid widget height based on number of rows
        new_height = required_rows * 48 + (required_rows - 1) * 2 + 4  # rows * icon_height + spacing + margins
        grid_info['widget'].setFixedHeight(new_height)
        
        # Add brush preset buttons to grid (using draggable buttons)
        for index, preset in enumerate(grid_info['brush_presets']):
            row = index // columns
            col = index % columns
            
            # Create draggable button for brush preset
            brush_button = DraggableBrushButton(preset, grid_info, self)
            layout.addWidget(brush_button, row, col)
        self.save_grids_data()
    
    def set_active_grid(self, grid_info):
        # Deactivate all grids
        for grid in self.grids:
            grid['is_active'] = False
            self.update_grid_style(grid)
        # Activate selected grid
        grid_info['is_active'] = True
        self.active_grid = grid_info
        self.update_grid_style(grid_info)
    
    def update_grid_style(self, grid_info):
        # Update visual style based on active status
        if grid_info['is_active']:
            grid_info['widget'].setStyleSheet("""
                QWidget {
                    border: 2px solid #0078d4;
                    background-color: #f0f8ff;
                }
            """)
            grid_info['name_label'].setStyleSheet("""
                font-weight: bold; 
                font-size: 12px; 
                color: #4FC3F7;
            """)
        else:
            grid_info['widget'].setStyleSheet("""
                QWidget {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                }
            """)
            grid_info['name_label'].setStyleSheet("""
                font-weight: bold; 
                font-size: 12px; 
                color: #ffffff;
            """)
    
    def resizeEvent(self, event):
        # 対策: グリッドのボタン再生成は行わない
        super().resizeEvent(event)
        # 必要ならレイアウト調整のみ（例: グリッドの高さや列数の調整）
        # for grid_info in self.grids:
        #     self.adjust_grid_layout(grid_info)

    # def adjust_grid_layout(self, grid_info):
    #     # ここでボタン再生成せず、レイアウトや高さのみ調整する
    #     columns = self.get_dynamic_columns()
    #     preset_count = len(grid_info['brush_presets'])
    #     required_rows = (preset_count + columns - 1) // columns if preset_count > 0 else 1
    #     new_height = required_rows * 48 + (required_rows - 1) * 2 + 4
    #     grid_info['widget'].setFixedHeight(new_height)
    
    def select_brush_preset(self, preset):
        # Set the selected brush preset as current
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            app.activeWindow().activeView().setCurrentBrushPreset(preset)
    
    def rebuild_grid_layout(self):
        # Clear main layout
        for i in reversed(range(self.main_grid_layout.count())):
            item = self.main_grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.main_grid_layout.removeWidget(widget)
        
        # Re-add grids in new order
        for grid_info in self.grids:
            self.main_grid_layout.addWidget(grid_info['container'])
        
        # Update styles
        for grid_info in self.grids:
            self.update_grid_style(grid_info)
        self.save_grids_data()

class QuickAccessDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        super().__init__("quick_access_manager_docker", DockWidgetFactory.DockRight)
    
    def createDockWidget(self):
        return QuickAccessDockerWidget()

class QuickAccessManagerExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.docker_factory = None
    
    def setup(self):
        # Register the docker factory during setup
        self.docker_factory = QuickAccessDockerFactory()
        Krita.instance().addDockWidgetFactory(self.docker_factory)
    
    def createActions(self, window):
        pass
