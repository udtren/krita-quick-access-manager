import json
import os
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QMessageBox, QGridLayout, QInputDialog, QApplication
from PyQt5.QtCore import Qt, QSize, QMimeData, QPoint
from PyQt5.QtGui import QDrag
from krita import Krita
from .data_manager import load_shortcut_grids_data, save_shortcut_grids_data

def load_common_config():
    config_path = os.path.join(os.path.dirname(__file__), "config", "common.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
COMMON_CONFIG = load_common_config()

def shortcut_btn_style():
    color = COMMON_CONFIG["color"]["shortcut_button_background_color"]
    font_color = COMMON_CONFIG["color"]["shortcut_button_font_color"]
    font_size = COMMON_CONFIG["font"]["shortcut_button_font_size"]
    return f"background-color: {color}; color: {font_color}; font-size: {font_size};"

def docker_btn_style():
    color = COMMON_CONFIG["color"]["docker_button_background_color"]
    font_color = COMMON_CONFIG["color"]["docker_button_font_color"]
    font_size = COMMON_CONFIG["font"]["docker_button_font_size"]
    return f"background-color: {color}; color: {font_color}; font-size: {font_size};"

def get_font_px(font_size_str):
    # "20px" -> 20
    try:
        return int(str(font_size_str).replace("px", ""))
    except Exception:
        return 12

def log_shortcut_restore(msg):
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, "shortcut_grid.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

class ShortcutPopup(QDialog):
    def __init__(self, parent_section):
        super().__init__(parent_section)
        self.parent_section = parent_section
        self.setWindowTitle("All Krita Shortcuts")
        self.resize(600, 400)
        layout = QVBoxLayout()

        self.add_shortcut_btn = QPushButton("AddShortCut")
        self.add_shortcut_btn.setStyleSheet(docker_btn_style())
        layout.addWidget(self.add_shortcut_btn)
        self.add_shortcut_btn.clicked.connect(self.add_selected_shortcut_to_grid)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by internal ID...")
        layout.addWidget(self.filter_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action ID", "Shortcut Keys"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.actions = []
        self.populate_table()
        self.filter_edit.textChanged.connect(self.apply_filter)

    def populate_table(self):
        self.actions = Krita.instance().actions()
        self.table.setRowCount(len(self.actions))
        for i, action in enumerate(self.actions):
            id_item = QTableWidgetItem(action.objectName())
            shortcut_item = QTableWidgetItem(", ".join([str(s.toString()) for s in action.shortcuts()]))
            self.table.setItem(i, 0, id_item)
            self.table.setItem(i, 1, shortcut_item)

    def apply_filter(self, text):
        for i in range(self.table.rowCount()):
            id_item = self.table.item(i, 0)
            self.table.setRowHidden(i, text.lower() not in id_item.text().lower())

    def get_selected_action(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            return self.actions[row]
        return None

    def add_selected_shortcut_to_grid(self):
        action = self.get_selected_action()
        if not action:
            QMessageBox.warning(self, "No Shortcut", "Please select a shortcut in the table.")
            return
        self.parent_section.add_shortcut_to_grid(action)

class ShortcutAccessSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent
        self.grids = []
        self.active_grid_idx = 0

        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        self.data_file = os.path.join(self.config_dir, "shortcut_grid_data.json")

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        button_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("ShowAllShortcut")
        self.show_all_btn.setStyleSheet(docker_btn_style())
        self.add_grid_btn = QPushButton("AddGrid")
        self.add_grid_btn.setStyleSheet(docker_btn_style())
        button_layout.addWidget(self.show_all_btn)
        button_layout.addWidget(self.add_grid_btn)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

        self.show_all_btn.clicked.connect(self.show_all_shortcut_popup)
        self.add_grid_btn.clicked.connect(self.add_grid)

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, "_restored"):
            self.restore_grids_from_file()
            self._restored = True

    def restore_grids_from_file(self):
        krita_instance = Krita.instance()
        # 追加: 利用可能な全アクションIDをログ出力
        all_action_ids = [a.objectName() for a in krita_instance.actions()]
        log_shortcut_restore(f"Krita available action IDs: {all_action_ids}")

        grids_data = load_shortcut_grids_data(self.data_file, krita_instance)
        log_shortcut_restore(f"restore_grids_from_file: loaded {len(grids_data) if grids_data else 0} grids from {self.data_file}")
        if grids_data:
            for grid_info in grids_data:
                if 'shortcuts' in grid_info:
                    actions_or_ids = grid_info['shortcuts']
                    log_shortcut_restore(f"Restoring grid: {grid_info['name']}, shortcuts: {actions_or_ids}")
                else:
                    actions_or_ids = grid_info.get('actions', [])
                    log_shortcut_restore(f"Restoring grid: {grid_info['name']}, actions: {[a.objectName() if hasattr(a, 'objectName') else str(a) for a in actions_or_ids]}")
                self.add_shortcut_grid(grid_info['name'], actions_or_ids, save=False)
        else:
            log_shortcut_restore("No grids found, adding default grid.")
            self.add_shortcut_grid("Shortcut Grid 1", save=False)

    def add_grid(self):
        grid_name = f"Shortcut Grid {len(self.grids) + 1}"
        self.add_shortcut_grid(grid_name, save=True)

    def add_shortcut_grid(self, grid_name, actions=None, save=True):
        # actionsがstrリスト（action_id）の場合はQActionリストに変換
        krita_instance = Krita.instance()
        if actions is None:
            actions = []
        elif all(isinstance(a, str) for a in actions):
            log_shortcut_restore(f"Converting action ids to QAction: {actions}")
            actions = [krita_instance.action(aid) for aid in actions if krita_instance.action(aid)]
        else:
            log_shortcut_restore(f"Using existing QAction list: {[a.objectName() for a in actions if hasattr(a, 'objectName')]}")
        # それ以外（QActionリスト）はそのまま
        grid_info = {
            'name': grid_name,
            'actions': actions,
        }
        log_shortcut_restore(f"Creating grid widget: {grid_name}, actions: {[a.objectName() for a in actions if hasattr(a, 'objectName')]}")
        grid_widget = SingleShortcutGridWidget(grid_info, self)
        self.grids.append(grid_widget)
        self.main_layout.addWidget(grid_widget)
        self.set_active_grid(len(self.grids) - 1)
        if save:
            self.save_grids_data()

    def set_active_grid(self, idx):
        for i, grid_widget in enumerate(self.grids):
            grid_widget.set_active(i == idx)
        self.active_grid_idx = idx

    def show_all_shortcut_popup(self):
        self.shortcut_popup = ShortcutPopup(self)
        self.shortcut_popup.exec_()

    def add_shortcut_to_grid(self, action):
        if self.grids:
            self.grids[self.active_grid_idx].add_shortcut_button(action)
            self.save_grids_data()

    def run_krita_action(self, action_id):
        action = Krita.instance().action(action_id)
        if action:
            action.trigger()
        else:
            QMessageBox.warning(self, "Action Error", f"Action '{action_id}' not found.")

    def save_grids_data(self):
        grids_data = []
        for grid_widget in self.grids:
            grids_data.append({
                'name': grid_widget.grid_info['name'],
                'actions': grid_widget.grid_info['actions'],
            })
        save_shortcut_grids_data(self.data_file, grids_data)

class SingleShortcutGridWidget(QWidget):
    def __init__(self, grid_info, parent_section):
        super().__init__()
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.is_active = False

        self.setAcceptDrops(True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(2, 2, 2, 2)

        header_layout = QHBoxLayout()
        self.grid_name_label = QLabel(self.grid_info['name'])
        self.grid_name_label.setStyleSheet("font-weight: bold; font-size: 13px; background: none;")
        header_layout.addWidget(self.grid_name_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()

        font_px = get_font_px(COMMON_CONFIG["font"]["docker_button_font_size"])
        btn_height = int(font_px * 2)
        btn_width = int(font_px * 2.5)

        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(btn_width, btn_height)
        self.up_btn.setStyleSheet(docker_btn_style())
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(btn_width, btn_height)
        self.down_btn.setStyleSheet(docker_btn_style())
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setFixedSize(btn_width * 2, btn_height)
        self.rename_btn.setStyleSheet(docker_btn_style())
        self.active_btn = QPushButton("Active")
        self.active_btn.setFixedSize(btn_width * 2, btn_height)
        self.active_btn.setStyleSheet(docker_btn_style())
        header_layout.addWidget(self.up_btn)
        header_layout.addWidget(self.down_btn)
        header_layout.addWidget(self.rename_btn)
        header_layout.addWidget(self.active_btn)
        main_layout.addLayout(header_layout)

        self.shortcut_grid_layout = QGridLayout()
        self.shortcut_grid_layout.setSpacing(4)
        self.shortcut_grid_layout.setContentsMargins(2, 2, 2, 2)
        grid_area = QWidget()
        grid_area.setLayout(self.shortcut_grid_layout)
        grid_area.setStyleSheet("background: none;")
        main_layout.addWidget(grid_area)

        self.setLayout(main_layout)

        self.rename_btn.clicked.connect(self.rename_grid)
        self.active_btn.clicked.connect(self.activate_grid)

    def add_shortcut_button(self, action):
        self.grid_info['actions'].append(action)
        self.update_grid()
        if hasattr(self.parent_section, "save_grids_data"):
            self.parent_section.save_grids_data()

    def update_grid(self):
        log_shortcut_restore(f"update_grid: grid={self.grid_info['name']}, actions={[a.objectName() if hasattr(a, 'objectName') else str(a) for a in self.grid_info['actions']]}")
        while self.shortcut_grid_layout.count():
            item = self.shortcut_grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        max_columns = COMMON_CONFIG.get("layout", {}).get("max_shortcut_per_row", 3)
        for idx, action in enumerate(self.grid_info['actions']):
            action_id = action.objectName()
            log_shortcut_restore(f"update_grid: grid={self.grid_info['name']}, adding button for action_id={action_id}")
            shortcut_btn = ShortcutDraggableButton(action, self.grid_info, self.parent_section)
            shortcut_btn.setMinimumSize(QSize(80, 32))
            shortcut_btn.setStyleSheet(shortcut_btn_style())
            row = idx // max_columns
            col = idx % max_columns
            self.shortcut_grid_layout.addWidget(shortcut_btn, row, col)
        log_shortcut_restore(f"update_grid: grid={self.grid_info['name']}, total_buttons={len(self.grid_info['actions'])}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("shortcut_action:"):
                event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("shortcut_action:"):
                action_id = text.split(":", 1)[1]
                source_action = None
                source_grid = None
                source_index = -1
                for grid_widget in self.parent_section.grids:
                    for i, act in enumerate(grid_widget.grid_info['actions']):
                        if act.objectName() == action_id:
                            source_action = act
                            source_grid = grid_widget.grid_info
                            source_index = i
                            break
                    if source_action:
                        break
                if source_action and source_grid:
                    drop_pos = event.pos()
                    max_columns = COMMON_CONFIG.get("layout", {}).get("max_shortcut_per_row", 3)
                    col = min(drop_pos.x() // 90, max_columns - 1)
                    row = drop_pos.y() // 36
                    target_index = row * max_columns + col
                    source_grid['actions'].pop(source_index)
                    if self.grid_info == source_grid:
                        target_index = min(target_index, len(source_grid['actions']))
                        source_grid['actions'].insert(target_index, source_action)
                        self.update_grid()
                    else:
                        target_index = min(target_index, len(self.grid_info['actions']))
                        self.grid_info['actions'].insert(target_index, source_action)
                        grid_widget = self.parent_section.grids[self.parent_section.grids.index(self)]
                        grid_widget.update_grid()
                        for gw in self.parent_section.grids:
                            if gw.grid_info == source_grid:
                                gw.update_grid()
                                break
                    event.acceptProposedAction()

    def set_active(self, active):
        self.is_active = active
        self.update_grid_style()

    def activate_grid(self):
        idx = self.parent_section.grids.index(self)
        self.parent_section.set_active_grid(idx)

    def update_grid_style(self):
        if self.is_active:
            self.setStyleSheet("""
                QWidget {
                    border: none;
                    background: none;
                }
            """)
            self.grid_name_label.setStyleSheet("""
                font-weight: bold;
                font-size: 13px;
                color: #4FC3F7;
                background: none;
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    border: none;
                    background: none;
                }
            """)
            self.grid_name_label.setStyleSheet("""
                font-weight: bold;
                font-size: 13px;
                color: #ffffff;
                background: none;
            """)

    def rename_grid(self):
        new_name, ok = QInputDialog.getText(self, "Rename Shortcut Grid", "Enter new grid name:", text=self.grid_info['name'])
        if ok and new_name.strip():
            self.grid_info['name'] = new_name.strip()
            self.grid_name_label.setText(self.grid_info['name'])

class ShortcutDraggableButton(QPushButton):
    def __init__(self, action, grid_info, parent_section):
        super().__init__(action.objectName())
        self.action = action
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.setToolTip(", ".join([str(s.toString()) for s in action.shortcuts()]))
        self.setStyleSheet(shortcut_btn_style())
        self.drag_start_position = QPoint()
        self.clicked.connect(lambda: self.parent_section.run_krita_action(action.objectName()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if QApplication.keyboardModifiers() != Qt.ControlModifier:
            return
        if ((event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance()):
            return
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(f"shortcut_action:{self.action.objectName()}")
        drag.setMimeData(mimeData)
        drag.setHotSpot(QPoint(16, 16))
        drag.exec_(Qt.MoveAction)
