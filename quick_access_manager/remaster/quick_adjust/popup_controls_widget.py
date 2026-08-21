"""
Lightweight brush/layer controls widget for embedding in the HueSVC popup -
sliders and dropdowns only, no history widgets, docker buttons, or global key
listeners (those belong to the Quick Adjust docker only).
"""

from ..compat import QWidget
from .controls_builder import build_popup_controls_layout
from .brush_monitor import BrushMonitorMixin
from .layer_monitor import LayerMonitorMixin
from .settings import get_blender_mode_list, get_brush_section, get_layer_section


class BrushLayerControlsWidget(QWidget, BrushMonitorMixin, LayerMonitorMixin):
    """Sliders/dropdowns for brush size, opacity, flow, blend mode, rotation,
    and layer opacity/blend mode - laid out for the HueSVC popup."""

    def __init__(self, parent=None, font_size=None):
        """`font_size` (a CSS size string, e.g. "12px") overrides every label
        and dropdown's text size, independent of the Quick Adjust docker's own
        font size setting - the HueSVC popup panel configures this separately
        since it's a much narrower panel."""
        super().__init__(parent)

        self.brush_config = get_brush_section()
        self.layer_config = get_layer_section()
        self.blender_modes = get_blender_mode_list()
        if font_size:
            for section in (self.brush_config, self.layer_config):
                for entry in section.values():
                    if isinstance(entry, dict) and "number_size" in entry:
                        entry["number_size"] = font_size

        self.setup_brush_monitoring()
        self.setup_layer_monitoring()

        layout = build_popup_controls_layout(
            self,
            self.brush_config,
            self.layer_config,
            self.blender_modes,
            font_size=font_size,
        )
        self.setLayout(layout)

        self.update_from_current_brush()
        self.update_from_current_layer()

    def start_monitoring(self):
        """Resume polling brush/layer state. Call when the popup becomes visible."""
        self.brush_check_timer.start(200)
        self.layer_check_timer.start(200)
        self.update_from_current_brush()
        self.update_from_current_layer()

    def stop_monitoring(self):
        """Pause polling brush/layer state. Call when the popup is hidden."""
        self.brush_check_timer.stop()
        self.layer_check_timer.stop()

    def closeEvent(self, event):
        self.brush_check_timer.stop()
        self.layer_check_timer.stop()
        super().closeEvent(event)
