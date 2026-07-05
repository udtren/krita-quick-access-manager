"""
Shared builder for the brush/layer slider and dropdown controls used by both
the Quick Adjust docker (BrushAdjustmentWidget) and the color selector popup's
BrushLayerControlsWidget.

`create_brush_layer_controls()` creates the individual widgets (assigned as
attributes on the target widget) and returns the slider+value-label rows as
sub-layouts. `build_docker_controls_layout()` and `build_popup_controls_layout()`
arrange those pieces differently for their respective embedders.
"""

import os

from ..compat import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
    Qt,
    QIcon,
    QPixmap,
)
from .widgets import CircularRotationWidget
from ..config.quick_adjust_docker_loader import get_font_size, get_number_size
from .utils_adjust import brush_size_to_slider


def create_brush_layer_controls(widget, brush_config, layer_config, blender_modes):
    """Create every slider/dropdown/rotation/reset control.

    Assigns the resulting widgets (size_slider, opacity_slider, flow_slider,
    blend_combo, reset_btn, layer_opacity_slider, layer_blend_combo,
    rotation_widget, rotation_value_label - any of which may be None when
    disabled via config) as attributes on `widget`.

    Returns a dict of the slider+value-label row sub-layouts (None for any
    disabled control), for callers to arrange into their own layout:
        {"size": QHBoxLayout|None, "opacity": ..., "flow": ..., "layer_opacity": ...}
    Standalone widgets (blend_combo, reset_btn, layer_blend_combo,
    rotation_widget, rotation_value_label) are available directly as
    `widget.<name>` and can be added to any layout the caller builds.
    """
    rows = {}

    # ============================================
    # Size row: Slider | Value (conditionally created)
    # ============================================
    size_config = brush_config.get("size_slider", {})
    if size_config.get("enabled", True):
        size_layout = QHBoxLayout()
        size_layout.setSpacing(6)

        widget.size_slider = QSlider(Qt.Horizontal)
        widget.size_slider.setMinimum(0)
        widget.size_slider.setMaximum(100)  # Use 0-100 range for internal scaling
        widget.size_slider.setValue(brush_size_to_slider(10))
        widget.size_slider.valueChanged.connect(widget.on_size_slider_changed_debounced)

        number_size = size_config.get("number_size", get_number_size())
        widget.size_value_label = QLabel("10")
        widget.size_value_label.setStyleSheet(f"font-size: {number_size};")
        widget.size_value_label.setAlignment(Qt.AlignCenter)
        widget.size_value_label.setFixedWidth(35)

        size_layout.addWidget(widget.size_slider, 1)
        size_layout.addWidget(widget.size_value_label)
        rows["size"] = size_layout
    else:
        widget.size_slider = None
        widget.size_value_label = None
        rows["size"] = None

    # ============================================
    # Brush opacity slider (conditionally created)
    # ============================================
    opacity_config = brush_config.get("opacity_slider", {})
    if opacity_config.get("enabled", True):
        brush_opacity_layout = QHBoxLayout()

        widget.opacity_slider = QSlider(Qt.Horizontal)
        widget.opacity_slider.setMinimum(0)
        widget.opacity_slider.setMaximum(100)
        widget.opacity_slider.setValue(100)
        widget.opacity_slider.valueChanged.connect(widget.on_opacity_changed_debounced)

        number_size = opacity_config.get("number_size", get_number_size())
        widget.opacity_value_label = QLabel("100%")
        widget.opacity_value_label.setStyleSheet(f"font-size: {number_size};")
        widget.opacity_value_label.setAlignment(Qt.AlignCenter)
        widget.opacity_value_label.setFixedWidth(35)

        brush_opacity_layout.addWidget(widget.opacity_slider, 1)
        brush_opacity_layout.addWidget(widget.opacity_value_label)
        rows["opacity"] = brush_opacity_layout
    else:
        widget.opacity_slider = None
        widget.opacity_value_label = None
        rows["opacity"] = None

    # ============================================
    # Brush flow slider (conditionally created)
    # ============================================
    flow_config = brush_config.get("flow_slider", {})
    if flow_config.get("enabled", True):
        brush_flow_layout = QHBoxLayout()

        widget.flow_slider = QSlider(Qt.Horizontal)
        widget.flow_slider.setMinimum(0)
        widget.flow_slider.setMaximum(100)
        widget.flow_slider.setValue(100)
        widget.flow_slider.valueChanged.connect(widget.on_flow_changed_debounced)

        number_size = flow_config.get("number_size", get_number_size())
        widget.flow_value_label = QLabel("100%")
        widget.flow_value_label.setStyleSheet(f"font-size: {number_size};")
        widget.flow_value_label.setAlignment(Qt.AlignCenter)
        widget.flow_value_label.setFixedWidth(35)

        brush_flow_layout.addWidget(widget.flow_slider, 1)
        brush_flow_layout.addWidget(widget.flow_value_label)
        rows["flow"] = brush_flow_layout
    else:
        widget.flow_slider = None
        widget.flow_value_label = None
        rows["flow"] = None

    # ============================================
    # Brush blend mode and reset button (only if opacity slider is enabled)
    # ============================================
    if opacity_config.get("enabled", True):
        widget.blend_combo = QComboBox()
        widget.blend_combo.setStyleSheet(f"font-size: {get_font_size()};")
        widget.blend_combo.setEditable(True)
        widget.blend_combo.setMaximumWidth(150)
        for mode in blender_modes:
            widget.blend_combo.addItem(mode.replace("_", " ").title(), mode)
        widget.blend_combo.currentTextChanged.connect(widget.on_blend_mode_changed)

        widget.reset_btn = QPushButton()
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "image", "refresh.png"
        )
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            widget.reset_btn.setIcon(icon)
            widget.reset_btn.setIconSize(QPixmap(16, 16).size())
        else:
            widget.reset_btn.setText("Reset")
            widget.reset_btn.setStyleSheet(
                f"font-size: {get_font_size()}; padding: 2px 8px;"
            )
        widget.reset_btn.setFixedSize(24, 24)
        widget.reset_btn.setToolTip("Reset brush settings")
        widget.reset_btn.clicked.connect(widget.reset_brush_settings)
    else:
        widget.blend_combo = None
        widget.reset_btn = None

    # ============================================
    # Layer opacity slider (conditionally created)
    # ============================================
    layer_opacity_config = layer_config.get("opacity_slider", {})
    if layer_opacity_config.get("enabled", True):
        layer_opacity_layout = QHBoxLayout()

        widget.layer_opacity_slider = QSlider(Qt.Horizontal)
        widget.layer_opacity_slider.setMinimum(0)
        widget.layer_opacity_slider.setMaximum(100)
        widget.layer_opacity_slider.setValue(100)
        widget.layer_opacity_slider.valueChanged.connect(
            widget.on_layer_opacity_changed_debounced
        )

        number_size = layer_opacity_config.get("number_size", get_number_size())
        widget.layer_opacity_value_label = QLabel("100%")
        widget.layer_opacity_value_label.setStyleSheet(f"font-size: {number_size};")
        widget.layer_opacity_value_label.setAlignment(Qt.AlignCenter)
        widget.layer_opacity_value_label.setFixedWidth(35)

        layer_opacity_layout.addWidget(widget.layer_opacity_slider, 1)
        layer_opacity_layout.addWidget(widget.layer_opacity_value_label)
        rows["layer_opacity"] = layer_opacity_layout
    else:
        widget.layer_opacity_slider = None
        widget.layer_opacity_value_label = None
        rows["layer_opacity"] = None

    # ============================================
    # Layer blend mode (only if layer opacity slider is enabled)
    # ============================================
    if layer_opacity_config.get("enabled", True):
        widget.layer_blend_combo = QComboBox()
        widget.layer_blend_combo.setStyleSheet(f"font-size: {get_font_size()};")
        widget.layer_blend_combo.setEditable(True)
        widget.layer_blend_combo.setMaximumWidth(150)
        for mode in blender_modes:
            widget.layer_blend_combo.addItem(mode.replace("_", " ").title(), mode)
        widget.layer_blend_combo.currentTextChanged.connect(
            widget.on_layer_blend_mode_changed
        )
    else:
        widget.layer_blend_combo = None

    # ============================================
    # Rotation widget - always created. Neither assembly function is forced
    # to place it; the Quick Adjust docker reparents it into a separate
    # floating pad instead of adding it to its own layout.
    # ============================================
    rotation_config = brush_config.get("rotation_slider", {})
    widget.rotation_widget = CircularRotationWidget()
    widget.rotation_widget.setValue(0)
    widget.rotation_widget.valueChanged.connect(widget.on_rotation_changed)

    number_size = rotation_config.get("number_size", get_number_size())
    widget.rotation_value_label = QLabel("0°")
    widget.rotation_value_label.setStyleSheet(f"font-size: {number_size};")
    widget.rotation_value_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    widget.rotation_value_label.setFixedWidth(35)

    return rows


def build_docker_controls_layout(widget, brush_config, layer_config, blender_modes):
    """Assemble controls into the Quick Adjust docker's layout:
        size slider                                    (full width)
        [opacity / flow / blend+reset] | [layer opacity / layer blend]
    The rotation widget is created but not added here - the docker reparents
    it into a separate floating pad (see ControlButtonWidget).
    """
    rows = create_brush_layer_controls(widget, brush_config, layer_config, blender_modes)

    left_layout = QVBoxLayout()
    left_layout.setSpacing(6)
    if rows["size"] is not None:
        left_layout.addLayout(rows["size"])

    brush_and_layer_layout = QHBoxLayout()

    brush_section_layout = QVBoxLayout()
    if rows["opacity"] is not None:
        brush_section_layout.addLayout(rows["opacity"])
    if rows["flow"] is not None:
        brush_section_layout.addLayout(rows["flow"])
    brush_blend_reset_layout = QHBoxLayout()
    if widget.blend_combo is not None:
        brush_blend_reset_layout.addWidget(widget.blend_combo)
        brush_blend_reset_layout.addWidget(widget.reset_btn)
    brush_section_layout.addLayout(brush_blend_reset_layout)
    brush_section_layout.addStretch()

    layer_section_layout = QVBoxLayout()
    if rows["layer_opacity"] is not None:
        layer_section_layout.addLayout(rows["layer_opacity"])
    if widget.layer_blend_combo is not None:
        layer_section_layout.addWidget(widget.layer_blend_combo)
    layer_section_layout.addStretch()

    brush_and_layer_layout.addLayout(brush_section_layout)
    brush_and_layer_layout.addLayout(layer_section_layout)
    left_layout.addLayout(brush_and_layer_layout)
    left_layout.addStretch()

    return left_layout


def build_popup_controls_layout(widget, brush_config, layer_config, blender_modes):
    """Assemble controls into the color selector popup's grid layout:
        size slider
        opacity slider       | layer opacity slider
        flow slider          | layer blending mode dropdown
        blending mode dropdown
        rotation circle       | reset button
    """
    rows = create_brush_layer_controls(widget, brush_config, layer_config, blender_modes)

    grid = QGridLayout()
    grid.setVerticalSpacing(6)
    grid.setHorizontalSpacing(10)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)

    row = 0
    if rows["size"] is not None:
        grid.addLayout(rows["size"], row, 0, 1, 2)
        row += 1

    if rows["opacity"] is not None:
        grid.addLayout(rows["opacity"], row, 0)
    if rows["layer_opacity"] is not None:
        grid.addLayout(rows["layer_opacity"], row, 1)
    if rows["opacity"] is not None or rows["layer_opacity"] is not None:
        row += 1

    if rows["flow"] is not None:
        grid.addLayout(rows["flow"], row, 0)
    if widget.layer_blend_combo is not None:
        grid.addWidget(widget.layer_blend_combo, row, 1)
    if rows["flow"] is not None or widget.layer_blend_combo is not None:
        row += 1

    if widget.blend_combo is not None:
        grid.addWidget(widget.blend_combo, row, 0, 1, 2)
        row += 1

    rotation_layout = QHBoxLayout()
    rotation_layout.addWidget(widget.rotation_widget)
    rotation_layout.addWidget(widget.rotation_value_label)
    grid.addLayout(rotation_layout, row, 0)
    if widget.reset_btn is not None:
        grid.addWidget(widget.reset_btn, row, 1)
    row += 1

    return grid
