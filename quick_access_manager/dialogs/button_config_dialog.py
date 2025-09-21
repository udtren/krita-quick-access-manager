from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class ShortcutButtonConfigDialog(QDialog):
    """Dialog for configuring shortcut button properties"""

    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.button = button

        self.setup_ui()
        self.setup_connections()
        self.load_current_values()

    def setup_ui(self):
        """Setup the UI elements"""
        self.setWindowTitle("Shortcut Button Config")
        self.resize(300, 200)
        layout = QVBoxLayout()

        # Button name
        layout.addWidget(QLabel("Button Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        # Font size
        layout.addWidget(QLabel("Font Size:"))
        self.font_size_edit = QLineEdit()
        layout.addWidget(self.font_size_edit)

        # Background color
        layout.addWidget(QLabel("Background Color:"))
        self.bg_color_edit = QLineEdit()
        layout.addWidget(self.bg_color_edit)

        # Font color
        layout.addWidget(QLabel("Font Color:"))
        self.font_color_edit = QLineEdit()
        layout.addWidget(self.font_color_edit)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def setup_connections(self):
        """Setup button connections"""
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_current_values(self):
        """Load current button values into the form"""
        # Button name
        self.name_edit.setText(self.button.text())

        # Font size
        config = self.button.config
        font_size = (
            config.get("fontSize")
            if config
            else str(max(self.button.font().pointSize(), 7))
        )
        if not font_size or font_size == "-1":
            font_size = str(max(self.button.font().pointSize(), 7))
        self.font_size_edit.setText(str(font_size))

        # Colors
        self.bg_color_edit.setText(
            self.button.palette().color(self.button.backgroundRole()).name()
        )
        self.font_color_edit.setText(
            self.button.palette().color(self.button.foregroundRole()).name()
        )
