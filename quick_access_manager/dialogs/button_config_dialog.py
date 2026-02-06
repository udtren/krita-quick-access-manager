from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QColorDialog,
)
from PyQt6.QtGui import QColor


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
        self.bg_color = QColor("#888888")
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedHeight(24)
        self.bg_color_button.clicked.connect(self.pick_bg_color)
        layout.addWidget(self.bg_color_button)

        # Font color
        layout.addWidget(QLabel("Font Color:"))
        self.font_color = QColor("#000000")
        self.font_color_button = QPushButton()
        self.font_color_button.setFixedHeight(24)
        self.font_color_button.clicked.connect(self.pick_font_color)
        layout.addWidget(self.font_color_button)

        # Icon name
        layout.addWidget(QLabel("Icon Name:"))
        self.icon_name_edit = QLineEdit()
        layout.addWidget(self.icon_name_edit)

        # Use global settings
        layout.addWidget(QLabel("Use Global Settings:"))
        self.use_global_settings_flag = QCheckBox()
        layout.addWidget(self.use_global_settings_flag)

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
        # Button name - get from config if available, otherwise from button text
        config = self.button.config
        if config and config.get("customName"):
            self.name_edit.setText(config.get("customName"))
        else:
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
        self.bg_color = QColor(
            self.button.palette().color(self.button.backgroundRole()).name()
        )
        self.font_color = QColor(
            self.button.palette().color(self.button.foregroundRole()).name()
        )
        self.update_color_buttons()

        # Icon name
        icon_name = config.get("icon_name", "") if config else ""
        self.icon_name_edit.setText(icon_name)

        # global settings flag
        if config.get("useGlobalSettings") is True:
            self.use_global_settings_flag.setChecked(True)

    def update_color_buttons(self):
        """Update color button backgrounds to show selected colors"""
        self.bg_color_button.setStyleSheet(
            f"background-color: {self.bg_color.name()}; border: 1px solid #888;"
        )
        self.bg_color_button.setText(self.bg_color.name())
        self.font_color_button.setStyleSheet(
            f"background-color: {self.font_color.name()}; border: 1px solid #888;"
        )
        self.font_color_button.setText(self.font_color.name())

    def pick_bg_color(self):
        """Open color picker for background color"""
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color
            self.update_color_buttons()

    def pick_font_color(self):
        """Open color picker for font color"""
        color = QColorDialog.getColor(self.font_color, self, "Select Font Color")
        if color.isValid():
            self.font_color = color
            self.update_color_buttons()

    def get_bg_color_hex(self):
        """Get background color as hex string"""
        return self.bg_color.name()

    def get_font_color_hex(self):
        """Get font color as hex string"""
        return self.font_color.name()
