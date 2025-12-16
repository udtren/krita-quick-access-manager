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
    StatusBarWidget,
)

# Import configuration loader
from .config.quick_adjust_docker_loader import (
    get_brush_section,
    get_layer_section,
    get_brush_history_section,
    get_color_history_section,
    get_blender_mode_list,
    get_status_bar_section,
    get_docker_toggle_section,
    get_font_size,
    get_number_size,
    get_color_history_total,
    get_color_history_icon_size,
    get_brush_history_total,
    get_brush_history_icon_size,
)


class BrushAdjustmentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None  # Add opacity tracking
        self.current_brush_rotation = None
        self.current_layer_opacity = None  # Add layer opacity tracking
        self.current_blend_mode = None  # Add blend mode tracking
        self.current_layer_blend_mode = None  # Add layer blend mode tracking
        self.updating_from_brush = False  # Flag to prevent recursive updates
        self.updating_from_layer = False

        # Load docker buttons configuration
        self.docker_buttons_config = self.load_docker_buttons_config()

        # Load quick adjust docker configuration
        self.brush_config = get_brush_section()
        self.layer_config = get_layer_section()
        self.brush_history_config = get_brush_history_section()
        self.color_history_config = get_color_history_section()
        self.status_bar_config = get_status_bar_section()
        self.docker_toggle_config = get_docker_toggle_section()
        self.blender_modes = get_blender_mode_list()

        self.init_ui()

        # Timer to periodically check for brush changes
        self.brush_check_timer = QTimer()
        self.brush_check_timer.timeout.connect(self.check_brush_change)
        self.brush_check_timer.start(200)  # Check every 200ms for more responsiveness

        self.layer_check_timer = QTimer()
        self.layer_check_timer.timeout.connect(self.check_layer_change)
        self.layer_check_timer.start(200)

        # ==========================================
        # Add debounce timers for sliders
        # ==========================================
        self.opacity_debounce_timer = QTimer()
        self.opacity_debounce_timer.setSingleShot(True)
        self.opacity_debounce_timer.timeout.connect(self.apply_opacity_change)

        self.size_debounce_timer = QTimer()
        self.size_debounce_timer.setSingleShot(True)
        self.size_debounce_timer.timeout.connect(self.apply_size_change)

        self.layer_opacity_debounce_timer = QTimer()
        self.layer_opacity_debounce_timer.setSingleShot(True)
        self.layer_opacity_debounce_timer.timeout.connect(
            self.apply_layer_opacity_change
        )

        # Store pending values
        self.pending_opacity_value = None
        self.pending_size_value = None
        self.pending_layer_opacity_value = None
        # ==========================================

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
                button.setStyleSheet(f"font-size: {get_font_size()}; padding: 2px 8px;")
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
                        f"font-size: {get_font_size()}; padding: 2px 8px;"
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

        # ============================================
        # Size row: Slider | Value (conditionally created)
        # ============================================
        size_config = self.brush_config.get("size_slider", {})
        if size_config.get("enabled", True):
            size_layout = QHBoxLayout()
            size_layout.setSpacing(6)

            self.size_slider = QSlider(Qt.Horizontal)
            self.size_slider.setMinimum(0)
            self.size_slider.setMaximum(100)  # Use 0-100 range for internal scaling
            self.size_slider.setValue(self.brush_size_to_slider(10))
            self.size_slider.valueChanged.connect(self.on_size_slider_changed_debounced)

            number_size = size_config.get("number_size", get_number_size())
            self.size_value_label = QLabel("10")
            self.size_value_label.setStyleSheet(f"font-size: {number_size};")
            self.size_value_label.setAlignment(Qt.AlignCenter)
            self.size_value_label.setFixedWidth(35)

            size_layout.addWidget(self.size_slider, 1)
            size_layout.addWidget(self.size_value_label)
        else:
            self.size_slider = None
            self.size_value_label = None

        # ============================================
        # Brush Section: Opacity Slider, Blend Mode (conditionally created)
        # ============================================
        brush_and_layer_layout = QHBoxLayout()
        brush_section_layout = QVBoxLayout()

        opacity_config = self.brush_config.get("opacity_slider", {})
        if opacity_config.get("enabled", True):
            brush_opacity_layout = QHBoxLayout()

            self.opacity_slider = QSlider(Qt.Horizontal)
            self.opacity_slider.setMinimum(0)
            self.opacity_slider.setMaximum(100)
            self.opacity_slider.setValue(100)
            self.opacity_slider.valueChanged.connect(self.on_opacity_changed_debounced)

            number_size = opacity_config.get("number_size", get_number_size())
            self.opacity_value_label = QLabel("100%")
            self.opacity_value_label.setStyleSheet(f"font-size: {number_size};")
            self.opacity_value_label.setAlignment(Qt.AlignCenter)
            self.opacity_value_label.setFixedWidth(35)

            brush_opacity_layout.addWidget(self.opacity_slider, 1)
            brush_opacity_layout.addWidget(self.opacity_value_label)
        else:
            self.opacity_slider = None
            self.opacity_value_label = None

        # Brush blend mode and reset button
        brush_blend_reset_layout = QHBoxLayout()

        # Only create blend combo if opacity slider is enabled
        if opacity_config.get("enabled", True):
            self.blend_combo = QComboBox()
            self.blend_combo.setStyleSheet(f"font-size: {get_font_size()};")
            self.blend_combo.setEditable(True)
            self.blend_combo.setMaximumWidth(150)
            # Add blending modes from configuration
            for mode in self.blender_modes:
                self.blend_combo.addItem(mode.replace("_", " ").title(), mode)

            self.blend_combo.currentTextChanged.connect(self.on_blend_mode_changed)

            # ============================================
            # Reset Button
            # ============================================
            self.reset_btn = QPushButton()
            icon_path = os.path.join(os.path.dirname(__file__), "image", "refresh.png")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.reset_btn.setIcon(icon)
                self.reset_btn.setIconSize(QPixmap(16, 16).size())
            else:
                self.reset_btn.setText("Reset")
                self.reset_btn.setStyleSheet(
                    f"font-size: {get_font_size()}; padding: 2px 8px;"
                )
            self.reset_btn.setFixedSize(24, 24)
            self.reset_btn.setToolTip("Reset brush settings")
            self.reset_btn.clicked.connect(self.reset_brush_settings)
        else:
            self.blend_combo = None
            self.reset_btn = None

        # ============================================
        # Layer Section: Opacity Slider, Blend Mode (conditionally created)
        # ============================================
        layer_section_layout = QVBoxLayout()

        layer_opacity_config = self.layer_config.get("opacity_slider", {})
        if layer_opacity_config.get("enabled", True):
            layer_opacity_layout = QHBoxLayout()

            self.layer_opacity_slider = QSlider(Qt.Horizontal)
            self.layer_opacity_slider.setMinimum(0)
            self.layer_opacity_slider.setMaximum(100)
            self.layer_opacity_slider.setValue(100)
            self.layer_opacity_slider.valueChanged.connect(
                self.on_layer_opacity_changed_debounced
            )

            number_size = layer_opacity_config.get("number_size", get_number_size())
            self.layer_opacity_value_label = QLabel("100%")
            self.layer_opacity_value_label.setStyleSheet(f"font-size: {number_size};")
            self.layer_opacity_value_label.setAlignment(Qt.AlignCenter)
            self.layer_opacity_value_label.setFixedWidth(35)

            layer_opacity_layout.addWidget(self.layer_opacity_slider, 1)
            layer_opacity_layout.addWidget(self.layer_opacity_value_label)
        else:
            self.layer_opacity_slider = None
            self.layer_opacity_value_label = None

        # Only create layer blend combo if layer opacity slider is enabled
        if layer_opacity_config.get("enabled", True):
            self.layer_blend_combo = QComboBox()
            self.layer_blend_combo.setStyleSheet(f"font-size: {get_font_size()};")
            self.layer_blend_combo.setEditable(True)
            self.layer_blend_combo.setMaximumWidth(150)
            # Add blending modes from configuration
            for mode in self.blender_modes:
                self.layer_blend_combo.addItem(mode.replace("_", " ").title(), mode)

            self.layer_blend_combo.currentTextChanged.connect(
                self.on_layer_blend_mode_changed
            )
        else:
            self.layer_blend_combo = None

        # ============================================
        # Assemble each section
        # ============================================

        # Assemble brush section
        if opacity_config.get("enabled", True):
            brush_section_layout.addLayout(brush_opacity_layout)
        if self.blend_combo is not None:
            brush_blend_reset_layout.addWidget(self.blend_combo)
            brush_blend_reset_layout.addWidget(self.reset_btn)
        brush_section_layout.addLayout(brush_blend_reset_layout)
        brush_section_layout.addStretch()

        # Assemble layer section
        if layer_opacity_config.get("enabled", True):
            layer_section_layout.addLayout(layer_opacity_layout)
        if self.layer_blend_combo is not None:
            layer_section_layout.addWidget(self.layer_blend_combo)
        layer_section_layout.addStretch()

        brush_and_layer_layout.addLayout(brush_section_layout)
        brush_and_layer_layout.addLayout(layer_section_layout)

        # Assemble left layout
        if size_config.get("enabled", True):
            left_layout.addLayout(size_layout)
        left_layout.addLayout(brush_and_layer_layout)
        left_layout.addStretch()

        # ============================================
        # Rotation widget on the right side (conditionally created)
        # ============================================
        right_layout = QHBoxLayout()
        right_layout.setSpacing(6)
        right_layout.setAlignment(Qt.AlignCenter)

        rotation_config = self.brush_config.get("rotation_slider", {})
        if rotation_config.get("enabled", True):
            self.rotation_widget = CircularRotationWidget()
            self.rotation_widget.setValue(0)
            self.rotation_widget.valueChanged.connect(self.on_rotation_changed)

            number_size = rotation_config.get("number_size", get_number_size())
            self.rotation_value_label = QLabel("0°")
            self.rotation_value_label.setStyleSheet(f"font-size: {number_size};")
            self.rotation_value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.rotation_value_label.setFixedWidth(
                35
            )  # Smaller width for side placement

            right_layout.addWidget(self.rotation_widget)
            right_layout.addWidget(self.rotation_value_label)
        else:
            self.rotation_widget = None
            self.rotation_value_label = None

        # ============================================
        # Add left and right layouts to main layout
        # ============================================
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout)

        # Add main layout to the widget
        layout.addLayout(main_layout)

        # Add color history widget below the main controls (conditionally created)
        if self.color_history_config.get("enabled", True):
            color_history_total = self.color_history_config.get(
                "total_items", get_color_history_total()
            )
            color_history_icon_size = self.color_history_config.get(
                "icon_size", get_color_history_icon_size()
            )
            self.color_history_widget = ColorHistoryWidget(
                self, color_history_total, color_history_icon_size
            )
            layout.addWidget(self.color_history_widget)
        else:
            self.color_history_widget = None

        # Add brush history widget below the color history (conditionally created)
        if self.brush_history_config.get("enabled", True):
            brush_history_total = self.brush_history_config.get(
                "total_items", get_brush_history_total()
            )
            brush_history_icon_size = self.brush_history_config.get(
                "icon_size", get_brush_history_icon_size()
            )
            self.brush_history_widget = BrushHistoryWidget(
                self, brush_history_total, brush_history_icon_size
            )
            layout.addWidget(self.brush_history_widget)
        else:
            self.brush_history_widget = None

        # Add status bar widget (conditionally created)
        if self.status_bar_config.get("enabled", True):
            self.status_bar_widget = StatusBarWidget(self)
            layout.addWidget(self.status_bar_widget)
        else:
            self.status_bar_widget = None

        # Add dynamic docker buttons below the brush history widget (conditionally created)
        if self.docker_toggle_config.get("enabled", True):
            docker_buttons_layout = QHBoxLayout()
            docker_buttons_layout.setSpacing(4)
            docker_buttons_layout.setContentsMargins(0, 5, 0, 0)
            docker_buttons_layout.setAlignment(
                Qt.AlignLeft
            )  # Align buttons to the left
            self.create_docker_buttons(docker_buttons_layout)
            layout.addLayout(docker_buttons_layout)

        self.setLayout(layout)

        # Load current brush settings
        self.update_from_current_brush()

    def brush_size_to_slider(self, size):
        """Convert brush size (1-1000) to slider value (0-100) with non-linear scaling"""
        if size <= 100:
            # Linear mapping for 1-100: maps to slider 0-70 (70% of slider range)
            return int((size - 1) * 70 / 100)
        else:
            # Linear mapping for 101-1000: maps to slider 71-100 (30% of slider range)
            return int(70 + (size - 100) * 30 / 900)

    def slider_to_brush_size(self, slider_value):
        """Convert slider value (0-100) to brush size (1-1000) with non-linear scaling"""
        if slider_value <= 70:
            # Map slider 0-70 to brush size 1-100
            return int(1 + slider_value * 100 / 70)
        else:
            # Map slider 71-100 to brush size 100-1000
            return int(100 + (slider_value - 70) * 900 / 30)

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
            if self.size_slider is not None:
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
            if self.opacity_slider is not None:
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
            if self.rotation_widget is not None:
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
            if self.blend_combo is not None:
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
                            self.blend_combo.setCurrentIndex(
                                self.blend_combo.count() - 1
                            )
                        self.current_blend_mode = blend_mode
                except:
                    # Fallback if blend mode method doesn't exist
                    self.blend_combo.setCurrentIndex(0)  # Set to "Normal"
                    self.current_blend_mode = "normal"

        self.updating_from_brush = False

    def check_layer_change(self):
        """Check if the current brush has changed and update sliders if needed"""
        app = Krita.instance()

        current_layer_opacity = None
        current_layer_blend_mode = None

        # Get current layer opacity
        try:
            if app.activeDocument() and app.activeDocument().activeNode():
                current_layer_opacity = app.activeDocument().activeNode().opacity()
        except:
            pass

        # Get current layer blend mode
        try:
            if app.activeDocument() and app.activeDocument().activeNode():
                current_layer_blend_mode = (
                    app.activeDocument().activeNode().blendingMode()
                )
        except:
            pass

        # Check if brush name changed OR if properties changed (for reload preset action)
        layer_opacity_changed = current_layer_opacity != self.current_layer_opacity
        layer_blend_changed = current_layer_blend_mode != self.current_layer_blend_mode

        if layer_opacity_changed or layer_blend_changed:
            self.current_layer_opacity = current_layer_opacity
            self.current_layer_blend_mode = current_layer_blend_mode
            self.update_from_current_layer()

    def update_from_current_layer(self):
        """Update sliders to match current brush settings"""
        if self.updating_from_layer:
            return

        app = Krita.instance()
        self.updating_from_layer = True

        if self.layer_opacity_slider is not None:
            try:
                activeNode = (
                    app.activeDocument().activeNode() if app.activeDocument() else None
                )
                if activeNode:
                    layer_opacity = activeNode.opacity()
                    layer_opacity_percent = int(
                        layer_opacity * 100 / 255
                    )  # Convert from 0-255 to 0-100
                    self.layer_opacity_slider.setValue(layer_opacity_percent)
                    self.layer_opacity_value_label.setText(f"{layer_opacity_percent}%")
                    self.current_layer_opacity = layer_opacity
            except:
                # Fallback if layer opacity method doesn't work
                self.layer_opacity_slider.setValue(100)
                self.layer_opacity_value_label.setText("100%")
                self.current_layer_opacity = 255

        # Get current layer blend mode
        if self.layer_blend_combo is not None:
            try:
                activeNode = (
                    app.activeDocument().activeNode() if app.activeDocument() else None
                )
                if activeNode:
                    layer_blend_mode = activeNode.blendingMode()
                    if layer_blend_mode:
                        # Find the blend mode in the combo box
                        index = self.layer_blend_combo.findData(layer_blend_mode)
                        if index >= 0:
                            self.layer_blend_combo.setCurrentIndex(index)
                        else:
                            # If not found, add it to the combo
                            self.layer_blend_combo.addItem(
                                layer_blend_mode.replace("_", " ").title(),
                                layer_blend_mode,
                            )
                            self.layer_blend_combo.setCurrentIndex(
                                self.layer_blend_combo.count() - 1
                            )
                        self.current_layer_blend_mode = layer_blend_mode
            except:
                # Fallback if layer blend mode method doesn't exist
                self.layer_blend_combo.setCurrentIndex(0)
                self.current_layer_blend_mode = "normal"
        self.updating_from_layer = False

    def on_opacity_changed_debounced(self, value):
        """Handle opacity slider with debouncing"""
        if self.updating_from_brush or self.opacity_slider is None:
            return

        # Update UI immediately for responsive feel
        self.opacity_value_label.setText(f"{value}%")

        # Store the pending value
        self.pending_opacity_value = value

        # Restart timer (300ms delay)
        self.opacity_debounce_timer.start(300)

    def on_size_slider_changed_debounced(self, slider_value):
        """Handle size slider with debouncing"""
        if self.updating_from_brush or self.size_slider is None:
            return

        brush_size = self.slider_to_brush_size(slider_value)

        # Update UI immediately
        self.size_value_label.setText(str(brush_size))

        # Store pending value
        self.pending_size_value = brush_size

        # Restart timer (300ms delay)
        self.size_debounce_timer.start(300)

    def on_layer_opacity_changed_debounced(self, value):
        """Handle layer opacity slider with debouncing"""
        if self.updating_from_layer or self.layer_opacity_slider is None:
            return

        # Update UI immediately
        self.layer_opacity_value_label.setText(f"{value}%")

        # Store pending value
        self.pending_layer_opacity_value = value

        # Restart timer (300ms delay)
        self.layer_opacity_debounce_timer.start(300)

    # ==========================================
    # Actual API calls - triggered after delay
    # ==========================================
    def apply_size_change(self):
        """Apply the pending size change to Krita"""
        if self.pending_size_value is None:
            return

        value = self.pending_size_value
        self.current_brush_size = value

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                view.setBrushSize(float(value))
            except Exception as e:
                print(f"Error setting brush size: {e}")

    def apply_opacity_change(self):
        """Apply the pending opacity change to Krita"""
        if self.pending_opacity_value is None:
            return

        value = self.pending_opacity_value
        opacity_float = value / 100.0
        self.current_brush_opacity = opacity_float

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                view.setPaintingOpacity(opacity_float)
            except Exception as e:
                print(f"Error setting brush opacity: {e}")

    def apply_layer_opacity_change(self):
        """Apply the pending layer opacity change to Krita"""
        if self.pending_layer_opacity_value is None:
            return

        value = self.pending_layer_opacity_value
        opacity_int = int(value * 255 / 100)
        self.current_layer_opacity = opacity_int

        app = Krita.instance()
        activeDoc = app.activeDocument()
        activeNode = activeDoc.activeNode() if activeDoc else None
        if activeNode:
            try:
                activeNode.setOpacity(opacity_int)
                activeDoc.refreshProjection()
            except Exception as e:
                print(f"Error setting layer opacity: {e}")

    # ==========================================

    def on_rotation_changed(self, value):
        """Handle brush rotation change"""
        if self.updating_from_brush or self.rotation_widget is None:
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
        if self.updating_from_brush or self.blend_combo is None:
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

    def on_layer_blend_mode_changed(self, text):
        """Handle layer blend mode change"""
        if self.updating_from_layer or self.layer_blend_combo is None:
            return

        # Get the blend mode data from the combo box
        layer_blend_mode = self.layer_blend_combo.currentData()
        if layer_blend_mode:
            self.current_layer_blend_mode = layer_blend_mode  # Update tracked value

            app = Krita.instance()
            activeDoc = app.activeDocument()
            activeNode = activeDoc.activeNode() if activeDoc else None
            if activeNode:
                try:
                    # Set blend mode on the active node
                    activeNode.setBlendingMode(layer_blend_mode)
                    # Refresh the projection to update the canvas display
                    activeDoc.refreshProjection()
                    print(f"Set layer blend mode to: {layer_blend_mode}")
                except Exception as e:
                    print(f"Error setting layer blend mode: {e}")

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
        if (
            hasattr(self, "color_history_widget")
            and self.color_history_widget is not None
        ):
            self.color_history_widget.force_color_update()
        # Also force brush history update
        if (
            hasattr(self, "brush_history_widget")
            and self.brush_history_widget is not None
        ):
            self.brush_history_widget.force_brush_update()
            # Add a test brush to verify functionality
            self.brush_history_widget.add_test_brush()

    def refresh_styles(self):
        """Refresh styles when settings change"""
        style = f"font-size: {get_font_size()};"
        for label in self.findChildren(QLabel):
            if label.text() not in ["Brush Adjustments"]:  # Skip title
                label.setStyleSheet(style)

    def closeEvent(self, event):
        """Clean up timers when widget is closed"""
        if hasattr(self, "brush_check_timer"):
            self.brush_check_timer.stop()
        if (
            hasattr(self, "color_history_widget")
            and self.color_history_widget is not None
        ):
            self.color_history_widget.closeEvent(event)
        if (
            hasattr(self, "brush_history_widget")
            and self.brush_history_widget is not None
        ):
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
