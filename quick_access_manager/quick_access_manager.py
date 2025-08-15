import os
import json
from krita import Extension, DockWidgetFactory, DockWidgetFactoryBase, Krita
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QDockWidget, QScrollArea, QHBoxLayout, QInputDialog, QApplication, QDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, QMimeData, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QDrag
from .data_manager import load_grids_data, save_grids_data
from .shortcut_manager import ShortcutAccessSection, SingleShortcutGridWidget, shortcut_btn_style
from .preprocess import check_common_config
from .brush_adjustment import BrushAdjustmentWidget

COMMON_CONFIG = check_common_config()
spacingBetweenGridsValue = COMMON_CONFIG["layout"]["spacing_between_grids"]
spacingBetweenButtonsValue = COMMON_CONFIG["layout"]["spacing_between_buttons"]
iconSize = COMMON_CONFIG["layout"]["brush_icon_size"]

def docker_btn_style():
    color = COMMON_CONFIG["color"]["docker_button_background_color"]
    font_color = COMMON_CONFIG["color"]["docker_button_font_color"]
    font_size = COMMON_CONFIG["font"]["docker_button_font_size"]
    return f"background-color: {color}; color: {font_color}; font-size: {font_size};"

def get_font_px(font_size_str):
    try:
        return int(str(font_size_str).replace("px", ""))
    except Exception:
        return 12

def get_spacing_between_buttons():
    return COMMON_CONFIG["layout"]["spacing_between_buttons"]

def get_spacing_between_grids():
    return COMMON_CONFIG["layout"]["spacing_between_grids"]

def get_brush_icon_size():
    return COMMON_CONFIG["layout"]["brush_icon_size"]

class CommonConfigDialog(QDialog):
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config_path = config_path
        self.resize(400, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Editable fields for color/font/layout
        self.fields = {}
        for section in ["color", "font", "layout"]:
            group = self.config.get(section, {})
            layout.addWidget(QLabel(f"[{section}]"))
            for key, value in group.items():
                hlayout = QHBoxLayout()
                label = QLabel(key)
                edit = QLineEdit(str(value))
                hlayout.addWidget(label)
                hlayout.addWidget(edit)
                layout.addLayout(hlayout)
                self.fields[(section, key)] = edit

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    def save_and_close(self):
        # Save edits to config
        for (section, key), edit in self.fields.items():
            val = edit.text()
            # 型変換
            if section == "layout":
                try:
                    val = int(val)
                except Exception:
                    pass
            self.config[section][key] = val
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
        self.accept()

class DraggableBrushButton(QPushButton):
    def __init__(self, preset, grid_info, parent_docker):
        super().__init__()
        self.preset = preset
        self.grid_info = grid_info
        self.parent_docker = parent_docker
        self.drag_start_position = QPoint()
        
        self.setToolTip(preset.name())
        self.setFixedSize(iconSize, iconSize)
        
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
        if event.button() == Qt.LeftButton and QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.drag_start_position = event.pos()
        # Ctrl+右クリックで削除
        if event.button() == Qt.RightButton and QApplication.keyboardModifiers() == Qt.ControlModifier:
            # グリッドからこのプリセットを削除
            for i, p in enumerate(self.grid_info['brush_presets']):
                if p.name() == self.preset.name():
                    self.grid_info['brush_presets'].pop(i)
                    self.parent_docker.update_grid(self.grid_info)
                    self.parent_docker.save_grids_data()
                    break
            return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if QApplication.keyboardModifiers() != Qt.ControlModifier:
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
        
        drag.setPixmap(self.icon().pixmap(32, 32))
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
                    button_size = iconSize
                    spacing = 2
                    
                    col = min(drop_pos.x() // (button_size + spacing), columns - 1)
                    row = drop_pos.y() // (button_size + spacing)
                    target_index = row * columns + col
                    
                    # Remove from old position
                    source_grid['brush_presets'].pop(source_index)
                    
                    # If dropping on the same grid, reorder
                    if source_grid == self.grid_info:
                        # Remove from old position
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
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        self.data_file = os.path.join(config_dir, "grids_data.json")
        self.common_config_path = os.path.join(config_dir, "common.json")
        self.preset_dict = Krita.instance().resources('preset')
        self.grids, self.grid_counter = load_grids_data(self.data_file, self.preset_dict)
        self.grids, self.grid_counter = load_grids_data(self.data_file, self.preset_dict)
        self.init_ui()

    def save_grids_data(self):
        save_grids_data(self.data_file, self.grids)

    def load_grids_data(self):
        self.grids, self.grid_counter = load_grids_data(self.data_file, self.preset_dict)
        self.grids, self.grid_counter = load_grids_data(self.data_file, self.preset_dict)

    def init_ui(self):
        # Create a central widget for the dock
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        #####################################
        ####   Brush Adjustments Section
        #####################################
        self.brush_adjustment_section = BrushAdjustmentWidget(self)
        main_layout.addWidget(self.brush_adjustment_section)

        #####################################
        ####   BrushSets Section
        #####################################
        # First button row (horizontal)
        button_layout_1 = QHBoxLayout()
        
        # Add Brush button
        add_brush_button = QPushButton("AddBrush")
        add_brush_button.setStyleSheet(docker_btn_style())
        add_brush_button.clicked.connect(self.add_current_brush)
        button_layout_1.addWidget(add_brush_button)
        
        # Add Grid button
        add_grid_button = QPushButton("AddGrid")
        add_grid_button.setStyleSheet(docker_btn_style())
        add_grid_button.clicked.connect(self.add_new_grid)
        button_layout_1.addWidget(add_grid_button)
        
        main_layout.addLayout(button_layout_1)
        
        # Scroll area for brush presets grids
        scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.main_grid_layout = QVBoxLayout()
        self.main_grid_layout.setSpacing(spacingBetweenGridsValue)  # Minimize spacing between grids
        self.main_grid_layout.setContentsMargins(0, 0, 0, 0)  # Minimize margins
        self.scroll_widget.setLayout(self.main_grid_layout)
        scroll_area.setWidget(self.scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        main_layout.addWidget(scroll_area)
        
        #####################################
        ####   Quick Shortcut Access Section
        #####################################
        self.shortcut_section = ShortcutAccessSection(self)
        main_layout.addWidget(self.shortcut_section)

        #####################################
        ####   Other
        #####################################
        # Settingボタンを一番下に追加
        setting_btn = QPushButton("Setting")
        setting_btn.setStyleSheet(docker_btn_style())
        main_layout.addWidget(setting_btn)
        setting_btn.clicked.connect(self.show_settings_dialog)

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

    def show_settings_dialog(self):
        dlg = CommonConfigDialog(self.common_config_path, self)
        if dlg.exec_():
            # 設定を再読み込みして即時反映
            global COMMON_CONFIG
            with open(self.common_config_path, "r", encoding="utf-8") as f:
                COMMON_CONFIG = json.load(f)
            # ここで再取得
            global iconSize
            iconSize = get_brush_icon_size()
            global spacingBetweenGridsValue
            spacingBetweenGridsValue = get_spacing_between_grids()
            global spacingBetweenButtonsValue
            spacingBetweenButtonsValue = get_spacing_between_buttons()

            self.refresh_styles()
            # ボタンサイズやレイアウトも再構築
            for grid_info in self.grids:
                # spacingBetweenGridsValueを再適用
                if grid_info.get('container'):
                    container_layout = grid_info['container'].layout()
                    if container_layout:
                        container_layout.setSpacing(1)
                if grid_info.get('layout'):
                    grid_info['layout'].setSpacing(spacingBetweenButtonsValue)
                self.update_grid(grid_info)
            # ショートカットグリッドも再構築
            if hasattr(self, "shortcut_section"):
                self.shortcut_section.refresh_layout()

    def refresh_styles(self):
        # ボタンやグリッドのスタイルを再適用
        # ブラシグリッド
        for grid in self.grids:
            # グリッド名ラベル
            if grid.get('name_label'):
                grid['name_label'].setStyleSheet("font-weight: bold; font-size: 12px; color: #4FC3F7;" if grid.get('is_active') else "font-weight: bold; font-size: 12px; color: #ffffff;")

            # ブラシボタン
            if grid.get('widget'):
                layout = grid['layout']
                for i in range(layout.count()):
                    btn = layout.itemAt(i).widget()
                    if btn:
                        btn.setStyleSheet(docker_btn_style())
        # ショートカットグリッド
        shortcut_section = self.findChild(ShortcutAccessSection)
        if shortcut_section:
            for grid_widget in shortcut_section.grids:
                # グリッド名ラベル
                if hasattr(grid_widget, "grid_name_label"):
                    grid_widget.grid_name_label.setStyleSheet(
                        "font-weight: bold; font-size: 13px; color: #4FC3F7; background: none;" if grid_widget.is_active else
                        "font-weight: bold; font-size: 13px; color: #ffffff; background: none;"
                    )
                # ショートカットボタン
                layout = getattr(grid_widget, "shortcut_grid_layout", None)
                if layout:
                    for i in range(layout.count()):
                        btn = layout.itemAt(i).widget()
                        if btn:
                            btn.setStyleSheet(shortcut_btn_style())
        # AddBrush/AddGrid/Settingボタンなども再適用
        for btn in self.findChildren(QPushButton):
            if btn.text() in ["AddBrush", "AddGrid", "Setting", "Actions", "RestoreActions"]:
                btn.setStyleSheet(docker_btn_style())
        # Brush adjustment section
        if hasattr(self, "brush_adjustment_section"):
            self.brush_adjustment_section.refresh_styles()

    def _add_grid_ui(self, grid_info):
        grid_container = DraggableGridContainer(grid_info, self)
        container_layout = QVBoxLayout()
        container_layout.setSpacing(1)
        container_layout.setContentsMargins(0, 0, 0, 0)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(grid_info['name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(name_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()

        container_layout.addLayout(header_layout)
        grid_info['container'] = grid_container
        grid_info['name_label'] = name_label

        def name_label_mousePressEvent(event):
            mods = QApplication.keyboardModifiers()
            # Shift + 左クリックで↑
            if event.button() == Qt.LeftButton and mods == Qt.ShiftModifier:
                self.move_grid(grid_info, -1)
            # Shift + 右クリックで↓
            elif event.button() == Qt.RightButton and mods == Qt.ShiftModifier:
                self.move_grid(grid_info, 1)
            # 通常左クリックでActive
            elif event.button() == Qt.LeftButton:
                self.set_active_grid(grid_info)
            # Alt + 右クリックでRename
            elif event.button() == Qt.RightButton and mods == Qt.AltModifier:
                self.rename_grid(grid_info)
            # Ctrl+Alt+Shift+右クリックでGrid削除
            elif (
                event.button() == Qt.RightButton and
                (mods & (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)) == (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)
            ):
                self.remove_grid(grid_info)
            
            
        name_label.mousePressEvent = name_label_mousePressEvent

        grid_widget = ClickableGridWidget(grid_info, self)
        grid_widget.setFixedHeight(iconSize + 4)
        grid_widget.setMinimumHeight(iconSize + 4)
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        grid_layout.setSpacing(spacingBetweenButtonsValue)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_widget.setLayout(grid_layout)
        container_layout.addWidget(grid_widget)
        grid_container.setLayout(container_layout)
        grid_info['widget'] = grid_widget
        grid_info['layout'] = grid_layout
        self.main_grid_layout.addWidget(grid_container)
        self.update_grid(grid_info)

    def remove_grid(self, grid_info):
        # グリッドを削除
        if grid_info in self.grids:
            idx = self.grids.index(grid_info)
            # レイアウトから削除
            container = grid_info.get('container')
            if container:
                self.main_grid_layout.removeWidget(container)
                container.setParent(None)
                container.deleteLater()
            self.grids.remove(grid_info)
            # アクティブグリッドの再設定
            if self.grids:
                self.set_active_grid(self.grids[0])
            else:
                self.active_grid = None
            self.save_grids_data()

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
        # max_brush_per_rowを優先して返す
        max_brush = COMMON_CONFIG.get("layout", {}).get("max_brush_per_row", 8)
        return int(max_brush)
    
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
    
    def update_grid(self, grid_info):
        # Clear existing buttons in this grid
        layout = grid_info['layout']
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        # max_brush_per_rowを使う
        columns = self.get_dynamic_columns()
        preset_count = len(grid_info['brush_presets'])
        required_rows = (preset_count + columns - 1) // columns if preset_count > 0 else 1
        new_height = required_rows * iconSize + (required_rows - 1) * 2 + 4
        grid_info['widget'].setFixedHeight(new_height)
        for index, preset in enumerate(grid_info['brush_presets']):
            row = index // columns
            col = index % columns
            brush_button = DraggableBrushButton(preset, grid_info, self)
            layout.addWidget(brush_button, row, col)
    
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
        super().resizeEvent(event)
    
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
        self.docker_factory = QuickAccessDockerFactory()
        Krita.instance().addDockWidgetFactory(self.docker_factory)

    def createActions(self, window):
        # Kritaのウィンドウが初期化された後に呼ばれる
        for d in window.dockers():
            try:
                widget = None
                if hasattr(d, "widget"):
                    w = d.widget
                    widget = w() if callable(w) else w
                if widget and hasattr(widget, "shortcut_section"):
                    widget.shortcut_section.restore_grids_from_file()
            except Exception:
                QMessageBox.warning(
                    None,
                    "QuickAccessManagerExtension Error",
                    "Something wrong is happening on QuickAccessManagerExtension.createActions.\n\nYou can try disable other plugin and start Krita again."
                )
