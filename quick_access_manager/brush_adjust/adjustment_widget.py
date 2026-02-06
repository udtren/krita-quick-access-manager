"""
Main brush adjustment widget with UI and coordination logic.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
    QDockWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from krita import Krita  # type: ignore
import os

# Import widgets from the widgets2 package
from .widgets import (
    ColorHistoryWidget,
    CircularRotationWidget,
    BrushHistoryWidget,
    ControlButtonWidget,
)

# Import configuration loader
from ..config.quick_adjust_docker_loader import (
    get_brush_section,
    get_layer_section,
    get_brush_history_section,
    get_color_history_section,
    get_blender_mode_list,
    get_docker_toggle_section,
    get_font_size,
    get_number_size,
    get_color_history_total,
    get_color_history_icon_size,
    get_brush_history_total,
    get_brush_history_icon_size,
)


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
        self.docker_toggle_config = get_docker_toggle_section()
        self.blender_modes = get_blender_mode_list()

        # Initialize monitoring from mixins
        self.setup_brush_monitoring()
        self.setup_layer_monitoring()

        # Build UI
        self.init_ui()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_docker_size)
        self.update_timer.start(2000)  # 1000 ms = 1 second

    def init_ui(self):
        """Build the complete UI"""
        # Create wrapper layout to hold main content and control buttons
        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(5)

        # Create main content layout
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

            self.size_slider = QSlider(Qt.Orientation.Horizontal)
            self.size_slider.setMinimum(0)
            self.size_slider.setMaximum(100)  # Use 0-100 range for internal scaling
            self.size_slider.setValue(brush_size_to_slider(10))
            self.size_slider.valueChanged.connect(self.on_size_slider_changed_debounced)

            number_size = size_config.get("number_size", get_number_size())
            self.size_value_label = QLabel("10")
            self.size_value_label.setStyleSheet(f"font-size: {number_size};")
            self.size_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.size_value_label.setFixedWidth(35)

            size_layout.addWidget(self.size_slider, 1)
            size_layout.addWidget(self.size_value_label)
        else:
            self.size_slider = None
            self.size_value_label = None

        # ============================================
        # Brush Section: Opacity Slider, Flow Slider, Blend Mode (conditionally created)
        # ============================================
        brush_and_layer_layout = QHBoxLayout()
        brush_section_layout = QVBoxLayout()

        opacity_config = self.brush_config.get("opacity_slider", {})
        if opacity_config.get("enabled", True):
            brush_opacity_layout = QHBoxLayout()

            self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
            self.opacity_slider.setMinimum(0)
            self.opacity_slider.setMaximum(100)
            self.opacity_slider.setValue(100)
            self.opacity_slider.valueChanged.connect(self.on_opacity_changed_debounced)

            number_size = opacity_config.get("number_size", get_number_size())
            self.opacity_value_label = QLabel("100%")
            self.opacity_value_label.setStyleSheet(f"font-size: {number_size};")
            self.opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.opacity_value_label.setFixedWidth(35)

            brush_opacity_layout.addWidget(self.opacity_slider, 1)
            brush_opacity_layout.addWidget(self.opacity_value_label)
        else:
            self.opacity_slider = None
            self.opacity_value_label = None

        # Flow slider (under opacity slider)
        flow_config = self.brush_config.get("flow_slider", {})
        if flow_config.get("enabled", True):
            brush_flow_layout = QHBoxLayout()

            self.flow_slider = QSlider(Qt.Orientation.Horizontal)
            self.flow_slider.setMinimum(0)
            self.flow_slider.setMaximum(100)
            self.flow_slider.setValue(100)
            self.flow_slider.valueChanged.connect(self.on_flow_changed_debounced)

            number_size = flow_config.get("number_size", get_number_size())
            self.flow_value_label = QLabel("100%")
            self.flow_value_label.setStyleSheet(f"font-size: {number_size};")
            self.flow_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.flow_value_label.setFixedWidth(35)

            brush_flow_layout.addWidget(self.flow_slider, 1)
            brush_flow_layout.addWidget(self.flow_value_label)
        else:
            self.flow_slider = None
            self.flow_value_label = None

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

            self.layer_opacity_slider = QSlider(Qt.Orientation.Horizontal)
            self.layer_opacity_slider.setMinimum(0)
            self.layer_opacity_slider.setMaximum(100)
            self.layer_opacity_slider.setValue(100)
            self.layer_opacity_slider.valueChanged.connect(
                self.on_layer_opacity_changed_debounced
            )

            number_size = layer_opacity_config.get("number_size", get_number_size())
            self.layer_opacity_value_label = QLabel("100%")
            self.layer_opacity_value_label.setStyleSheet(f"font-size: {number_size};")
            self.layer_opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        if flow_config.get("enabled", True):
            brush_section_layout.addLayout(brush_flow_layout)
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
        # Rotation widget - always enabled as floating widget (not added to docker layout)
        # ============================================
        rotation_config = self.brush_config.get("rotation_slider", {})
        # Always create rotation widget for floating display
        self.rotation_widget = CircularRotationWidget()
        self.rotation_widget.setValue(0)
        self.rotation_widget.valueChanged.connect(self.on_rotation_changed)

        number_size = rotation_config.get("number_size", get_number_size())
        self.rotation_value_label = QLabel("0°")
        self.rotation_value_label.setStyleSheet(f"font-size: {number_size};")
        self.rotation_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.rotation_value_label.setFixedWidth(35)

        # Note: rotation_widget and rotation_value_label are NOT added to any layout here
        # They will be used by the floating rotation widget instead

        # ============================================
        # Add left layout to main layout (no right layout needed)
        # ============================================
        main_layout.addLayout(left_layout, 1)

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

        # Add dynamic docker buttons below the brush history widget (conditionally created)
        if self.docker_toggle_config.get("enabled", True):
            docker_buttons_layout = QHBoxLayout()
            docker_buttons_layout.setSpacing(4)
            docker_buttons_layout.setContentsMargins(0, 5, 0, 0)
            docker_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            create_docker_buttons(
                docker_buttons_layout,
                self.docker_buttons_config,
                toggle_docker_by_keywords,
            )
            layout.addLayout(docker_buttons_layout)

        # Add main content layout to wrapper
        wrapper_layout.addLayout(layout)

        # Add control buttons layout to wrapper
        self.control_buttons_layout = ControlButtonWidget(self)
        wrapper_layout.addWidget(self.control_buttons_layout)

        self.setLayout(wrapper_layout)

        # Load current brush settings
        self.update_from_current_brush()

    def force_update(self):
        """Force update from current brush - can be called externally"""
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None
        self.current_brush_flow = None
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

    def update_docker_size(self):
        # Force immediate size recalculation
        self.updateGeometry()
        self.adjustSize()

        # Find and update parent docker size more aggressively
        parent_widget = self.parent()
        while parent_widget:
            parent_widget.updateGeometry()
            if hasattr(parent_widget, "layout") and parent_widget.layout():
                parent_widget.layout().invalidate()
                parent_widget.layout().activate()

            if isinstance(parent_widget, QDockWidget):
                # Force the docker to resize by setting size policies and hints
                parent_widget.updateGeometry()
                parent_widget.adjustSize()

                # Get the main widget and force it to recalculate
                main_widget = parent_widget.widget()
                if main_widget:
                    main_widget.updateGeometry()
                    main_widget.adjustSize()
                break
            parent_widget = parent_widget.parent()

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
        # Close floating widget if it exists
        if (
            hasattr(self, "control_buttons_layout")
            and self.control_buttons_layout is not None
            and hasattr(self.control_buttons_layout, "float_tool_options")
            and self.control_buttons_layout.float_tool_options is not None
        ):
            self.control_buttons_layout.float_tool_options.close()
        super().closeEvent(event)
