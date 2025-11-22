from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
    QDockWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase  # type: ignore
import json
import os

# Import widgets from the widgets2 package
from .widgets2 import (
    ColorHistoryWidget,
    CircularRotationWidget,
    BrushHistoryWidget,
    BRUSH_ADJUSTMENT_FONT_SIZE,
    BRUSH_ADJUSTMENT_NUMBER_SIZE,
    COLOR_HISTORY_NUMBER,
    BRUSH_HISTORY_NUMBER,
    COLOR_HISTORY_ICON_SIZE,
    BRUSH_HISTORY_ICON_SIZE,
    BLENDE_MODES,
)


class BrushAdjustmentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None  # Add opacity tracking
        self.current_brush_rotation = None
        self.current_blend_mode = None  # Add blend mode tracking
        self.updating_from_brush = False  # Flag to prevent recursive updates

        # Load docker buttons configuration
        self.docker_buttons_config = self.load_docker_buttons_config()

        self.init_ui()

        # Timer to periodically check for brush changes
        self.brush_check_timer = QTimer()
        self.brush_check_timer.timeout.connect(self.check_brush_change)
        self.brush_check_timer.start(200)  # Check every 200ms for more responsiveness

    def load_docker_buttons_config(self):
        """Load docker buttons configuration from JSON file"""
        try:
            # Get the directory where this file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(current_dir, "config")
            config_file = os.path.join(config_dir, "docker_buttons.json")

            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)
                    print(
                        f"Loaded docker buttons config: {len(config.get('docker_buttons', []))} buttons"
                    )
                    return config
            else:
                print(f"Docker buttons config file not found: {config_file}")
                print("Creating default config file...")

                # Create the config directory if it doesn't exist
                os.makedirs(config_dir, exist_ok=True)

                # Get default configuration
                default_config = self.get_default_docker_config()

                # Write default config to file
                with open(config_file, "w") as f:
                    json.dump(default_config, f, indent=4)

                print(f"Created default docker buttons config file: {config_file}")
                return default_config

        except Exception as e:
            print(f"Error loading docker buttons config: {e}")
            return self.get_default_docker_config()

    def get_default_docker_config(self):
        """Return default docker configuration if JSON file is not available"""
        return {
            "docker_buttons": [
                {
                    "button_name": "Tool",
                    "button_width": 40,
                    "button_icon": "",
                    "docker_keywords": ["tool", "option"],
                    "description": "Tool Options Docker",
                },
                {
                    "button_name": "Layers",
                    "button_width": 50,
                    "button_icon": "",
                    "docker_keywords": ["layer"],
                    "description": "Layers Docker",
                },
                {
                    "button_name": "Brush",
                    "button_width": 50,
                    "button_icon": "",
                    "docker_keywords": ["brush", "preset"],
                    "description": "Brush Presets Docker",
                },
            ]
        }

    def create_docker_buttons(self, layout):
        """Dynamically create docker toggle buttons based on configuration"""
        docker_buttons = self.docker_buttons_config.get("docker_buttons", [])
        if not docker_buttons:
            return

        print(f"Creating {len(docker_buttons)} docker buttons")

        for button_config in docker_buttons:
            button_icon = button_config.get("button_icon", "")

            # Check if button_icon is empty
            if not button_icon:
                # Create button with text
                button = QPushButton(button_config["button_name"])
                button.setStyleSheet(
                    f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE}; padding: 2px 8px;"
                )
                button.setFixedWidth(button_config["button_width"])
            else:
                # Create button with icon
                button = QPushButton()
                icon_path = os.path.join(
                    os.path.dirname(__file__), "config", "icon", button_icon
                )

                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    button.setIcon(icon)
                    button.setFixedSize(24, 24)
                else:
                    # Fallback to text if icon not found
                    print(f"Icon not found: {icon_path}, using text instead")
                    button.setText(button_config["button_name"])
                    button.setStyleSheet(
                        f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE}; padding: 2px 8px;"
                    )
                    button.setFixedWidth(button_config["button_width"])

            button.setToolTip(button_config["description"])

            # Create a closure to capture the button configuration
            def make_docker_toggle_handler(config):
                def toggle_docker():
                    self.toggle_docker_by_keywords(
                        config["docker_keywords"], config["description"]
                    )

                return toggle_docker

            button.clicked.connect(make_docker_toggle_handler(button_config))
            layout.addWidget(button)

    def toggle_docker_by_keywords(self, keywords, description):
        """Generic function to toggle any docker based on keywords"""
        print(f"Toggling {description}")

        app = Krita.instance()
        try:
            window = app.activeWindow()
            if window:
                dockers = window.dockers()
                for docker in dockers:
                    docker_title = docker.windowTitle().lower()

                    # Check if all keywords are present in the docker title
                    if all(keyword.lower() in docker_title for keyword in keywords):
                        if docker.isVisible():
                            docker.hide()
                            print(f"Hid {description}: {docker.windowTitle()}")
                        else:
                            docker.show()
                            docker.raise_()
                            print(f"Showed {description}: {docker.windowTitle()}")
                        return

            print(f"Could not find {description}")

        except Exception as e:
            print(f"Error toggling {description}: {e}")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)

        # Create main horizontal layout: [Size/Opacity rows] | [Rotation widget]
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)

        # Left side: Size and Opacity controls in vertical layout
        left_layout = QVBoxLayout()
        left_layout.setSpacing(6)

        # Size row: Label | Slider | Value
        size_layout = QHBoxLayout()
        size_layout.setSpacing(6)

        size_label = QLabel("Size:")
        size_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};")
        size_label.setFixedWidth(50)
        size_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setMinimum(0)
        self.size_slider.setMaximum(100)  # Use 0-100 range for internal scaling
        self.size_slider.setValue(self.brush_size_to_slider(10))
        self.size_slider.valueChanged.connect(self.on_size_slider_changed)

        self.size_value_label = QLabel("10")
        self.size_value_label.setStyleSheet(
            f"font-size: {BRUSH_ADJUSTMENT_NUMBER_SIZE};"
        )
        self.size_value_label.setAlignment(Qt.AlignCenter)
        self.size_value_label.setFixedWidth(35)

        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_slider, 1)
        size_layout.addWidget(self.size_value_label)

        # Opacity row: Label | Slider | Value
        opacity_layout = QHBoxLayout()
        opacity_layout.setSpacing(6)

        opacity_label = QLabel("Opacity:")
        opacity_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};")
        opacity_label.setFixedWidth(50)
        opacity_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)

        self.opacity_value_label = QLabel("100%")
        self.opacity_value_label.setStyleSheet(
            f"font-size: {BRUSH_ADJUSTMENT_NUMBER_SIZE};"
        )
        self.opacity_value_label.setAlignment(Qt.AlignCenter)
        self.opacity_value_label.setFixedWidth(35)

        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider, 1)
        opacity_layout.addWidget(self.opacity_value_label)

        # Add size and opacity to left layout
        left_layout.addLayout(size_layout)
        left_layout.addLayout(opacity_layout)

        # Blending Mode row: Label | Dropdown
        blend_layout = QHBoxLayout()
        blend_layout.setSpacing(6)

        blend_label = QLabel("Blend:")
        blend_label.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};")
        blend_label.setFixedWidth(50)
        blend_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.blend_combo = QComboBox()
        self.blend_combo.setStyleSheet(f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};")
        # Add common blending modes
        blend_modes = BLENDE_MODES
        for mode in blend_modes:
            self.blend_combo.addItem(mode.replace("_", " ").title(), mode)

        self.blend_combo.currentTextChanged.connect(self.on_blend_mode_changed)

        blend_layout.addWidget(blend_label)
        blend_layout.addWidget(self.blend_combo, 1)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setStyleSheet(
            f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE}; padding: 2px 8px;"
        )
        reset_btn.clicked.connect(self.reset_brush_settings)
        reset_btn.setFixedWidth(50)

        blend_layout.addWidget(reset_btn)
        left_layout.addLayout(blend_layout)

        # Right side: Rotation widget and value
        right_layout = QHBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setAlignment(Qt.AlignCenter)

        self.rotation_widget = CircularRotationWidget()
        self.rotation_widget.setValue(0)
        self.rotation_widget.valueChanged.connect(self.on_rotation_changed)

        self.rotation_value_label = QLabel("0°")
        self.rotation_value_label.setStyleSheet(
            f"font-size: {BRUSH_ADJUSTMENT_NUMBER_SIZE};"
        )
        self.rotation_value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.rotation_value_label.setFixedWidth(35)  # Smaller width for side placement

        right_layout.addWidget(self.rotation_widget)
        right_layout.addWidget(self.rotation_value_label)

        # Add left and right layouts to main layout
        main_layout.addLayout(left_layout, 1)  # Give left side more space
        main_layout.addLayout(right_layout)

        # Add main layout to the widget
        layout.addLayout(main_layout)

        # Add color history widget below the main controls
        self.color_history_widget = ColorHistoryWidget(
            self, COLOR_HISTORY_NUMBER, COLOR_HISTORY_ICON_SIZE
        )
        layout.addWidget(self.color_history_widget)

        # Add brush history widget below the color history
        self.brush_history_widget = BrushHistoryWidget(
            self, BRUSH_HISTORY_NUMBER, BRUSH_HISTORY_ICON_SIZE
        )
        layout.addWidget(self.brush_history_widget)

        # Add dynamic docker buttons below the brush history widget
        docker_buttons_layout = QHBoxLayout()
        docker_buttons_layout.setSpacing(4)
        docker_buttons_layout.setContentsMargins(0, 5, 0, 0)
        docker_buttons_layout.setAlignment(Qt.AlignLeft)  # Align buttons to the left
        self.create_docker_buttons(docker_buttons_layout)
        layout.addLayout(docker_buttons_layout)

        self.setLayout(layout)

        # Load current brush settings
        self.update_from_current_brush()

    def brush_size_to_slider(self, size):
        """Convert brush size (1-1000) to slider value (0-100) with non-linear scaling"""
        if size <= 50:
            # Linear mapping for 1-50: maps to slider 0-70 (70% of slider range)
            return int((size - 1) * 70 / 49)
        else:
            # Linear mapping for 51-1000: maps to slider 71-100 (30% of slider range)
            return int(70 + (size - 50) * 30 / 950)

    def slider_to_brush_size(self, slider_value):
        """Convert slider value (0-100) to brush size (1-1000) with non-linear scaling"""
        if slider_value <= 70:
            # Map slider 0-70 to brush size 1-50
            return int(1 + slider_value * 49 / 70)
        else:
            # Map slider 71-100 to brush size 51-1000
            return int(50 + (slider_value - 70) * 950 / 30)

    def on_size_slider_changed(self, slider_value):
        """Handle size slider change with non-linear conversion"""
        brush_size = self.slider_to_brush_size(slider_value)
        self.on_size_changed(brush_size)

    def check_brush_change(self):
        """Check if the current brush has changed and update sliders if needed"""
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                current_preset = view.currentBrushPreset()
                if current_preset:
                    brush_name = current_preset.name()

                    # Get current brush properties
                    current_size = None
                    current_opacity = None
                    current_rotation = None
                    current_blend_mode = None

                    try:
                        current_size = view.brushSize()
                    except:
                        pass

                    try:
                        current_opacity = view.paintingOpacity()
                    except:
                        pass

                    try:
                        current_rotation = view.brushRotation()
                    except:
                        pass

                    try:
                        current_blend_mode = view.currentBlendingMode()
                    except:
                        pass

                    # Check if brush name changed OR if properties changed (for reload preset action)
                    brush_changed = brush_name != self.current_brush_name
                    size_changed = current_size != self.current_brush_size
                    opacity_changed = current_opacity != self.current_brush_opacity
                    rotation_changed = current_rotation != self.current_brush_rotation
                    blend_changed = current_blend_mode != self.current_blend_mode

                    if (
                        brush_changed
                        or size_changed
                        or opacity_changed
                        or rotation_changed
                        or blend_changed
                    ):
                        self.current_brush_name = brush_name
                        self.current_brush_size = current_size
                        self.current_brush_opacity = current_opacity
                        self.current_brush_rotation = current_rotation
                        self.current_blend_mode = current_blend_mode
                        self.update_from_current_brush()
            except:
                pass

    def update_from_current_brush(self):
        """Update sliders to match current brush settings"""
        if self.updating_from_brush:
            return

        self.updating_from_brush = True

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()

            # Get current brush size directly from the view
            try:
                size = view.brushSize()
                self.size_slider.setValue(self.brush_size_to_slider(int(size)))
                self.size_value_label.setText(str(int(size)))
                self.current_brush_size = size
            except:
                # Fallback to default if brushSize() doesn't work
                self.size_slider.setValue(self.brush_size_to_slider(10))
                self.size_value_label.setText("10")
                self.current_brush_size = 10

            # Get current opacity
            try:
                opacity = view.paintingOpacity()
                opacity_percent = int(opacity * 100)  # Convert from 0-1 to 0-100
                self.opacity_slider.setValue(opacity_percent)
                self.opacity_value_label.setText(f"{opacity_percent}%")
                self.current_brush_opacity = opacity
            except:
                # Fallback if opacity method doesn't work
                self.opacity_slider.setValue(100)
                self.opacity_value_label.setText("100%")
                self.current_brush_opacity = 1.0

            # Get brush rotation - this might need different approach
            try:
                rotation = view.brushRotation()
                self.rotation_widget.setValue(int(rotation))
                self.rotation_value_label.setText(f"{int(rotation)}°")
                self.current_brush_rotation = rotation
            except:
                # Fallback if rotation method doesn't exist
                self.rotation_widget.setValue(0)
                self.rotation_value_label.setText("0°")
                self.current_brush_rotation = 0

            # Get current blend mode
            try:
                blend_mode = view.currentBlendingMode()
                if blend_mode:
                    # Find the blend mode in the combo box
                    index = self.blend_combo.findData(blend_mode)
                    if index >= 0:
                        self.blend_combo.setCurrentIndex(index)
                    else:
                        # If not found, add it to the combo
                        self.blend_combo.addItem(
                            blend_mode.replace("_", " ").title(), blend_mode
                        )
                        self.blend_combo.setCurrentIndex(self.blend_combo.count() - 1)
                    self.current_blend_mode = blend_mode
            except:
                # Fallback if blend mode method doesn't exist
                self.blend_combo.setCurrentIndex(0)  # Set to "Normal"
                self.current_blend_mode = "normal"

        self.updating_from_brush = False

    def on_size_changed(self, value):
        """Handle brush size change"""
        if self.updating_from_brush:
            return

        self.size_value_label.setText(str(value))
        self.current_brush_size = value  # Update tracked value

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Set brush size directly on the view
                view.setBrushSize(float(value))
            except Exception as e:
                print(f"Error setting brush size: {e}")

    def on_opacity_changed(self, value):
        """Handle brush opacity change"""
        if self.updating_from_brush:
            return

        self.opacity_value_label.setText(f"{value}%")
        opacity_float = value / 100.0  # Convert from 0-100 to 0-1
        self.current_brush_opacity = opacity_float  # Update tracked value

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Set opacity directly on the view
                view.setPaintingOpacity(opacity_float)
            except Exception as e:
                print(f"Error setting brush opacity: {e}")

    def on_rotation_changed(self, value):
        """Handle brush rotation change"""
        if self.updating_from_brush:
            return

        self.rotation_value_label.setText(f"{value}°")
        self.current_brush_rotation = value  # Update tracked value

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Set brush rotation directly on the view
                view.setBrushRotation(float(value))
            except Exception as e:
                print(f"Error setting brush rotation: {e}")

    def on_blend_mode_changed(self, text):
        """Handle blend mode change"""
        if self.updating_from_brush:
            return

        # Get the blend mode data from the combo box
        blend_mode = self.blend_combo.currentData()
        if blend_mode:
            self.current_blend_mode = blend_mode  # Update tracked value

            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                try:
                    # Set blend mode directly on the view
                    view.setCurrentBlendingMode(blend_mode)
                    print(f"Set blend mode to: {blend_mode}")
                except Exception as e:
                    print(f"Error setting blend mode: {e}")

    def reset_brush_settings(self):
        """Reset brush settings by triggering Krita's reload preset action"""
        print("Triggering Krita's reload preset action")

        app = Krita.instance()
        try:
            # Trigger Krita's built-in reload preset action
            app.action("reload_preset_action").trigger()
            print("Successfully triggered reload_preset_action")

            # Clear tracked values to force UI refresh after reload
            self.current_brush_name = None
            self.current_brush_size = None
            self.current_brush_opacity = None
            self.current_brush_rotation = None
            self.current_blend_mode = None

            # Update UI after a short delay to let Krita finish the reload
            QTimer.singleShot(150, self.update_from_current_brush)

        except Exception as e:
            print(f"Error triggering reload_preset_action: {e}")
            # Fallback - just refresh the UI
            self.update_from_current_brush()

    def force_update(self):
        """Force update from current brush - can be called externally"""
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None
        self.current_brush_rotation = None
        self.current_blend_mode = None
        self.update_from_current_brush()
        # Also force color history update
        if hasattr(self, "color_history_widget"):
            self.color_history_widget.force_color_update()
        # Also force brush history update
        if hasattr(self, "brush_history_widget"):
            self.brush_history_widget.force_brush_update()
            # Add a test brush to verify functionality
            self.brush_history_widget.add_test_brush()

    def refresh_styles(self):
        """Refresh styles when settings change"""
        style = f"font-size: {BRUSH_ADJUSTMENT_FONT_SIZE};"
        for label in self.findChildren(QLabel):
            if label.text() not in ["Brush Adjustments"]:  # Skip title
                label.setStyleSheet(style)

    def closeEvent(self, event):
        """Clean up timers when widget is closed"""
        if hasattr(self, "brush_check_timer"):
            self.brush_check_timer.stop()
        if hasattr(self, "color_history_widget"):
            self.color_history_widget.closeEvent(event)
        if hasattr(self, "brush_history_widget"):
            self.brush_history_widget.closeEvent(event)
        super().closeEvent(event)


class BrushAdjustDockerFactory(DockWidgetFactoryBase):
    """Factory for creating the Brush Adjustments Docker"""

    def __init__(self):
        super().__init__("brush_adjust_docker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        """Create and return the brush adjustments dock widget"""
        return BrushAdjustDockerWidget()


class BrushAdjustDockerWidget(QDockWidget):
    """Docker widget for brush adjustments"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Brush Adjustments")
        self.setObjectName("QuickBrushAdjustmentsDocker")

        # Create the brush adjustment widget
        self.brush_adjustment_section = BrushAdjustmentWidget(self)
        self.setWidget(self.brush_adjustment_section)

        # Set minimum size to ensure usability
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)

    def refresh_styles(self):
        """Refresh styles when settings change"""
        if hasattr(self, "brush_adjustment_section"):
            self.brush_adjustment_section.refresh_styles()

    def force_update_brush(self):
        """Force update brush settings - can be called externally"""
        if hasattr(self, "brush_adjustment_section"):
            self.brush_adjustment_section.force_update()
