import json
import os
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QWidget,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon


class GestureConfigDialog(QDialog):
    """Dialog for configuring gesture shortcuts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gesture Configuration")
        self.resize(600, 500)

        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.image_dir = os.path.join(os.path.dirname(__file__), "image")
        self.configs = {}

        self.setup_ui()
        self.load_configs()

    def setup_ui(self):
        """Setup the UI elements"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

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
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
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
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
                border-bottom-color: #2b2b2b;
            }
            QTabBar::tab:hover {
                background-color: #454545;
            }
        """
        )

        # Tab widget for different config files
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        # Connect buttons
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    def load_configs(self):
        """Load all JSON config files from the config directory"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            return

        # Find all JSON files
        json_files = [f for f in os.listdir(self.config_dir) if f.endswith(".json")]

        if not json_files:
            # Create a default tab if no configs exist
            self.add_config_tab("Default", {})
            return

        for json_file in sorted(json_files):
            config_path = os.path.join(self.config_dir, json_file)
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Use filename without extension as tab name
                tab_name = os.path.splitext(json_file)[0]
                self.configs[tab_name] = {"path": config_path, "data": config_data}

                self.add_config_tab(tab_name, config_data)
            except Exception as e:
                print(f"Error loading config {json_file}: {e}")

    def add_config_tab(self, name, config_data):
        """Add a new tab with gesture configuration UI"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout()
        tab_widget.setLayout(tab_layout)

        # Create the 3x3 gesture grid
        gesture_grid = self.create_gesture_grid(name, config_data)
        tab_layout.addLayout(gesture_grid)

        tab_layout.addStretch()

        # Add tab to tab widget
        self.tab_widget.addTab(tab_widget, name)

    def create_gesture_grid(self, config_name, config_data):
        """Create the 3x3 grid of gesture arrows and labels"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Direction mappings: (row, col) -> direction_key
        direction_map = {
            (0, 0): "left_up",
            (0, 1): "up",
            (0, 2): "right_up",
            (1, 0): "left",
            (1, 1): "center",  # Special case for the key config button
            (1, 2): "right",
            (2, 0): "left_down",
            (2, 1): "down",
            (2, 2): "right_down",
        }

        for (row, col), direction in direction_map.items():
            if direction == "center":
                # Center button for gesture key configuration
                key_button = QPushButton("Config Key")
                key_button.setMinimumSize(80, 80)
                key_button.clicked.connect(
                    lambda _, cn=config_name: self.config_gesture_key(cn)
                )
                grid_layout.addWidget(key_button, 2, 2)  # Center of 5x5 grid
            else:
                # Create arrow button with image icon
                arrow_btn = QPushButton()

                # Load icon image
                icon_path = os.path.join(self.image_dir, f"{direction}.png")
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    arrow_btn.setIcon(icon)
                    arrow_btn.setIconSize(QSize(32, 32))
                else:
                    # Fallback to text if image not found
                    arrow_btn.setText(direction)

                arrow_btn.setMinimumSize(60, 60)
                arrow_btn.setProperty("direction", direction)
                arrow_btn.setProperty("config_name", config_name)
                arrow_btn.clicked.connect(self.config_gesture_action)

                # Create label to show current config
                gesture_config = config_data.get(direction, {})
                label_text = self.format_gesture_label(gesture_config)
                config_label = QLabel(label_text)
                config_label.setAlignment(Qt.AlignCenter)
                config_label.setWordWrap(True)
                config_label.setMinimumWidth(100)
                config_label.setProperty("direction", direction)
                config_label.setProperty("config_name", config_name)

                # Position based on direction in 5x5 grid
                label_col = col * 2  # Label columns: 0, 2, 4
                arrow_col = col + 1  # Arrow columns: 1, 2, 3

                if row == 0:  # Top row
                    grid_layout.addWidget(config_label, 0, label_col)
                    grid_layout.addWidget(arrow_btn, 1, arrow_col)
                elif row == 1:  # Middle row
                    if col == 0:  # Left
                        grid_layout.addWidget(config_label, 2, 0)
                        grid_layout.addWidget(arrow_btn, 2, 1)
                    else:  # Right (col == 2)
                        grid_layout.addWidget(arrow_btn, 2, 3)
                        grid_layout.addWidget(config_label, 2, 4)
                else:  # Bottom row (row == 2)
                    grid_layout.addWidget(arrow_btn, 3, arrow_col)
                    grid_layout.addWidget(config_label, 4, label_col)

        return grid_layout

    def format_gesture_label(self, gesture_config):
        """Format gesture configuration for display in label"""
        if not gesture_config:
            return "[Empty]"

        gesture_type = gesture_config.get("gesture_type", "unknown")
        parameters = gesture_config.get("parameters", {})

        if gesture_type == "action":
            return f"Action:\n{parameters.get('action_id', 'N/A')}"
        elif gesture_type == "brush":
            return f"Brush:\n{parameters.get('brush_name', 'N/A')}"
        elif gesture_type == "docker_toggle":
            return f"Docker:\n{parameters.get('docker_name', 'N/A')}"
        else:
            return f"{gesture_type}"

    def config_gesture_action(self):
        """Open dialog to configure a gesture action"""
        button = self.sender()
        direction = button.property("direction")
        config_name = button.property("config_name")

        # Placeholder dialog - will be implemented later
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Configure Gesture: {direction}")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Configuration for {direction} gesture"))
        layout.addWidget(QLabel(f"Config: {config_name}"))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def config_gesture_key(self, config_name):
        """Open dialog to configure the gesture trigger key"""
        # Placeholder dialog - will be implemented later
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Gesture Key")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Configure gesture trigger key for: {config_name}"))
        layout.addWidget(QLabel("Press the key combination you want to use"))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_and_close(self):
        """Save all configurations and close dialog"""
        for config_name, config_info in self.configs.items():
            try:
                with open(config_info["path"], "w", encoding="utf-8") as f:
                    json.dump(config_info["data"], f, indent=4)
            except Exception as e:
                print(f"Error saving config {config_name}: {e}")

        self.accept()


# if __name__ == "__main__":
#     import sys
#     from PyQt5.QtWidgets import QApplication

#     app = QApplication(sys.argv)
#     dialog = GestureConfigDialog()
#     dialog.show()
#     sys.exit(app.exec_())
