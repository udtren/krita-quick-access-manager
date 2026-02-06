from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from ..utils.action_manager import ActionManager


class GestureActionPopup(QDialog):
    """Dialog for selecting Krita actions for gesture configuration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.actions = []
        self.selected_action_id = None

        self.setup_ui()
        self.setup_connections()
        self.populate_table()

    def setup_ui(self):
        """Setup the UI elements"""
        self.setWindowTitle("Select Krita Action")
        self.resize(600, 400)
        layout = QVBoxLayout()

        # Apply dark mode styling
        self.setStyleSheet(
            """
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
        """
        )

        # Filter input
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by action ID...")
        layout.addWidget(self.filter_edit)

        # Actions table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action ID", "Shortcut Keys"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Button layout
        from PyQt6.QtWidgets import QHBoxLayout

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def setup_connections(self):
        """Setup signal connections"""
        self.filter_edit.textChanged.connect(self.apply_filter)
        self.ok_btn.clicked.connect(self.accept_selection)
        self.cancel_btn.clicked.connect(self.reject)
        self.table.itemDoubleClicked.connect(self.accept_selection)

    def populate_table(self):
        """Populate the table with available actions"""
        self.actions = ActionManager.get_all_actions()
        self.table.setRowCount(len(self.actions))

        for i, action in enumerate(self.actions):
            # Action ID column
            id_item = QTableWidgetItem(action.objectName())
            self.table.setItem(i, 0, id_item)

            # Shortcuts column
            shortcuts_text = ", ".join([str(s.toString()) for s in action.shortcuts()])
            shortcut_item = QTableWidgetItem(shortcuts_text)
            self.table.setItem(i, 1, shortcut_item)

    def apply_filter(self, text):
        """Apply filter to the actions table"""
        for i in range(self.table.rowCount()):
            id_item = self.table.item(i, 0)
            should_hide = text.lower() not in id_item.text().lower()
            self.table.setRowHidden(i, should_hide)

    def get_selected_action(self):
        """Get the currently selected action"""
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            return self.actions[row]
        return None

    def accept_selection(self):
        """Accept the selected action"""
        action = self.get_selected_action()
        if not action:
            QMessageBox.warning(
                self, "No Action Selected", "Please select an action from the table."
            )
            return

        self.selected_action_id = action.objectName()
        self.accept()

    def get_action_id(self):
        """Return the selected action ID"""
        return self.selected_action_id
