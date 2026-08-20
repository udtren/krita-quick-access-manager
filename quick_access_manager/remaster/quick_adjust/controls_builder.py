"""
Shared builder for the brush/layer slider and dropdown controls used by the
Quick Adjust docker (BrushAdjustmentWidget) and the HueSVC popup's right
panel (BrushLayerControlsWidget).

`create_brush_layer_controls()` creates the individual widgets (assigned as
attributes on the target widget) and returns the slider+value-label rows as
sub-layouts. `build_docker_controls_layout()` arranges those pieces for the
docker; `build_popup_controls_layout()` arranges them for the popup panel.
"""

import os

from ..compat import (
    QComboBox,
    QHBoxLayout,
    QIcon,
    QLabel,
    QPixmap,
    QPushButton,
    QSlider,
    Qt,
    QVBoxLayout,
)
from ..infrastructure import get_quick_adjust_icons_dir
from .settings import get_font_size, get_number_size
from .utils_adjust import brush_size_to_slider
from .widgets import CircularRotationWidget


def create_brush_layer_controls(
    widget, brush_config, layer_config, blender_modes, font_size=None
):
    """Create every slider/dropdown/rotation/reset control.

    Assigns the resulting widgets (size_slider, opacity_slider, flow_slider,
    blend_combo, reset_btn, layer_opacity_slider, layer_blend_combo,
    rotation_widget, rotation_value_label - any of which may be None when
    disabled via config) as attributes on `widget`.

    `font_size` overrides the blend-mode dropdowns' and reset button's text
    size (both otherwise always follow the Quick Adjust docker's font size
    setting, which the HueSVC popup panel needs to size independently of).
    Value-label sizes still come from each config dict's own `number_size`.
    """
    rows = {}
    combo_font_size = font_size or get_font_size()

    size_config = brush_config.get("size_slider", {})
    if size_config.get("enabled", True):
        size_layout = QHBoxLayout()
        size_layout.setSpacing(6)

        widget.size_slider = QSlider(Qt.Horizontal)
        widget.size_slider.setMinimum(0)
        widget.size_slider.setMaximum(100)
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

    if opacity_config.get("enabled", True):
        widget.blend_combo = QComboBox()
        widget.blend_combo.setStyleSheet(f"font-size: {combo_font_size};")
        widget.blend_combo.setEditable(True)
        widget.blend_combo.setMaximumWidth(150)
        for mode in blender_modes:
            widget.blend_combo.addItem(mode.replace("_", " ").title(), mode)
        widget.blend_combo.currentTextChanged.connect(widget.on_blend_mode_changed)

        widget.reset_btn = QPushButton()
        icon_path = os.path.join(get_quick_adjust_icons_dir(), "refresh.png")
        if os.path.exists(icon_path):
            widget.reset_btn.setIcon(QIcon(icon_path))
            widget.reset_btn.setIconSize(QPixmap(16, 16).size())
        else:
            widget.reset_btn.setText("Reset")
            widget.reset_btn.setStyleSheet(
                f"font-size: {combo_font_size}; padding: 2px 8px;"
            )
        widget.reset_btn.setFixedSize(24, 24)
        widget.reset_btn.setToolTip("Reset brush settings")
        widget.reset_btn.clicked.connect(widget.reset_brush_settings)
    else:
        widget.blend_combo = None
        widget.reset_btn = None

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

    if layer_opacity_config.get("enabled", True):
        widget.layer_blend_combo = QComboBox()
        widget.layer_blend_combo.setStyleSheet(f"font-size: {combo_font_size};")
        widget.layer_blend_combo.setEditable(True)
        widget.layer_blend_combo.setMaximumWidth(150)
        for mode in blender_modes:
            widget.layer_blend_combo.addItem(mode.replace("_", " ").title(), mode)
        widget.layer_blend_combo.currentTextChanged.connect(
            widget.on_layer_blend_mode_changed
        )
    else:
        widget.layer_blend_combo = None

    # Rotation widget - always created but not placed by this function. The
    # popup layout below adds it inline; the docker instead reparents it into
    # a floating pad (ControlButtonWidget.enableRotationExtension()).
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


def build_docker_controls_layout(
    widget, brush_config, layer_config, blender_modes, font_size=None
):
    """Assemble controls into the Quick Adjust docker's layout."""
    rows = create_brush_layer_controls(
        widget, brush_config, layer_config, blender_modes, font_size=font_size
    )

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


def build_popup_controls_layout(
    widget, brush_config, layer_config, blender_modes, font_size=None
):
    """Arrange the controls for the HueSVC popup's right panel."""
    rows = create_brush_layer_controls(
        widget, brush_config, layer_config, blender_modes, font_size=font_size
    )

    layout = QVBoxLayout()
    layout.setSpacing(6)

    if rows["size"] is not None:
        layout.addLayout(rows["size"])
    if rows["opacity"] is not None:
        layout.addLayout(rows["opacity"])
    if rows["flow"] is not None:
        layout.addLayout(rows["flow"])
    if widget.blend_combo is not None:
        layout.addWidget(widget.blend_combo)

    rotation_layout = QHBoxLayout()
    rotation_layout.addWidget(widget.rotation_widget)
    rotation_layout.addWidget(widget.rotation_value_label)
    if widget.reset_btn is not None:
        rotation_layout.addWidget(widget.reset_btn)
    layout.addLayout(rotation_layout)

    if rows["layer_opacity"] is not None:
        layout.addLayout(rows["layer_opacity"])
    if widget.layer_blend_combo is not None:
        layout.addWidget(widget.layer_blend_combo)

    return layout
