from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QMessageBox, QGridLayout, QInputDialog
from PyQt5.QtCore import Qt, QSize
from krita import Krita

class ShortcutPopup(QDialog):
    def __init__(self, parent_section):
        super().__init__(parent_section)
        self.parent_section = parent_section
        self.setWindowTitle("All Krita Shortcuts")
        self.resize(600, 400)
        layout = QVBoxLayout()

        # AddShortCutボタンを一番上に配置
        self.add_shortcut_btn = QPushButton("AddShortCut")
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

class ShortcutGridWidget(QWidget):
    def __init__(self, grid_info, parent_section):
        super().__init__()
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.layout = QGridLayout()
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.layout)
        self.buttons = []
        self.update_grid()

    def add_shortcut_button(self, action):
        self.grid_info['actions'].append(action)
        self.update_grid()

    def update_grid(self):
        # Remove all widgets safely
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        # ボタンリストを再構築
        self.buttons = []
        max_columns = 3
        for idx, action in enumerate(self.grid_info['actions']):
            action_id = action.objectName()
            shortcut_btn = QPushButton(action_id)
            shortcut_btn.setToolTip(", ".join([str(s.toString()) for s in action.shortcuts()]))
            shortcut_btn.setStyleSheet("font-size: 12px; margin: 2px;")
            shortcut_btn.setMinimumSize(QSize(80, 32))
            shortcut_btn.clicked.connect(lambda checked, aid=action_id: self.parent_section.run_krita_action(aid))
            self.buttons.append(shortcut_btn)
            row = idx // max_columns
            col = idx % max_columns
            self.layout.addWidget(shortcut_btn, row, col)

class ShortcutAccessSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent
        self.grid_info = {
            'name': 'Shortcut Grid 1',
            'actions': [],
        }
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header row: left=grid name, right=↑↓Rename+Active
        header_layout = QHBoxLayout()
        self.grid_name_label = QLabel(self.grid_info['name'])
        self.grid_name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(self.grid_name_label, alignment=Qt.AlignLeft)

        header_layout.addStretch()

        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(24, 20)
        self.up_btn.setStyleSheet("font-size: 10px;")
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(24, 20)
        self.down_btn.setStyleSheet("font-size: 10px;")
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setFixedSize(50, 20)
        self.rename_btn.setStyleSheet("font-size: 10px;")
        self.active_btn = QPushButton("Active")
        self.active_btn.setFixedSize(50, 20)
        self.active_btn.setStyleSheet("font-size: 10px;")
        header_layout.addWidget(self.up_btn)
        header_layout.addWidget(self.down_btn)
        header_layout.addWidget(self.rename_btn)
        header_layout.addWidget(self.active_btn)
        main_layout.addLayout(header_layout)

        # Button row (ShowAllShortcut, AddGrid)
        button_layout = QHBoxLayout()
        self.add_grid_btn = QPushButton("AddGrid")
        self.show_all_btn = QPushButton("ShowAllShortcut")
        button_layout.addWidget(self.add_grid_btn)
        button_layout.addWidget(self.show_all_btn)
        main_layout.addLayout(button_layout)

        # Shortcut grid area (dynamic grid)
        self.shortcut_grid_widget = ShortcutGridWidget(self.grid_info, self)
        main_layout.addWidget(self.shortcut_grid_widget)

        self.setLayout(main_layout)

        # Connect buttons
        self.show_all_btn.clicked.connect(self.show_all_shortcut_popup)
        self.rename_btn.clicked.connect(self.rename_grid)
        self.up_btn.clicked.connect(lambda: self.move_grid(-1))
        self.down_btn.clicked.connect(lambda: self.move_grid(1))
        self.active_btn.clicked.connect(self.set_active_grid)

        self.selected_action = None
        self.shortcut_popup = None
        self.is_active = False

    def show_all_shortcut_popup(self):
        self.shortcut_popup = ShortcutPopup(self)
        self.shortcut_popup.exec_()

    def run_krita_action(self, action_id):
        action = Krita.instance().action(action_id)
        if action:
            action.trigger()
        else:
            QMessageBox.warning(self, "Action Error", f"Action '{action_id}' not found.")

    def rename_grid(self):
        new_name, ok = QInputDialog.getText(self, "Rename Shortcut Grid", "Enter new grid name:", text=self.grid_info['name'])
        if ok and new_name.strip():
            self.grid_info['name'] = new_name.strip()
            self.grid_name_label.setText(self.grid_info['name'])

    def move_grid(self, direction):
        # Placeholder: implement multi-grid support if needed
        QMessageBox.information(self, "Move Grid", "Multi-grid shortcut support not implemented yet.")

    def add_shortcut_to_grid(self, action):
        self.shortcut_grid_widget.add_shortcut_button(action)

    def set_active_grid(self):
        # Active状態を切り替え（複数グリッド対応時は他グリッドの非Active化も必要）
        self.is_active = True
        self.update_grid_style()

    def update_grid_style(self):
        # Active状態で枠色・ラベル色変更
        if self.is_active:
            self.shortcut_grid_widget.setStyleSheet("""
                QWidget {
                    border: 2px solid #0078d4;
                    background-color: #f0f8ff;
                }
            """)
            self.grid_name_label.setStyleSheet("""
                font-weight: bold;
                font-size: 13px;
                color: #4FC3F7;
            """)
        else:
            self.shortcut_grid_widget.setStyleSheet("""
                QWidget {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                }
            """)
            self.grid_name_label.setStyleSheet("""
                font-weight: bold;
                font-size: 13px;
                color: #333333;
            """)
