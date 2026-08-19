import json
import os

from krita import Krita  # type: ignore

from ..compat import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QIcon,
    QKeyEvent,
    QLabel,
    QPixmap,
    QPushButton,
    QSize,
    QSpinBox,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from ..infrastructure import (
    get_gesture_data_dir,
    get_gesture_images_dir,
    get_system_icons_dir,
)
from .arrow_config_popup import ArrowConfigPopup
from .gesture_main import (
    enable_gesture_preview,
    get_gesture_manager,
    pause_gesture_event_filter,
    reload_gesture_configs,
    resume_gesture_event_filter,
    set_config_dialog_active,
)
from .log_utils import write_log


class GestureConfigDialog(QDialog):
    """Dialog for configuring gesture shortcuts"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.setWindowTitle("Gesture Configuration")
        self.resize(600, 500)

        gesture_data_dir = get_gesture_data_dir()
        self.config_dir = os.path.join(gesture_data_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
        self.image_dir = get_gesture_images_dir()
        self.configs = {}
        self.label_widgets = {}
        self.gesture_settings_path = os.path.join(gesture_data_dir, "gesture.json")

        try:
            self.preset_dict = Krita.instance().resources("preset")
        except Exception:
            self.preset_dict = {}

        self.setup_ui()
        self.load_configs()
        self.load_gesture_settings()
        self.update_indicator()

        set_config_dialog_active(True)

    # ========================================================================
    # UI Setup and Loading/Saving Configs
    # ========================================================================
    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.setStyleSheet("""
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
        """)

        top_layout = QHBoxLayout()
        self.tab_widget = QTabWidget()
        top_layout.addStretch()

        icon_dir = get_system_icons_dir()

        self.plus_btn = QPushButton()
        self.plus_btn.setIcon(QIcon(os.path.join(icon_dir, "add.png")))
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

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(os.path.join(icon_dir, "setting.png")))
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

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)
        self.status_indicator.setStyleSheet("""
            QLabel {
                background-color: #808080;
                border-radius: 2px;
                border: 2px solid #555;
            }
        """)
        self.status_indicator.setToolTip("Gesture system status")
        top_layout.addWidget(self.status_indicator)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.tab_widget)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    # ========================================================================
    # Gesture Grid Creation and Handlers
    # ========================================================================
    def create_gesture_grid(self, config_name, config_data):
        """Create the gesture arrow/label grid for one config tab"""
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setAlignment(Qt.AlignCenter)

        direction_map = {
            (0, 0): "left_up",
            (0, 1): "up",
            (0, 2): "right_up",
            (1, 0): "left",
            (1, 1): "center",
            (1, 2): "right",
            (2, 0): "left_down",
            (2, 1): "down",
            (2, 2): "right_down",
        }

        for (row, col), direction in direction_map.items():
            if direction == "center":
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

                gesture_config = config_data.get("center", {})
                center_label = QLabel(self.format_gesture_label(gesture_config))
                center_label.setAlignment(Qt.AlignCenter)
                center_label.setWordWrap(True)
                center_label.setFixedSize(100, 60)
                center_label.setProperty("direction", "center")
                center_label.setProperty("config_name", config_name)
                self.apply_brush_preview(center_label, gesture_config)

                label_key = f"{config_name}_center"
                self.label_widgets[label_key] = center_label

                center_widget = QWidget()
                center_layout = QVBoxLayout()
                center_layout.setSpacing(5)
                center_layout.addWidget(key_button, alignment=Qt.AlignCenter)
                center_layout.addWidget(center_label, alignment=Qt.AlignCenter)
                center_widget.setLayout(center_layout)

                grid_layout.addWidget(center_widget, 2, 2, Qt.AlignCenter)
            else:
                arrow_btn = QPushButton()
                icon_path = os.path.join(self.image_dir, f"{direction}.png")
                if os.path.exists(icon_path):
                    arrow_btn.setIcon(QIcon(icon_path))
                    arrow_btn.setIconSize(QSize(64, 64))
                else:
                    arrow_btn.setText(direction)

                arrow_btn.setFixedSize(64, 64)
                arrow_btn.setProperty("direction", direction)
                arrow_btn.setProperty("config_name", config_name)
                arrow_btn.clicked.connect(self.config_gesture_action)

                gesture_config = config_data.get(direction, {})
                config_label = QLabel(self.format_gesture_label(gesture_config))
                config_label.setAlignment(Qt.AlignCenter)
                config_label.setWordWrap(True)
                config_label.setMinimumSize(100, 100)
                config_label.setMaximumHeight(100)
                config_label.setProperty("direction", direction)
                config_label.setProperty("config_name", config_name)
                self.apply_brush_preview(config_label, gesture_config)

                label_key = f"{config_name}_{direction}"
                self.label_widgets[label_key] = config_label

                label_col = col * 2
                arrow_col = col + 1

                if row == 0:
                    grid_layout.addWidget(config_label, 0, label_col, Qt.AlignCenter)
                    grid_layout.addWidget(arrow_btn, 1, arrow_col, Qt.AlignCenter)
                elif row == 1:
                    if col == 0:
                        grid_layout.addWidget(config_label, 2, 0, Qt.AlignCenter)
                        grid_layout.addWidget(arrow_btn, 2, 1, Qt.AlignCenter)
                    else:
                        grid_layout.addWidget(arrow_btn, 2, 3, Qt.AlignCenter)
                        grid_layout.addWidget(config_label, 2, 4, Qt.AlignCenter)
                else:
                    grid_layout.addWidget(arrow_btn, 3, arrow_col, Qt.AlignCenter)
                    grid_layout.addWidget(config_label, 4, label_col, Qt.AlignCenter)

        return grid_layout

    def apply_brush_preview(self, label, gesture_config):
        """Show the brush preset thumbnail on a label, if configured."""
        if gesture_config.get("gesture_type") != "brush":
            return
        brush_name = gesture_config.get("parameters", {}).get("brush_name")
        if not brush_name or brush_name not in self.preset_dict:
            return
        try:
            preset = self.preset_dict[brush_name]
            preset_image = preset.image()
            if preset_image:
                pixmap = QPixmap.fromImage(preset_image).scaled(
                    64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                label.setPixmap(pixmap)
                label.setText("")
        except Exception:
            pass

    def format_gesture_label(self, gesture_config):
        if not gesture_config:
            return "[Empty]"

        gesture_type = gesture_config.get("gesture_type", "unknown")
        parameters = gesture_config.get("parameters", {})

        if gesture_type == "action":
            return f"Action:\n{parameters.get('action_id', 'N/A')}"
        if gesture_type == "brush":
            return f"Brush:\n{parameters.get('brush_name', 'N/A')}"
        if gesture_type == "docker_toggle":
            return f"Docker:\n{parameters.get('docker_name', 'N/A')}"
        return f"{gesture_type}"

    # ========================================================================
    def load_configs(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            return

        json_files = [
            f
            for f in os.listdir(self.config_dir)
            if f.endswith(".json") and f != "gesture.json"
        ]

        if not json_files:
            self.add_config_tab("1", {})
            return

        for json_file in sorted(json_files):
            config_path = os.path.join(self.config_dir, json_file)
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                tab_name = os.path.splitext(json_file)[0]
                self.configs[tab_name] = {"path": config_path, "data": config_data}
                self.add_config_tab(tab_name, config_data)
            except Exception as e:
                print(f"Error loading config {json_file}: {e}")

    def update_indicator(self):
        manager = get_gesture_manager()
        is_running = manager.detector is not None if manager else False
        is_enabled = self.gesture_settings.get("enabled", True)

        if is_running and is_enabled:
            self.status_indicator.setStyleSheet(
                "QLabel { background-color: #4CAF50; border-radius: 2px; border: 2px solid #388E3C; }"
            )
            self.status_indicator.setToolTip("Gesture system is running")
        else:
            self.status_indicator.setStyleSheet(
                "QLabel { background-color: #808080; border-radius: 2px; border: 2px solid #555; }"
            )
            self.status_indicator.setToolTip("Gesture system is not running")

    # ========================================================================
    # Gesture System Settings Dialog
    # ========================================================================
    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Gesture Settings")
        settings_dialog.resize(500, 300)
        settings_dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(self.gesture_settings.get("enabled", True))
        form_layout.addRow("Enable Gesture System:", enabled_checkbox)

        min_pixels_spinbox = QSpinBox()
        min_pixels_spinbox.setMinimum(1)
        min_pixels_spinbox.setMaximum(200)
        min_pixels_spinbox.setValue(
            self.gesture_settings.get("minimum_pixels_to_move", 20)
        )
        form_layout.addRow("Minimum Pixels to Move:", min_pixels_spinbox)

        show_preview_checkbox = QCheckBox()
        show_preview_checkbox.setChecked(
            self.gesture_settings.get("show_preview", True)
        )
        form_layout.addRow("Show Gesture Preview:", show_preview_checkbox)

        alias_note = QLabel(
            "Custom name / color / icon for actions and dockers are now set in\n"
            "the shared Alias Config dialog (docker header button)."
        )
        form_layout.addRow(alias_note)

        layout.addLayout(form_layout)

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
            self.save_gesture_settings()

            manager = get_gesture_manager()
            event_filter_installed = bool(
                manager and manager.detector and manager.detector.event_filter_installed
            )

            if not enabled and event_filter_installed:
                pause_gesture_event_filter()
            elif enabled and not event_filter_installed:
                resume_gesture_event_filter()

            enable_gesture_preview(show_gesture_preview)

            self.update_indicator()
            settings_dialog.accept()

        ok_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(settings_dialog.reject)

        settings_dialog.exec()

    # ========================================================================
    def load_gesture_settings(self):
        default_settings = {
            "enabled": True,
            "minimum_pixels_to_move": 20,
            "show_preview": True,
        }
        try:
            if os.path.exists(self.gesture_settings_path):
                with open(self.gesture_settings_path, "r", encoding="utf-8") as f:
                    self.gesture_settings = json.load(f)
            else:
                self.gesture_settings = dict(default_settings)
                with open(self.gesture_settings_path, "w", encoding="utf-8") as f:
                    json.dump(self.gesture_settings, f, indent=4)
        except Exception as e:
            print(f"Error loading gesture settings: {e}")
            self.gesture_settings = dict(default_settings)

    def save_gesture_settings(self):
        try:
            with open(self.gesture_settings_path, "w", encoding="utf-8") as f:
                json.dump(self.gesture_settings, f, indent=4)
            write_log("Gesture settings saved.")
        except Exception as e:
            print(f"Error saving gesture settings: {e}")

    # ========================================================================
    def add_new_config(self):
        existing_numbers = []
        for config_name in self.configs.keys():
            try:
                existing_numbers.append(int(config_name))
            except ValueError:
                pass

        next_num = max(existing_numbers) + 1 if existing_numbers else 1
        new_name = str(next_num)
        new_path = os.path.join(self.config_dir, f"{new_name}.json")

        empty_config = {}
        self.configs[new_name] = {"path": new_path, "data": empty_config}
        self.add_config_tab(new_name, empty_config)
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def add_config_tab(self, name, config_data):
        tab_widget = QWidget()
        tab_layout = QVBoxLayout()
        tab_widget.setLayout(tab_layout)

        tab_layout.addLayout(self.create_gesture_grid(name, config_data))
        tab_layout.addStretch()

        self.tab_widget.addTab(tab_widget, name)

    def config_gesture_action(self):
        button = self.sender()
        direction = button.property("direction")
        config_name = button.property("config_name")

        dialog = ArrowConfigPopup(direction, config_name, self, self)
        if dialog.exec():
            gesture_config = dialog.get_gesture_config()
            if gesture_config is None:
                self.configs[config_name]["data"].pop(direction, None)
            else:
                self.configs[config_name]["data"][direction] = gesture_config

            self.update_gesture_label(config_name, direction)

    def update_gesture_label(self, config_name, direction):
        label_key = f"{config_name}_{direction}"
        if label_key not in self.label_widgets:
            return

        label = self.label_widgets[label_key]
        gesture_config = self.configs[config_name]["data"].get(direction, {})
        label.setText(self.format_gesture_label(gesture_config))
        self.apply_brush_preview(label, gesture_config)

    def config_gesture_key(self, config_name, button=None):
        dialog = KeyCaptureDialog(config_name, self)
        if dialog.exec():
            key = dialog.get_captured_key()
            if key:
                self.configs[config_name]["data"]["gesture_key"] = key
                if button:
                    button.setText(f"Key: {key}")
            elif key is None and dialog.result() == QDialog.Accepted:
                self.configs[config_name]["data"]["gesture_key"] = ""
                if button:
                    button.setText("Config Key")

            action_dialog = ArrowConfigPopup("center", config_name, self, self)
            if action_dialog.exec():
                gesture_config = action_dialog.get_gesture_config()
                if gesture_config is None:
                    self.configs[config_name]["data"].pop("center", None)
                else:
                    self.configs[config_name]["data"]["center"] = gesture_config
            self.update_gesture_label(config_name, "center")

    def save_and_close(self):
        for config_name, config_info in self.configs.items():
            try:
                with open(config_info["path"], "w", encoding="utf-8") as f:
                    json.dump(config_info["data"], f, indent=4)
            except Exception as e:
                print(f"Error saving config {config_name}: {e}")

        reload_gesture_configs()
        set_config_dialog_active(False)
        self.accept()

    def reject(self):
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
        self.setWindowTitle("Configure Gesture Key")
        self.resize(400, 200)
        layout = QVBoxLayout()

        self.setStyleSheet("""
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
        """)

        title_label = QLabel(f"Configure gesture key for: {self.config_name}")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        instruction_label = QLabel("Press any key (A-Z, 0-9, F1-F12, etc.)")
        instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label)

        self.key_label = QLabel("No key captured")
        self.key_label.setAlignment(Qt.AlignCenter)
        self.key_label.setStyleSheet(
            "QLabel { font-size: 24px; font-weight: bold; color: #4FC3F7; padding: 20px; }"
        )
        layout.addWidget(self.key_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.clear_btn = QPushButton("Clear Key")
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.clear_btn.clicked.connect(self.clear_key)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
            return

        key_text = event.text().upper()
        key = event.key()
        if key == Qt.Key_Escape:
            self.reject()
            return
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            key_text = f"F{key - Qt.Key_F1 + 1}"
        elif key == Qt.Key_Space:
            key_text = "SPACE"
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            key_text = "ENTER"
        elif key == Qt.Key_QuoteLeft:
            key_text = "`"
        elif not key_text or not key_text.isalnum():
            return

        self.captured_key = key_text
        self.key_label.setText(f"Key: {key_text}")

    def clear_key(self):
        self.captured_key = None
        self.key_label.setText("No key captured")

    def get_captured_key(self):
        return self.captured_key
