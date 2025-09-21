from PyQt5.QtWidgets import (
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
from ..utils.styles import docker_btn_style


class ShortcutPopup(QDialog):
    """Dialog for selecting Krita actions to add as shortcuts"""

    def __init__(self, parent_section):
        super().__init__(parent_section)
        self.parent_section = parent_section
        self.actions = []

        self.setup_ui()
        self.setup_connections()
        self.populate_table()

    def setup_ui(self):
        """Setup the UI elements"""
        self.setWindowTitle("Krita Actions")
        self.resize(600, 400)
        layout = QVBoxLayout()

        # Add action button
        self.add_shortcut_btn = QPushButton("AddAction")
        self.add_shortcut_btn.setStyleSheet(docker_btn_style())
        layout.addWidget(self.add_shortcut_btn)

        # Filter input
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by internal ID...")
        layout.addWidget(self.filter_edit)

        # Actions table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action ID", "Shortcut Keys"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def setup_connections(self):
        """Setup signal connections"""
        self.add_shortcut_btn.clicked.connect(self.add_selected_shortcut_to_grid)
        self.filter_edit.textChanged.connect(self.apply_filter)

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

    def add_selected_shortcut_to_grid(self):
        """Add the selected action to the grid"""
        action = self.get_selected_action()
        if not action:
            QMessageBox.warning(
                self, "No Shortcut", "Please select a shortcut in the table."
            )
            return

        self.parent_section.add_shortcut_to_grid(action)
        self.accept()  # Close dialog after adding
