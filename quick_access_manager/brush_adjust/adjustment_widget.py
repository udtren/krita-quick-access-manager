"""
Main brush adjustment widget with UI and coordination logic.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from krita import Krita  # type: ignore
import os

# Import widgets from the widgets2 package
from .widgets import (
    ColorHistoryWidget,
    CircularRotationWidget,
    BrushHistoryWidget,
    StatusBarWidget,
)

# Import configuration loader
from ..config.quick_adjust_docker_loader import (
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

from .floating_widgets.tool_options import ntToolOptions

# Import local modules
from .docker_buttons import (
    load_docker_buttons_config,
    create_docker_buttons,
    toggle_docker_by_keywords,
)
from .utils_adjust import brush_size_to_slider, slider_to_brush_size
from .brush_monitor import BrushMonitorMixin
from .layer_monitor import LayerMonitorMixin


class BrushAdjustmentWidget(QWidget, BrushMonitorMixin, LayerMonitorMixin):
    """Main widget for brush and layer adjustments"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent

        # Load docker buttons configuration
        self.docker_buttons_config = load_docker_buttons_config()

        # Load quick adjust docker configuration
        self.brush_config = get_brush_section()
        self.layer_config = get_layer_section()
        self.brush_history_config = get_brush_history_section()
        self.color_history_config = get_color_history_section()
        self.status_bar_config = get_status_bar_section()
        self.docker_toggle_config = get_docker_toggle_section()
        self.blender_modes = get_blender_mode_list()

        # Initialize monitoring from mixins
        self.setup_brush_monitoring()
        self.setup_layer_monitoring()

        # Build UI
        self.init_ui()

        # Setup tool options extension initialization
        application = Krita.instance()
        appNotifier = application.notifier()
        appNotifier.windowCreated.connect(self.enableToolOptionsExtension)

    def init_ui(self):
        """Build the complete UI"""
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
            self.size_slider.setValue(brush_size_to_slider(10))
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
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "image", "refresh.png"
            )
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
            self.rotation_value_label.setFixedWidth(35)

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
            docker_buttons_layout.setAlignment(Qt.AlignLeft)
            create_docker_buttons(
                docker_buttons_layout,
                self.docker_buttons_config,
                toggle_docker_by_keywords,
            )
            layout.addLayout(docker_buttons_layout)

        self.setLayout(layout)

        # Load current brush settings
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
        if hasattr(self, "layer_check_timer"):
            self.layer_check_timer.stop()
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

    def enableToolOptionsExtension(self):
        """Enable the floating Tool Options extension if not already enabled"""
        window = Krita.instance().activeWindow()
        self.ntTO = ntToolOptions(window)
        self.ntTO.pad.show()
