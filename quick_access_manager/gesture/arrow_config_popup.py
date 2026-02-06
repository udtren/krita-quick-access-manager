from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QMessageBox,
)
from krita import Krita  # type: ignore
from .action_popup import GestureActionPopup


class ArrowConfigPopup(QDialog):
    """Dialog for configuring a gesture arrow action"""

    def __init__(self, direction, config_name, parent_dialog, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.config_name = config_name
        self.parent_dialog = parent_dialog
        self.gesture_config = None

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the UI elements"""
        self.setWindowTitle(f"Configure Gesture: {self.direction}")
        self.resize(400, 200)
        layout = QVBoxLayout()

        # Apply dark mode styling
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                background-color: transparent;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #e0e0e0;
                selection-background-color: #4a4a4a;
                border: 1px solid #555;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
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

        # Type selection
        type_label = QLabel("Gesture Type:")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Brush Preset", "Action", "Docker Toggle", "None"])
        layout.addWidget(self.type_combo)

        # Docker name input (initially hidden)
        self.docker_label = QLabel("Docker Name:")
        self.docker_input = QLineEdit()
        self.docker_input.setPlaceholderText("Enter docker name (e.g., 'Tool Options')")
        self.docker_label.hide()
        self.docker_input.hide()
        layout.addWidget(self.docker_label)
        layout.addWidget(self.docker_input)

        layout.addStretch()

        # Button layout
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def setup_connections(self):
        """Setup signal connections"""
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.ok_btn.clicked.connect(self.on_ok_clicked)
        self.cancel_btn.clicked.connect(self.reject)

    def on_type_changed(self, text):
        """Handle gesture type change"""
        # Show/hide docker input based on selection
        if text == "Docker Toggle":
            self.docker_label.show()
            self.docker_input.show()
        else:
            self.docker_label.hide()
            self.docker_input.hide()

    def on_ok_clicked(self):
        """Handle OK button click"""
        gesture_type = self.type_combo.currentText()

        if gesture_type == "Brush Preset":
            self.configure_brush_preset()
        elif gesture_type == "Action":
            self.configure_action()
        elif gesture_type == "Docker Toggle":
            self.configure_docker_toggle()
        elif gesture_type == "None":
            self.configure_none()

    def configure_brush_preset(self):
        """Configure brush preset gesture"""
        # Get current brush
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            current_preset = app.activeWindow().activeView().currentBrushPreset()
            if current_preset:
                self.gesture_config = {
                    "gesture_type": "brush",
                    "parameters": {"brush_name": current_preset.name()},
                }
                self.accept()
            else:
                QMessageBox.warning(
                    self, "No Brush Selected", "Please select a brush preset first."
                )
        else:
            QMessageBox.warning(
                self, "No Active View", "Please open a document in Krita first."
            )

    def configure_action(self):
        """Configure action gesture"""
        # Open action selection dialog
        action_dialog = GestureActionPopup(self)
        if action_dialog.exec_():
            action_id = action_dialog.get_action_id()
            if action_id:
                self.gesture_config = {
                    "gesture_type": "action",
                    "parameters": {"action_id": action_id},
                }
                self.accept()

    def configure_docker_toggle(self):
        """Configure docker toggle gesture"""
        docker_name = self.docker_input.text().strip()
        if not docker_name:
            QMessageBox.warning(self, "No Docker Name", "Please enter a docker name.")
            return

        self.gesture_config = {
            "gesture_type": "docker_toggle",
            "parameters": {"docker_name": docker_name},
        }
        self.accept()

    def configure_none(self):
        """Configure no action gesture"""
        self.gesture_config = None
        self.accept()

    def get_gesture_config(self):
        """Return the configured gesture"""
        return self.gesture_config
