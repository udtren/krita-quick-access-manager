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
    QTextEdit,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QKeyEvent
from krita import Krita  # type: ignore
from .arrow_config_popup import ArrowConfigPopup
from .gesture_main import (
    reload_gesture_configs,
    get_gesture_manager,
    set_config_dialog_active,
    pause_gesture_event_filter,
    resume_gesture_event_filter,
    enable_gesture_preview,
    refresh_gesture_setting,
)
from ..utils.logs import write_log


class GestureConfigDialog(QDialog):
    """Dialog for configuring gesture shortcuts"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Make the dialog modeless and stay on top
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.setWindowTitle("Gesture Configuration")
        self.resize(600, 500)

        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.image_dir = os.path.join(os.path.dirname(__file__), "image")
        self.configs = {}
        self.label_widgets = {}  # Store label widgets for updating
        # gesture.json is now in the gesture folder, not in config subfolder
        self.gesture_settings_path = os.path.join(
            os.path.dirname(__file__), "gesture.json"
        )

        # Get brush presets dictionary
        try:
            self.preset_dict = Krita.instance().resources("preset")
        except:
            self.preset_dict = {}

        self.setup_ui()
        self.load_configs()
        self.load_gesture_settings()
        self.update_indicator()

        # Notify gesture system that config dialog is active
        set_config_dialog_active(True)

    # ========================================================================
    # UI Setup and Loading/Saving Configs
    # ========================================================================
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
        top_layout = QHBoxLayout()
        self.tab_widget = QTabWidget()
        top_layout.addStretch()

        # Get icon directory path (reused for both buttons)
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "system_icon")

        # Plus button to add new config
        self.plus_btn = QPushButton()
        add_icon = QIcon(os.path.join(icon_dir, "add.png"))
        self.plus_btn.setIcon(add_icon)
        self.plus_btn.setIconSize(QSize(18, 18))
        self.plus_btn.setFixedSize(22, 22)
        self.plus_btn.setToolTip("Add new gesture config")
        self.plus_btn.setStyleSheet("""
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #6a6a6a;
            }
        """)
        self.plus_btn.clicked.connect(self.add_new_config)

        top_layout.addWidget(self.plus_btn)

        # Settings button
        self.settings_btn = QPushButton()
        settings_icon = QIcon(os.path.join(icon_dir, "setting.png"))
        self.settings_btn.setIcon(settings_icon)
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setFixedSize(22, 22)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #6a6a6a;
            }
        """)
        self.settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(self.settings_btn)
        # Status indicator (green/gray circle)
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self.status_indicator.setStyleSheet(
            """
            QLabel {
                background-color: #808080;
                border-radius: 2px;
                border: 2px solid #555;
            }
        """
        )
        self.status_indicator.setToolTip("Gesture system status")
        top_layout.addWidget(self.status_indicator)

        main_layout.addLayout(top_layout)

        main_layout.addWidget(self.tab_widget)

        # Bottom buttons: Indicator, Enable/Disable, Plus, Save, Cancel
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        # Connect buttons
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    # ========================================================================
    # Gesture Grid Creation and Handlers
    # ========================================================================
    def create_gesture_grid(self, config_name, config_data):
        """Create the 3x3 grid of gesture arrows and labels"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setAlignment(Qt.AlignCenter)

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
                current_key = config_data.get("gesture_key", "")
                button_text = f"Key: {current_key}" if current_key else "Config Key"
                key_button = QPushButton(button_text)
                key_button.setFixedSize(80, 30)
                key_button.setProperty("config_name", config_name)
                key_button.clicked.connect(
                    lambda _, cn=config_name, btn=key_button: self.config_gesture_key(
                        cn, btn
                    )
                )

                # Create label to show center action config
                gesture_config = config_data.get("center", {})
                label_text = self.format_gesture_label(gesture_config)
                center_label = QLabel(label_text)
                center_label.setAlignment(Qt.AlignCenter)
                center_label.setWordWrap(True)
                center_label.setFixedSize(100, 60)
                center_label.setProperty("direction", "center")
                center_label.setProperty("config_name", config_name)

                # If it's a brush preset, try to show the brush image
                if gesture_config.get("gesture_type") == "brush":
                    brush_name = gesture_config.get("parameters", {}).get("brush_name")
                    if brush_name and brush_name in self.preset_dict:
                        preset = self.preset_dict[brush_name]
                        try:
                            preset_image = preset.image()
                            if preset_image:
                                pixmap = QPixmap.fromImage(preset_image).scaled(
                                    64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                                )
                                center_label.setPixmap(pixmap)
                                center_label.setText(
                                    ""
                                )  # Clear text when showing image
                        except:
                            pass  # Keep text label if image fails

                # Store label widget for later updates
                label_key = f"{config_name}_center"
                self.label_widgets[label_key] = center_label

                # Create vertical layout for center (button + label)
                from PyQt5.QtWidgets import QVBoxLayout

                center_widget = QWidget()
                center_layout = QVBoxLayout()
                center_layout.setSpacing(5)
                center_layout.addWidget(key_button, alignment=Qt.AlignCenter)
                center_layout.addWidget(center_label, alignment=Qt.AlignCenter)
                center_widget.setLayout(center_layout)

                grid_layout.addWidget(
                    center_widget, 2, 2, Qt.AlignCenter
                )  # Center of 5x5 grid
            else:
                # Create arrow button with image icon
                arrow_btn = QPushButton()

                # Load icon image
                icon_path = os.path.join(self.image_dir, f"{direction}.png")
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    arrow_btn.setIcon(icon)
                    arrow_btn.setIconSize(QSize(64, 64))
                else:
                    # Fallback to text if image not found
                    arrow_btn.setText(direction)

                arrow_btn.setFixedSize(64, 64)
                arrow_btn.setProperty("direction", direction)
                arrow_btn.setProperty("config_name", config_name)
                arrow_btn.clicked.connect(self.config_gesture_action)

                # Create label to show current config
                gesture_config = config_data.get(direction, {})
                label_text = self.format_gesture_label(gesture_config)
                config_label = QLabel(label_text)
                config_label.setAlignment(Qt.AlignCenter)
                config_label.setWordWrap(True)
                config_label.setMinimumSize(100, 100)
                config_label.setMaximumHeight(100)
                config_label.setProperty("direction", direction)
                config_label.setProperty("config_name", config_name)

                # If it's a brush preset, try to show the brush image
                if gesture_config.get("gesture_type") == "brush":
                    brush_name = gesture_config.get("parameters", {}).get("brush_name")
                    if brush_name and brush_name in self.preset_dict:
                        preset = self.preset_dict[brush_name]
                        try:
                            preset_image = preset.image()
                            if preset_image:
                                pixmap = QPixmap.fromImage(preset_image).scaled(
                                    64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                                )
                                config_label.setPixmap(pixmap)
                                config_label.setText(
                                    ""
                                )  # Clear text when showing image
                        except:
                            pass  # Keep text label if image fails

                # Store label widget for later updates
                label_key = f"{config_name}_{direction}"
                self.label_widgets[label_key] = config_label

                # Position based on direction in 5x5 grid
                label_col = col * 2  # Label columns: 0, 2, 4
                arrow_col = col + 1  # Arrow columns: 1, 2, 3

                if row == 0:  # Top row
                    grid_layout.addWidget(config_label, 0, label_col, Qt.AlignCenter)
                    grid_layout.addWidget(arrow_btn, 1, arrow_col, Qt.AlignCenter)
                elif row == 1:  # Middle row
                    if col == 0:  # Left
                        grid_layout.addWidget(config_label, 2, 0, Qt.AlignCenter)
                        grid_layout.addWidget(arrow_btn, 2, 1, Qt.AlignCenter)
                    else:  # Right (col == 2)
                        grid_layout.addWidget(arrow_btn, 2, 3, Qt.AlignCenter)
                        grid_layout.addWidget(config_label, 2, 4, Qt.AlignCenter)
                else:  # Bottom row (row == 2)
                    grid_layout.addWidget(arrow_btn, 3, arrow_col, Qt.AlignCenter)
                    grid_layout.addWidget(config_label, 4, label_col, Qt.AlignCenter)

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

    # ========================================================================
    def load_configs(self):
        """Load all JSON config files from the config directory"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            return

        # Find all JSON files (excluding gesture.json which is for settings)
        json_files = [
            f
            for f in os.listdir(self.config_dir)
            if f.endswith(".json") and f != "gesture.json"
        ]

        if not json_files:
            # Create a default tab if no configs exist
            self.add_config_tab("1", {})
            return

        for json_file in sorted(json_files):
            config_path = os.path.join(self.config_dir, json_file)
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Use filename without extension as tab name
                tab_name = os.path.splitext(json_file)[0]
                self.configs[tab_name] = {"path": config_path, "data": config_data}
                # gesture_key = config_data.get("gesture_key", "")
                # tab_name += f"({gesture_key})" if gesture_key else ""

                self.add_config_tab(tab_name, config_data)
            except Exception as e:
                print(f"Error loading config {json_file}: {e}")

    def update_indicator(self):
        """Update the status indicator based on gesture manager state"""
        manager = get_gesture_manager()
        is_running = manager.detector is not None if manager else False
        is_enabled = self.gesture_settings.get("enabled", True)

        if is_running and is_enabled:
            # Green indicator
            self.status_indicator.setStyleSheet(
                """
                QLabel {
                    background-color: #4CAF50;
                    border-radius: 2px;
                    border: 2px solid #388E3C;
                }
            """
            )
            self.status_indicator.setToolTip("Gesture system is running")
        else:
            # Gray indicator
            self.status_indicator.setStyleSheet(
                """
                QLabel {
                    background-color: #808080;
                    border-radius: 2px;
                    border: 2px solid #555;
                }
            """
            )
            self.status_indicator.setToolTip("Gesture system is not running")

    # ========================================================================
    # Gesture System Settings Dialog
    # ========================================================================
    def open_settings(self):
        """Open settings dialog"""
        from PyQt5.QtWidgets import QCheckBox, QSpinBox, QFormLayout

        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Gesture Settings")
        settings_dialog.resize(500, 300)
        settings_dialog.setStyleSheet(self.styleSheet())  # Apply same dark theme

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Enabled checkbox
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(self.gesture_settings.get("enabled", True))
        form_layout.addRow("Enable Gesture System:", enabled_checkbox)

        # Minimum pixels spinbox
        min_pixels_spinbox = QSpinBox()
        min_pixels_spinbox.setMinimum(1)
        min_pixels_spinbox.setMaximum(200)
        min_pixels_spinbox.setValue(
            self.gesture_settings.get("minimum_pixels_to_move", 20)
        )
        form_layout.addRow("Minimum Pixels to Move:", min_pixels_spinbox)

        # Show preview checkbox
        show_preview_checkbox = QCheckBox()
        show_preview_checkbox.setChecked(
            self.gesture_settings.get("show_preview", True)
        )
        form_layout.addRow("Show Gesture Preview:", show_preview_checkbox)

        # Alias settings
        alias_setting = QTextEdit()
        alias_setting.setPlaceholderText(
            """
Enter alias settings in JSON format
Both "alias_name" and "icon_name" are optional.
Priority is Icon > Alias Name > Original Name.
Example:
    {
    "KisToolSelectOutline": {
        "alias_name": "Free Hand",
        "icon_name": "free_hand.png"
        },
    "invert_selection": {
        "alias_name": "Invert"
        }
    }
        """
        )
        alias_setting.setText(
            json.dumps(self.gesture_settings.get("alias", {}), indent=4)
        )
        alias_setting.setMinimumHeight(300)
        form_layout.addRow("Alias Settings (JSON):", alias_setting)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        settings_dialog.setLayout(layout)

        def save_settings():
            enabled = enabled_checkbox.isChecked()
            show_gesture_preview = show_preview_checkbox.isChecked()
            self.gesture_settings["enabled"] = enabled
            self.gesture_settings["minimum_pixels_to_move"] = min_pixels_spinbox.value()
            self.gesture_settings["show_preview"] = show_gesture_preview
            # Load alias settings from text
            try:
                alias_json = alias_setting.toPlainText()
                alias_dict = json.loads(alias_json)
                self.gesture_settings["alias"] = alias_dict
            except Exception as e:
                print(f"Error parsing alias settings JSON: {e}")
                self.gesture_settings["alias"] = {}
            self.save_gesture_settings()

            # Get current event filter installation state
            manager = get_gesture_manager()
            event_filter_installed = False
            if manager and manager.detector:
                event_filter_installed = manager.detector.event_filter_installed

            # Pause or resume based on enabled state and current installation state
            if not enabled and event_filter_installed:
                # Checkbox is false and filter is installed -> pause
                pause_gesture_event_filter()
            elif enabled and not event_filter_installed:
                # Checkbox is true and filter is not installed -> resume
                resume_gesture_event_filter()

            # Enable or disable gesture preview
            if show_gesture_preview:
                enable_gesture_preview(True)
            else:
                enable_gesture_preview(False)

            self.update_indicator()
            settings_dialog.accept()

        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(settings_dialog.reject)

        settings_dialog.exec_()

    # ========================================================================

    def load_gesture_settings(self):
        """Load gesture system settings"""
        try:
            if os.path.exists(self.gesture_settings_path):
                with open(self.gesture_settings_path, "r", encoding="utf-8") as f:
                    self.gesture_settings = json.load(f)
                    self.gesture_alias = self.gesture_settings.get("alias", {})
            else:
                # Default settings
                self.gesture_settings = {
                    "enabled": True,
                    "minimum_pixels_to_move": 20,
                    "show_preview": True,
                    "alias": {}
                }
                # Create the file with default settings
                with open(self.gesture_settings_path, "w", encoding="utf-8") as f:
                    json.dump(self.gesture_settings, f, indent=4)
                self.gesture_alias = {}
        except Exception as e:
            print(f"Error loading gesture settings: {e}")
            self.gesture_settings = {
                "enabled": True,
                "minimum_pixels_to_move": 20,
                "show_preview": True,
                "alias": {}
            }
            self.gesture_alias = {}

    def save_gesture_settings(self):
        """Save gesture system settings"""
        try:
            with open(self.gesture_settings_path, "w", encoding="utf-8") as f:
                json.dump(self.gesture_settings, f, indent=4)
            gesture_alias = self.gesture_settings.get("alias", {})
            refresh_gesture_setting(gesture_alias)
            write_log("Gesture settings saved and refreshed.")
        except Exception as e:
            print(f"Error saving gesture settings: {e}")

    # ========================================================================

    def add_new_config(self):
        """Add a new empty config file with next available number"""
        # Find the next available number
        existing_numbers = []
        for config_name in self.configs.keys():
            try:
                num = int(config_name)
                existing_numbers.append(num)
            except ValueError:
                pass  # Skip non-numeric config names

        # Get next number
        next_num = 1
        if existing_numbers:
            next_num = max(existing_numbers) + 1

        new_name = str(next_num)
        new_path = os.path.join(self.config_dir, f"{new_name}.json")

        # Create empty config
        empty_config = {}
        self.configs[new_name] = {"path": new_path, "data": empty_config}

        # Add tab
        self.add_config_tab(new_name, empty_config)

        # Switch to the new tab
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def add_config_tab(self, name, config_data):
        """Add a new tab with gesture configuration UI"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout()
        tab_widget.setLayout(tab_layout)

        # Create the 5x5 gesture grid
        gesture_grid = self.create_gesture_grid(name, config_data)
        tab_layout.addLayout(gesture_grid)

        tab_layout.addStretch()

        # Add tab to tab widget
        self.tab_widget.addTab(tab_widget, name)

    def config_gesture_action(self):
        """Open dialog to configure a gesture action"""
        button = self.sender()
        direction = button.property("direction")
        config_name = button.property("config_name")

        # Open arrow config popup
        dialog = ArrowConfigPopup(direction, config_name, self, self)
        if dialog.exec_():
            gesture_config = dialog.get_gesture_config()
            # Update the config data (including None to clear)
            if gesture_config is None:
                # Remove the direction from config to clear it
                if direction in self.configs[config_name]["data"]:
                    del self.configs[config_name]["data"][direction]
            else:
                # Set the gesture config
                self.configs[config_name]["data"][direction] = gesture_config

            # Update the label to show new config
            self.update_gesture_label(config_name, direction)

    def update_gesture_label(self, config_name, direction):
        """Update the label for a specific gesture direction"""
        label_key = f"{config_name}_{direction}"
        if label_key in self.label_widgets:
            label = self.label_widgets[label_key]
            gesture_config = self.configs[config_name]["data"].get(direction, {})

            # Update text
            label_text = self.format_gesture_label(gesture_config)
            label.setText(label_text)

            # If it's a brush preset, try to set the icon
            if gesture_config.get("gesture_type") == "brush":
                brush_name = gesture_config.get("parameters", {}).get("brush_name")
                if brush_name and brush_name in self.preset_dict:
                    preset = self.preset_dict[brush_name]
                    try:
                        preset_image = preset.image()
                        if preset_image:
                            pixmap = QPixmap.fromImage(preset_image).scaled(
                                64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                            label.setPixmap(pixmap)
                            label.setText("")  # Clear text when showing image
                    except:
                        pass  # Keep text label if image fails

    def config_gesture_key(self, config_name, button=None):
        """Open dialog to configure the gesture trigger key and center action"""
        # First, configure the key
        dialog = KeyCaptureDialog(config_name, self)
        if dialog.exec_():
            key = dialog.get_captured_key()
            if key:
                # Save the key to config
                self.configs[config_name]["data"]["gesture_key"] = key
                # Update the button text if button reference is provided
                if button:
                    button.setText(f"Key: {key}")
            elif key is None and dialog.result() == QDialog.Accepted:
                # User cleared the key
                self.configs[config_name]["data"]["gesture_key"] = ""
                if button:
                    button.setText("Config Key")

            # Then, configure the center action (key press action)
            action_dialog = ArrowConfigPopup("center", config_name, self, self)
            if action_dialog.exec_():
                gesture_config = action_dialog.get_gesture_config()
                if gesture_config is None:
                    # Remove the direction from config to clear it
                    if "center" in self.configs[config_name]["data"]:
                        del self.configs[config_name]["data"]["center"]
                else:
                    # Update the config data for center action
                    self.configs[config_name]["data"]["center"] = gesture_config
                # Update the label to show new config
            self.update_gesture_label(config_name, "center")

    def save_and_close(self):
        """Save all configurations and close dialog"""
        for config_name, config_info in self.configs.items():
            try:
                with open(config_info["path"], "w", encoding="utf-8") as f:
                    json.dump(config_info["data"], f, indent=4)
            except Exception as e:
                print(f"Error saving config {config_name}: {e}")

        # Reload gesture configurations after saving
        reload_gesture_configs()
        set_config_dialog_active(False)

        self.accept()

    def reject(self):
        """Handle dialog rejection (Cancel button)"""
        # Notify gesture system that config dialog is no longer active
        set_config_dialog_active(False)
        super().reject()


class KeyCaptureDialog(QDialog):
    """Dialog for capturing a key press for gesture trigger"""

    def __init__(self, config_name, parent=None):
        super().__init__(parent)
        self.config_name = config_name
        self.captured_key = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI elements"""
        self.setWindowTitle("Configure Gesture Key")
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
                font-size: 14px;
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

        # Instructions
        title_label = QLabel(f"Configure gesture key for: {self.config_name}")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        instruction_label = QLabel("Press any key (A-Z, 0-9, F1-F12, etc.)")
        instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label)

        # Display captured key
        self.key_label = QLabel("No key captured")
        self.key_label.setAlignment(Qt.AlignCenter)
        self.key_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4FC3F7;
                padding: 20px;
            }
        """
        )
        layout.addWidget(self.key_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.clear_btn = QPushButton("Clear Key")
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Connect buttons
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.clear_btn.clicked.connect(self.clear_key)

    def keyPressEvent(self, event: QKeyEvent):
        """Capture key press event"""
        # Ignore modifier-only keys
        if event.key() in [Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta]:
            return

        # Get the key text
        key_text = event.text().upper()

        # Handle special keys
        key = event.key()
        if key == Qt.Key_Escape:
            self.reject()
            return
        elif key >= Qt.Key_F1 and key <= Qt.Key_F12:
            key_text = f"F{key - Qt.Key_F1 + 1}"
        elif key == Qt.Key_Space:
            key_text = "SPACE"
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            key_text = "ENTER"
        elif key == Qt.Key_QuoteLeft:
            key_text = "`"
        elif not key_text or not key_text.isalnum():
            # Only accept alphanumeric keys and F-keys
            return

        self.captured_key = key_text
        self.key_label.setText(f"Key: {key_text}")

    def clear_key(self):
        """Clear the captured key"""
        self.captured_key = None
        self.key_label.setText("No key captured")

    def get_captured_key(self):
        """Return the captured key"""
        return self.captured_key
