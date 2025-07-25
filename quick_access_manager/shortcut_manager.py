import json
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QMessageBox, QGridLayout, QInputDialog, QApplication
from PyQt5.QtCore import Qt, QSize, QMimeData, QPoint
from PyQt5.QtGui import QDrag
from PyQt5.QtGui import QFontMetrics
from krita import Krita
from .data_manager import load_shortcut_grids_data, save_shortcut_grids_data, log_save_grids_data, spacingValue
from .preprocess import check_common_config

COMMON_CONFIG = check_common_config()

def shortcut_btn_style():
    # 最新のCOMMON_CONFIGを毎回参照
    from .quick_access_manager import COMMON_CONFIG
    color = COMMON_CONFIG["color"]["shortcut_button_background_color"]
    font_color = COMMON_CONFIG["color"]["shortcut_button_font_color"]
    font_size = COMMON_CONFIG["font"]["shortcut_button_font_size"]
    return f"background-color: {color}; color: {font_color}; font-size: {font_size};"

def docker_btn_style():
    color = COMMON_CONFIG["color"]["docker_button_background_color"]
    font_color = COMMON_CONFIG["color"]["docker_button_font_color"]
    font_size = COMMON_CONFIG["font"]["docker_button_font_size"]
    return f"background-color: {color}; color: {font_color}; font-size: {font_size};"

# すべてのQActionを再帰的に取得
def get_all_actions():
    all_actions = {}
    app = Krita.instance()
    main_window = app.activeWindow()
    if not main_window:
        return []
    qwin = main_window.qwindow()
    widgets = [qwin]
    if hasattr(qwin, 'menuBar'):
        widgets.append(qwin.menuBar())
    if hasattr(qwin, 'toolBar'):
        widgets.append(qwin.toolBar())
    while widgets:
        widget = widgets.pop()
        if hasattr(widget, 'actions'):
            actions = widget.actions
            if callable(actions):
                actions = actions()
            for action in actions:
                if action and hasattr(action, "objectName") and action.objectName():
                    all_actions[action.objectName()] = action
        if hasattr(widget, 'children'):
            widgets.extend(child for child in widget.children() if hasattr(child, 'actions'))
    for action in app.actions():
        if action and hasattr(action, "objectName") and action.objectName():
            all_actions[action.objectName()] = action
    return list(all_actions.values())

def get_font_px(font_size_str):
    # "20px" -> 20
    try:
        return int(str(font_size_str).replace("px", ""))
    except Exception:
        return 12

def get_max_shortcut_per_row():
    # 最新のCOMMON_CONFIGを毎回参照
    from .quick_access_manager import COMMON_CONFIG
    return int(COMMON_CONFIG.get("layout", {}).get("max_shortcut_per_row", 3))

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
        self.actions = get_all_actions()
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
        self.main_layout.setSpacing(spacingValue)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # タイトルラベルを追加
        title_label = QLabel("Quick Shortcut Access")
        title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title_label)

        button_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("ShowAllShortcut")
        self.show_all_btn.setStyleSheet(docker_btn_style())
        self.add_grid_btn = QPushButton("AddGrid")
        self.add_grid_btn.setStyleSheet(docker_btn_style())
        button_layout.addWidget(self.show_all_btn)
        button_layout.addWidget(self.add_grid_btn)
        self.main_layout.addLayout(button_layout)

        # RestoreShortGridボタンを追加
        self.restore_grid_btn = QPushButton("RestoreShortcutGrid")
        self.restore_grid_btn.setStyleSheet(docker_btn_style())
        self.main_layout.addWidget(self.restore_grid_btn)

        self.setLayout(self.main_layout)

        self.show_all_btn.clicked.connect(self.show_all_shortcut_popup)
        self.add_grid_btn.clicked.connect(self.add_grid)
        self.restore_grid_btn.clicked.connect(self.restore_grids_from_file)

    def restore_grids_from_file(self):
        # 既存グリッドを全て削除
        for grid_widget in self.grids:
            self.main_layout.removeWidget(grid_widget)
            grid_widget.deleteLater()
        self.grids = []
        self.active_grid_idx = 0

        krita_instance = Krita.instance()
        # すべてのQActionをobjectNameで辞書化
        all_actions = {a.objectName(): a for a in get_all_actions()}

        # JSONからグリッドデータを取得
        grids_data = load_shortcut_grids_data(self.data_file, krita_instance)

        # グリッドを全て作成
        grid_name_to_widget = {}
        for grid_info in grids_data:
            grid_widget = self.add_shortcut_grid(grid_info['name'], [], save=False)
            grid_name_to_widget[grid_info['name']] = grid_widget
            # shortcut_configsも復元
            grid_widget.grid_info["shortcut_configs"] = grid_info.get("shortcut_configs", grid_info.get("shortcuts", []))

        # 各グリッドにボタンを追加
        for grid_info in grids_data:
            grid_widget = grid_name_to_widget.get(grid_info['name'])
            if not grid_widget:
                continue
            shortcut_configs = grid_info.get("shortcut_configs", grid_info.get("shortcuts", []))
            actions = []
            for config in shortcut_configs:
                action_id = config.get("actionName")
                action = all_actions.get(action_id)
                if action:
                    actions.append(action)
            grid_widget.grid_info['actions'] = actions
            grid_widget.update_grid()

        # 最初のグリッドをアクティブにする
        if self.grids:
            self.set_active_grid(0)

    def add_grid(self):
        grid_name = f"Shortcut Grid {len(self.grids) + 1}"
        self.add_shortcut_grid(grid_name, save=True)

    def add_shortcut_grid(self, grid_name, actions=None, save=True):
        # actionsがstrリスト（action_id）の場合はQActionリストに変換
        krita_instance = Krita.instance()
        if actions is None:
            actions = []
        elif all(isinstance(a, str) for a in actions):
            actions = [krita_instance.action(aid) for aid in actions if krita_instance.action(aid)]
        else:
            pass
        # それ以外（QActionリスト）はそのまま
        grid_info = {
            'name': grid_name,
            'actions': actions,
        }
        grid_widget = SingleShortcutGridWidget(grid_info, self)
        self.grids.append(grid_widget)
        self.main_layout.addWidget(grid_widget)
        self.set_active_grid(len(self.grids) - 1)
        if save:
            self.save_grids_data()
        return grid_widget  # 追加: 作成したウィジェットを返す

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
            # shortcut_configsを直接保存
            # log_save_grids_data(f"save_grids_data grid_widget: {grid_widget}")
            # log_save_grids_data(f"save_grids_data shortcut_configs: {grid_widget.grid_info.get('shortcut_configs', [])}")

            shortcuts = grid_widget.grid_info.get("shortcut_configs", [])
            grid_info = {
                'name': grid_widget.grid_info['name'],
                'shortcuts': shortcuts
            }
            grids_data.append(grid_info)
        try:
            save_shortcut_grids_data(self.data_file, grids_data)
            # log_save_grids_data(f"save_grids_data called. File: {self.data_file} Grids: {len(grids_data)}")
        except Exception as e:
            log_save_grids_data(f"save_grids_data ERROR: {str(e)}")

    def move_grid(self, grid_widget, direction):
        idx = self.grids.index(grid_widget)
        new_idx = idx + direction
        if 0 <= new_idx < len(self.grids):
            self.grids.pop(idx)
            self.grids.insert(new_idx, grid_widget)
            # レイアウトから全て削除して再追加
            for gw in self.grids:
                self.main_layout.removeWidget(gw)
            for gw in self.grids:
                self.main_layout.addWidget(gw)
            self.set_active_grid(new_idx)
            self.save_grids_data()

    def refresh_layout(self):
        for grid_widget in self.grids:
            grid_widget.update_grid()

class SingleShortcutGridWidget(QWidget):
    def __init__(self, grid_info, parent_section):
        super().__init__()
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.is_active = False
        self.shortcut_buttons = []

        self.setAcceptDrops(True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(spacingValue)
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
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setFixedSize(btn_width * 2, btn_height)
        self.remove_btn.setStyleSheet(docker_btn_style())
        header_layout.addWidget(self.up_btn)
        header_layout.addWidget(self.down_btn)
        header_layout.addWidget(self.rename_btn)
        header_layout.addWidget(self.active_btn)
        header_layout.addWidget(self.remove_btn)
        main_layout.addLayout(header_layout)

        self.shortcut_grid_layout = QGridLayout()
        self.shortcut_grid_layout.setSpacing(spacingValue)
        self.shortcut_grid_layout.setContentsMargins(2, 2, 2, 2)
        grid_area = QWidget()
        grid_area.setLayout(self.shortcut_grid_layout)
        grid_area.setStyleSheet("background: none;")
        main_layout.addWidget(grid_area)

        self.setLayout(main_layout)

        self.rename_btn.clicked.connect(self.rename_grid)
        self.active_btn.clicked.connect(self.activate_grid)
        self.up_btn.clicked.connect(lambda: self.parent_section.move_grid(self, -1))
        self.down_btn.clicked.connect(lambda: self.parent_section.move_grid(self, 1))
        self.remove_btn.clicked.connect(self.remove_grid)

    def add_shortcut_button(self, action):
        self.grid_info['actions'].append(action)
        # 個別設定がなければデフォルト値で追加
        if "shortcut_configs" not in self.grid_info:
            self.grid_info["shortcut_configs"] = []
        self.grid_info["shortcut_configs"].append({
            "actionName": action.objectName(),
            "customName": action.objectName(),
            "fontSize": str(get_font_px(COMMON_CONFIG["font"]["shortcut_button_font_size"])),
            "fontColor": COMMON_CONFIG["color"]["shortcut_button_font_color"],
            "backgroundColor": COMMON_CONFIG["color"]["shortcut_button_background_color"]
        })
        self.update_grid()
        if hasattr(self.parent_section, "save_grids_data"):
            self.parent_section.save_grids_data()

    def update_grid(self):
        while self.shortcut_grid_layout.count():
            item = self.shortcut_grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self.shortcut_buttons = []
        max_columns = get_max_shortcut_per_row()
        
        for idx, action in enumerate(self.grid_info['actions']):
            config = None

            # log_save_grids_data(f"self.grid_info['actions']: {self.grid_info['actions']}")
            # log_save_grids_data(f"self.grid_info[shortcut_configs]: {self.grid_info['shortcut_configs']}")

            if "shortcut_configs" in self.grid_info and idx < len(self.grid_info["shortcut_configs"]):
                config = self.grid_info["shortcut_configs"][idx]
            else:
                # デフォルト値で補完
                config = {
                    "actionName": action.objectName(),
                    "customName": action.objectName(),
                    "fontSize": str(get_font_px(COMMON_CONFIG["font"]["shortcut_button_font_size"])),
                    "fontColor": COMMON_CONFIG["color"]["shortcut_button_font_color"],
                    "backgroundColor": COMMON_CONFIG["color"]["shortcut_button_background_color"]
                }
            # log_save_grids_data(f"config: {config}")

            shortcut_btn = ShortcutDraggableButton(action, self.grid_info, self.parent_section, config)
            shortcut_btn.setMinimumSize(QSize(40, 28))

            # 個別設定がグローバル値と異なる場合のみ個別設定を適用
            font_color = config.get("fontColor", COMMON_CONFIG["color"]["shortcut_button_font_color"])
            bg_color = config.get("backgroundColor", COMMON_CONFIG["color"]["shortcut_button_background_color"])
            font_size = config.get("fontSize", COMMON_CONFIG["font"]["shortcut_button_font_size"])

            is_custom = (
                font_color != COMMON_CONFIG["color"]["shortcut_button_font_color"] or
                bg_color != COMMON_CONFIG["color"]["shortcut_button_background_color"] or
                f"{str(font_size)}px" != COMMON_CONFIG["font"]["shortcut_button_font_size"]
            )

            # log_save_grids_data(f'font_color: {font_color}')
            # log_save_grids_data(f'shortcut_button_font_color: {COMMON_CONFIG["color"]["shortcut_button_font_color"]}')
            # log_save_grids_data(f'bg_color: {bg_color}')
            # log_save_grids_data(f'shortcut_button_background_color: {COMMON_CONFIG["color"]["shortcut_button_background_color"]}')
            # log_save_grids_data(f'font_size: {f"{str(font_size)}px"}')
            # log_save_grids_data(f'shortcut_button_font_size: {COMMON_CONFIG["font"]["shortcut_button_font_size"]}')

            if is_custom:
                # log_save_grids_data(f"is_custom: True")
                shortcut_btn.setStyleSheet(
                    f"background-color: {bg_color}; color: {font_color}; font-size: {font_size}px;"
                )
            else:
                # log_save_grids_data(f"is_custom: False")
                shortcut_btn.setStyleSheet(shortcut_btn_style())

            row = idx // max_columns
            col = idx % max_columns
            self.shortcut_grid_layout.addWidget(shortcut_btn, row, col)
            self.shortcut_buttons.append(shortcut_btn)

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
                    max_columns = get_max_shortcut_per_row()
                    col = min(drop_pos.x() // 90, max_columns - 1)
                    row = drop_pos.y() // 36
                    target_index = row * max_columns + col

                    # shortcut_configsも同期して移動
                    source_configs = source_grid.get("shortcut_configs", [])
                    config_to_move = None
                    if source_configs and source_index < len(source_configs):
                        config_to_move = source_configs.pop(source_index)

                    # 同じグリッド内で移動の場合
                    if self.grid_info == source_grid:
                        if target_index > source_index:
                            target_index -= 1
                        source_grid['actions'].pop(source_index)
                        if config_to_move:
                            source_configs.insert(target_index, config_to_move)
                        source_grid['actions'].insert(target_index, source_action)
                        self.update_grid()
                    else:
                        source_grid['actions'].pop(source_index)
                        if config_to_move:
                            source_configs  # 既にpop済み
                        target_index = max(0, min(target_index, len(self.grid_info['actions'])))
                        self.grid_info['actions'].insert(target_index, source_action)
                        # shortcut_configsも追加
                        target_configs = self.grid_info.setdefault("shortcut_configs", [])
                        if config_to_move:
                            target_configs.insert(target_index, config_to_move)
                        grid_widget = self.parent_section.grids[self.parent_section.grids.index(self)]
                        grid_widget.update_grid()
                        for gw in self.parent_section.grids:
                            if gw.grid_info == source_grid:
                                gw.update_grid()
                                break
                    self.parent_section.save_grids_data()
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
            self.parent_section.save_grids_data()


    def remove_grid(self):
        if self in self.parent_section.grids:
            idx = self.parent_section.grids.index(self)
            self.parent_section.main_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()
            self.parent_section.grids.remove(self)
            if self.parent_section.grids:
                self.parent_section.set_active_grid(0)
            else:
                self.parent_section.active_grid_idx = 0
            self.parent_section.save_grids_data()

class ShortcutDraggableButton(QPushButton):
    def __init__(self, action, grid_info, parent_section, config=None):
        display_name = action.objectName()
        if config:
            custom_name = config.get("customName")
            if custom_name:
                display_name = custom_name
        super().__init__(display_name)
        self.action = action
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.custom_name = config.get("customName") if config else None
        self.config = config

        # フォントサイズ・色・背景色を反映
        font = self.font()
        font_size_str = config.get("fontSize", get_font_px(COMMON_CONFIG["font"]["shortcut_button_font_size"]))
        try:
            font_size = int(font_size_str)
            if font_size < 7:
                font_size = get_font_px(COMMON_CONFIG["font"]["shortcut_button_font_size"])
        except Exception:
            font_size = get_font_px(COMMON_CONFIG["font"]["shortcut_button_font_size"])
        font.setPointSize(font_size)
        self.setFont(font)

        font_color = config.get("fontColor", COMMON_CONFIG["color"]["shortcut_button_font_color"]) if config else COMMON_CONFIG["color"]["shortcut_button_font_color"]
        bg_color = config.get("backgroundColor", COMMON_CONFIG["color"]["shortcut_button_background_color"]) if config else COMMON_CONFIG["color"]["shortcut_button_background_color"]
        self.setStyleSheet(f"background-color: {bg_color}; color: {font_color};")
        self.drag_start_position = QPoint()
        self.clicked.connect(lambda: self.parent_section.run_krita_action(action.objectName()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
    #     self.adjust_text_to_fit()

    # def adjust_text_to_fit(self):
    #     font = self.font()
    #     config = self.config
    #     font_size = int(config.get("fontSize", 12)) if config else 12
    #     font.setPointSize(font_size)
    #     self.setFont(font)   

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        # Ctrl+Shift+Alt+左クリック: Indexを-1
        if (event.button() == Qt.LeftButton and
            modifiers == (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier)):
            idx = self.grid_info['actions'].index(self.action)
            if idx > 0:
                # actionsの並び替え
                self.grid_info['actions'].pop(idx)
                self.grid_info['actions'].insert(idx - 1, self.action)
                # shortcut_configsの並び替え
                if "shortcut_configs" in self.grid_info and idx < len(self.grid_info["shortcut_configs"]):
                    config = self.grid_info["shortcut_configs"].pop(idx)
                    self.grid_info["shortcut_configs"].insert(idx - 1, config)
                self.parent_section.save_grids_data()
                for grid_widget in self.parent_section.grids:
                    if grid_widget.grid_info is self.grid_info:
                        grid_widget.update_grid()
                        break
            return

        if (event.button() == Qt.RightButton and
            modifiers == (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier)):
            idx = self.grid_info['actions'].index(self.action)
            if idx < len(self.grid_info['actions']) - 1:
                # actionsの並び替え
                self.grid_info['actions'].pop(idx)
                self.grid_info['actions'].insert(idx + 1, self.action)
                # shortcut_configsの並び替え
                if "shortcut_configs" in self.grid_info and idx < len(self.grid_info["shortcut_configs"]):
                    config = self.grid_info["shortcut_configs"].pop(idx)
                    self.grid_info["shortcut_configs"].insert(idx + 1, config)
                self.parent_section.save_grids_data()
                for grid_widget in self.parent_section.grids:
                    if grid_widget.grid_info is self.grid_info:
                        grid_widget.update_grid()
                        break
            return
        # Ctrl+左クリック: グリッド間移動(ドラッグ)
        if event.button() == Qt.LeftButton and modifiers == Qt.ControlModifier:
            self.drag_start_position = event.pos()
        # Ctrl+右クリック: 削除
        if event.button() == Qt.RightButton and modifiers == Qt.ControlModifier:
            for i, act in enumerate(self.grid_info['actions']):
                if act.objectName() == self.action.objectName():
                    # actionsから削除
                    self.grid_info['actions'].pop(i)
                    # shortcut_configsも同期して削除
                    if "shortcut_configs" in self.grid_info and i < len(self.grid_info["shortcut_configs"]):
                        self.grid_info["shortcut_configs"].pop(i)
                    self.parent_section.save_grids_data()
                    for grid_widget in self.parent_section.grids:
                        if grid_widget.grid_info is self.grid_info:
                            grid_widget.update_grid()
                            break
                    break
            return
        # Alt+右クリック: 個別設定ポップアップ
        if event.button() == Qt.RightButton and modifiers == Qt.AltModifier:
            dlg = ShortcutButtonConfigDialog(self)
            if dlg.exec_():
                # フォントサイズのバリデーション
                font_size_str = dlg.font_size_edit.text().strip()
                try:
                    font_size = int(font_size_str)
                    if font_size < 7:  # 最小サイズ
                        font_size = 12
                except Exception:
                    font_size = 12  # デフォルト

                # 設定をgrid_infoのshortcut_configsに保存
                idx = self.grid_info['actions'].index(self.action)
                if "shortcut_configs" not in self.grid_info:
                    self.grid_info["shortcut_configs"] = [{} for _ in self.grid_info["actions"]]
                self.grid_info["shortcut_configs"][idx] = {
                    "actionName": self.action.objectName(),
                    "customName": dlg.name_edit.text(),
                    "fontSize": str(font_size),
                    "fontColor": dlg.font_color_edit.text(),
                    "backgroundColor": dlg.bg_color_edit.text()
                }
                # update_gridで再生成時に反映
                for grid_widget in self.parent_section.grids:
                    if grid_widget.grid_info is self.grid_info:
                        grid_widget.update_grid()
                        break
                self.parent_section.save_grids_data()
                return
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

class ShortcutButtonConfigDialog(QDialog):
    def __init__(self, btn, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcut Button Config")
        self.resize(300, 180)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ボタン名
        layout.addWidget(QLabel("Button Name:"))
        self.name_edit = QLineEdit(btn.text())
        layout.addWidget(self.name_edit)

        # フォントサイズ
        layout.addWidget(QLabel("Font Size:"))
        font_size = btn.config.get("fontSize") if btn.config else str(max(btn.font().pointSize(), 7))
        if not font_size or font_size == "-1":
            font_size = str(max(btn.font().pointSize(), 7))
        self.font_size_edit = QLineEdit(str(font_size))
        layout.addWidget(self.font_size_edit)

        # 背景色
        layout.addWidget(QLabel("Background Color:"))
        self.bg_color_edit = QLineEdit(btn.palette().color(btn.backgroundRole()).name())
        layout.addWidget(self.bg_color_edit)

        # フォント色
        layout.addWidget(QLabel("Font Color:"))
        self.font_color_edit = QLineEdit(btn.palette().color(btn.foregroundRole()).name())
        layout.addWidget(self.font_color_edit)

        btns = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
