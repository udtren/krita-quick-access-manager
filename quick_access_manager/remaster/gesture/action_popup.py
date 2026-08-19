"""Dialog for selecting Krita actions for gesture configuration."""

from ..compat import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from ..infrastructure import ActionManager


class GestureActionPopup(QDialog):
    """Dialog for selecting Krita actions for gesture configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions = []
        self.selected_action_id = None

        self.setup_ui()
        self.setup_connections()
        self.populate_table()

    def setup_ui(self):
        self.setWindowTitle("Select Krita Action")
        self.resize(600, 400)
        layout = QVBoxLayout()

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                gridline-color: #555;
                border: 1px solid #555;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
                border: 1px solid #444;
            }
        """)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by action ID...")
        layout.addWidget(self.filter_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action ID", "Shortcut Keys"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def setup_connections(self):
        self.filter_edit.textChanged.connect(self.apply_filter)
        self.ok_btn.clicked.connect(self.accept_selection)
        self.cancel_btn.clicked.connect(self.reject)
        self.table.itemDoubleClicked.connect(self.accept_selection)

    def populate_table(self):
        self._actions = ActionManager.get_all_actions()
        self.table.setRowCount(len(self._actions))

        for i, action in enumerate(self._actions):
            id_item = QTableWidgetItem(action.objectName())
            self.table.setItem(i, 0, id_item)

            shortcuts_text = ", ".join(str(s.toString()) for s in action.shortcuts())
            self.table.setItem(i, 1, QTableWidgetItem(shortcuts_text))

    def apply_filter(self, text):
        for i in range(self.table.rowCount()):
            id_item = self.table.item(i, 0)
            self.table.setRowHidden(i, text.lower() not in id_item.text().lower())

    def get_selected_action(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            return self._actions[row]
        return None

    def accept_selection(self):
        action = self.get_selected_action()
        if not action:
            QMessageBox.warning(
                self, "No Action Selected", "Please select an action from the table."
            )
            return

        self.selected_action_id = action.objectName()
        self.accept()

    def get_action_id(self):
        return self.selected_action_id
