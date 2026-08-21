"""
Main brush adjustment widget with UI and coordination logic.
"""

from ..compat import (
    QDockWidget,
    QHBoxLayout,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from .alt_erase_listener import (
    AltEraseListener,
    PreserveAlphaListener,
    SelectOutlineListener,
    TempBrushSetListener,
)
from .brush_monitor import BrushMonitorMixin
from .controls_builder import build_docker_controls_layout
from .layer_monitor import LayerMonitorMixin
from .settings import (
    get_alt_erase_key,
    get_blender_mode_list,
    get_brush_history_icon_size,
    get_brush_history_section,
    get_brush_history_total,
    get_brush_section,
    get_color_history_icon_size,
    get_color_history_section,
    get_color_history_total,
    get_layer_section,
    get_preserve_alpha_key,
    get_select_outline_key,
    get_temp_brush_sets,
)
from .widgets import (
    BrushHistoryWidget,
    ColorHistoryWidget,
    ControlButtonWidget,
)


class BrushAdjustmentWidget(QWidget, BrushMonitorMixin, LayerMonitorMixin):
    """Main widget for brush and layer adjustments"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_docker = parent

        self.brush_config = get_brush_section()
        self.layer_config = get_layer_section()
        self.brush_history_config = get_brush_history_section()
        self.color_history_config = get_color_history_section()
        self.blender_modes = get_blender_mode_list()

        alt_erase_key = get_alt_erase_key()
        if alt_erase_key:
            self._alt_erase_listener = AltEraseListener(alt_erase_key)
            self.destroyed.connect(self._alt_erase_listener.remove)
        else:
            self._alt_erase_listener = None

        preserve_alpha_key = get_preserve_alpha_key()
        if preserve_alpha_key:
            self._preserve_alpha_listener = PreserveAlphaListener(preserve_alpha_key)
            self.destroyed.connect(self._preserve_alpha_listener.remove)
        else:
            self._preserve_alpha_listener = None

        select_outline_key = get_select_outline_key()
        if select_outline_key:
            self._select_outline_listener = SelectOutlineListener(select_outline_key)
            self.destroyed.connect(self._select_outline_listener.remove)
        else:
            self._select_outline_listener = None

        self._temp_brush_set_listeners = []
        for entry in get_temp_brush_sets():
            key = entry.get("key", "")
            brush = entry.get("brush", "")
            size_scale = float(entry.get("size_scale", 0.0))
            if key and brush:
                listener = TempBrushSetListener(key, brush, size_scale)
                self.destroyed.connect(listener.remove)
                self._temp_brush_set_listeners.append(listener)

        self.setup_brush_monitoring()
        self.setup_layer_monitoring()

        self.init_ui()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_docker_size)
        self.update_timer.start(2000)

    def init_ui(self):
        """Build the complete UI"""
        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(5)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)

        left_layout = build_docker_controls_layout(
            self, self.brush_config, self.layer_config, self.blender_modes
        )

        main_layout.addLayout(left_layout, 1)
        layout.addLayout(main_layout)

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

        wrapper_layout.addLayout(layout)

        self.control_buttons_layout = ControlButtonWidget(self)
        wrapper_layout.addWidget(self.control_buttons_layout)

        self.setLayout(wrapper_layout)

        self.update_from_current_brush()

    def set_monitoring_active(self, active):
        """Start/stop the polling timers.

        Driven by the docker's show/hide so a collapsed or tabbed-away docker
        stops polling Krita five times a second. Qt sends hide events to the
        QDockWidget, not to this child widget, so the docker calls this for us.
        """
        timers = (
            getattr(self, "brush_check_timer", None),
            getattr(self, "layer_check_timer", None),
            getattr(self, "update_timer", None),
        )
        intervals = (200, 200, 2000)
        for timer, interval in zip(timers, intervals):
            if timer is None:
                continue
            if active:
                if not timer.isActive():
                    timer.start(interval)
            else:
                timer.stop()

        control_buttons = getattr(self, "control_buttons_layout", None)
        status_timer = getattr(control_buttons, "status_update_timer", None)
        if status_timer is not None:
            if active:
                if not status_timer.isActive():
                    status_timer.start(1000)
            else:
                status_timer.stop()

        # The history widgets filter every mouse press in the application;
        # take them out of the chain while the docker is not visible.
        for history in (self.color_history_widget, self.brush_history_widget):
            if history is not None:
                history.set_filter_active(active)

        if active:
            self.force_update()

    def force_update(self):
        """Force update from current brush - can be called externally"""
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None
        self.current_brush_flow = None
        self.current_brush_rotation = None
        self.current_blend_mode = None
        self.update_from_current_brush()
        if self.color_history_widget is not None:
            self.color_history_widget.force_color_update()
        if self.brush_history_widget is not None:
            self.brush_history_widget.force_brush_update()

    def update_docker_size(self):
        # Relayouting the whole parent chain twice a second is expensive and
        # makes the docker flicker, so bail out unless the content actually
        # wants a different size than last time.
        size_hint = self.sizeHint()
        if size_hint == getattr(self, "_last_size_hint", None):
            return
        self._last_size_hint = size_hint

        self.updateGeometry()
        self.adjustSize()

        parent_widget = self.parent()
        while parent_widget:
            parent_widget.updateGeometry()
            if hasattr(parent_widget, "layout") and parent_widget.layout():
                parent_widget.layout().invalidate()
                parent_widget.layout().activate()

            if isinstance(parent_widget, QDockWidget):
                parent_widget.updateGeometry()
                parent_widget.adjustSize()

                main_widget = parent_widget.widget()
                if main_widget:
                    main_widget.updateGeometry()
                    main_widget.adjustSize()
                break
            parent_widget = parent_widget.parent()

    def closeEvent(self, event):
        """Stop every timer, event filter, and notifier connection we own."""
        self.set_monitoring_active(False)
        if self.control_buttons_layout is not None:
            self.control_buttons_layout.cleanup()
            if self.control_buttons_layout.float_tool_options is not None:
                self.control_buttons_layout.float_tool_options.close()
            if self.control_buttons_layout.float_rotation is not None:
                self.control_buttons_layout.float_rotation.close()
        super().closeEvent(event)
