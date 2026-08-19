"""
Brush state monitoring and control functionality.
"""

from krita import Krita  # type: ignore

from ..compat import QTimer
from .utils_adjust import brush_size_to_slider, slider_to_brush_size


class BrushMonitorMixin:
    """Mixin providing brush monitoring and control methods for BrushAdjustmentWidget."""

    def setup_brush_monitoring(self):
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None
        self.current_brush_flow = None
        self.current_brush_rotation = None
        self.current_blend_mode = None
        self.updating_from_brush = False

        self.opacity_debounce_timer = QTimer()
        self.opacity_debounce_timer.setSingleShot(True)
        self.opacity_debounce_timer.timeout.connect(self.apply_opacity_change)

        self.size_debounce_timer = QTimer()
        self.size_debounce_timer.setSingleShot(True)
        self.size_debounce_timer.timeout.connect(self.apply_size_change)

        self.flow_debounce_timer = QTimer()
        self.flow_debounce_timer.setSingleShot(True)
        self.flow_debounce_timer.timeout.connect(self.apply_flow_change)

        self.pending_opacity_value = None
        self.pending_size_value = None
        self.pending_flow_value = None

        self.brush_check_timer = QTimer()
        self.brush_check_timer.timeout.connect(self.check_brush_change)
        self.brush_check_timer.start(200)

    def check_brush_change(self):
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                current_preset = view.currentBrushPreset()
                if current_preset:
                    brush_name = current_preset.name()

                    current_size = None
                    current_opacity = None
                    current_flow = None
                    current_rotation = None
                    current_blend_mode = None

                    try:
                        current_size = view.brushSize()
                    except Exception:
                        pass
                    try:
                        current_opacity = view.paintingOpacity()
                    except Exception:
                        pass
                    try:
                        current_flow = view.paintingFlow()
                    except Exception:
                        pass
                    try:
                        current_rotation = view.brushRotation()
                    except Exception:
                        pass
                    try:
                        current_blend_mode = view.currentBlendingMode()
                    except Exception:
                        pass

                    brush_changed = brush_name != self.current_brush_name
                    size_changed = current_size != self.current_brush_size
                    opacity_changed = current_opacity != self.current_brush_opacity
                    flow_changed = current_flow != self.current_brush_flow
                    rotation_changed = current_rotation != self.current_brush_rotation
                    blend_changed = current_blend_mode != self.current_blend_mode

                    if (
                        brush_changed
                        or size_changed
                        or opacity_changed
                        or flow_changed
                        or rotation_changed
                        or blend_changed
                    ):
                        self.current_brush_name = brush_name
                        self.current_brush_size = current_size
                        self.current_brush_opacity = current_opacity
                        self.current_brush_flow = current_flow
                        self.current_brush_rotation = current_rotation
                        self.current_blend_mode = current_blend_mode
                        self.update_from_current_brush()
            except Exception:
                pass

    def update_from_current_brush(self):
        if self.updating_from_brush:
            return

        self.updating_from_brush = True

        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()

            if self.size_slider is not None:
                try:
                    size = view.brushSize()
                    self.size_slider.setValue(brush_size_to_slider(int(size)))
                    self.size_value_label.setText(str(int(size)))
                    self.current_brush_size = size
                except Exception:
                    self.size_slider.setValue(brush_size_to_slider(10))
                    self.size_value_label.setText("10")
                    self.current_brush_size = 10

            if self.opacity_slider is not None:
                try:
                    opacity = view.paintingOpacity()
                    opacity_percent = int(opacity * 100)
                    self.opacity_slider.setValue(opacity_percent)
                    self.opacity_value_label.setText(f"{opacity_percent}%")
                    self.current_brush_opacity = opacity
                except Exception:
                    self.opacity_slider.setValue(100)
                    self.opacity_value_label.setText("100%")
                    self.current_brush_opacity = 1.0

            if self.flow_slider is not None:
                try:
                    flow = view.paintingFlow()
                    flow_percent = int(flow * 100)
                    self.flow_slider.setValue(flow_percent)
                    self.flow_value_label.setText(f"{flow_percent}%")
                    self.current_brush_flow = flow
                except Exception:
                    self.flow_slider.setValue(100)
                    self.flow_value_label.setText("100%")
                    self.current_brush_flow = 1.0

            if self.rotation_widget is not None:
                try:
                    rotation = view.brushRotation()
                    self.rotation_widget.setValue(int(rotation))
                    self.rotation_value_label.setText(f"{int(rotation)}°")
                    self.current_brush_rotation = rotation
                except Exception:
                    self.rotation_widget.setValue(0)
                    self.rotation_value_label.setText("0°")
                    self.current_brush_rotation = 0

            if self.blend_combo is not None:
                try:
                    blend_mode = view.currentBlendingMode()
                    if blend_mode:
                        index = self.blend_combo.findData(blend_mode)
                        if index >= 0:
                            self.blend_combo.setCurrentIndex(index)
                        else:
                            self.blend_combo.addItem(
                                blend_mode.replace("_", " ").title(), blend_mode
                            )
                            self.blend_combo.setCurrentIndex(
                                self.blend_combo.count() - 1
                            )
                        self.current_blend_mode = blend_mode
                except Exception:
                    self.blend_combo.setCurrentIndex(0)
                    self.current_blend_mode = "normal"

        self.updating_from_brush = False

    def on_opacity_changed_debounced(self, value):
        if self.updating_from_brush or self.opacity_slider is None:
            return
        self.opacity_value_label.setText(f"{value}%")
        self.pending_opacity_value = value
        self.opacity_debounce_timer.start(300)

    def on_size_slider_changed_debounced(self, slider_value):
        if self.updating_from_brush or self.size_slider is None:
            return
        brush_size = slider_to_brush_size(slider_value)
        self.size_value_label.setText(str(brush_size))
        self.pending_size_value = brush_size
        self.size_debounce_timer.start(300)

    def apply_size_change(self):
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

    def on_flow_changed_debounced(self, value):
        if self.updating_from_brush or self.flow_slider is None:
            return
        self.flow_value_label.setText(f"{value}%")
        self.pending_flow_value = value
        self.flow_debounce_timer.start(300)

    def apply_flow_change(self):
        if self.pending_flow_value is None:
            return
        value = self.pending_flow_value
        flow_float = value / 100.0
        self.current_brush_flow = flow_float
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                view.setPaintingFlow(flow_float)
            except Exception as e:
                print(f"Error setting brush flow: {e}")

    def on_rotation_changed(self, value):
        if self.updating_from_brush or self.rotation_widget is None:
            return
        self.rotation_value_label.setText(f"{value}°")
        self.current_brush_rotation = value
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                view.setBrushRotation(float(value))
            except Exception as e:
                print(f"Error setting brush rotation: {e}")

    def on_blend_mode_changed(self, text):
        if self.updating_from_brush or self.blend_combo is None:
            return
        blend_mode = self.blend_combo.currentData()
        if blend_mode:
            self.current_blend_mode = blend_mode
            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                try:
                    view.setCurrentBlendingMode(blend_mode)
                except Exception as e:
                    print(f"Error setting blend mode: {e}")

    def reset_brush_settings(self):
        """Reset brush settings by triggering Krita's reload preset action"""
        app = Krita.instance()
        try:
            app.action("reload_preset_action").trigger()

            self.current_brush_name = None
            self.current_brush_size = None
            self.current_brush_opacity = None
            self.current_brush_flow = None
            self.current_brush_rotation = None
            self.current_blend_mode = None

            QTimer.singleShot(150, self.update_from_current_brush)
        except Exception as e:
            print(f"Error triggering reload_preset_action: {e}")
            self.update_from_current_brush()
