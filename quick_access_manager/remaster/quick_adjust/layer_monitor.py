"""
Layer state monitoring and control functionality.
"""

from krita import Krita  # type: ignore

from ..compat import QTimer


class LayerMonitorMixin:
    """Mixin providing layer monitoring and control methods for BrushAdjustmentWidget."""

    def setup_layer_monitoring(self):
        self.current_layer_opacity = None
        self.current_layer_blend_mode = None
        self.updating_from_layer = False

        self.layer_opacity_debounce_timer = QTimer()
        self.layer_opacity_debounce_timer.setSingleShot(True)
        self.layer_opacity_debounce_timer.timeout.connect(
            self.apply_layer_opacity_change
        )

        self.pending_layer_opacity_value = None

        self.layer_check_timer = QTimer()
        self.layer_check_timer.timeout.connect(self.check_layer_change)
        self.layer_check_timer.start(200)

    def check_layer_change(self):
        app = Krita.instance()

        current_layer_opacity = None
        current_layer_blend_mode = None

        try:
            if app.activeDocument() and app.activeDocument().activeNode():
                current_layer_opacity = app.activeDocument().activeNode().opacity()
        except Exception:
            pass

        try:
            if app.activeDocument() and app.activeDocument().activeNode():
                current_layer_blend_mode = (
                    app.activeDocument().activeNode().blendingMode()
                )
        except Exception:
            pass

        layer_opacity_changed = current_layer_opacity != self.current_layer_opacity
        layer_blend_changed = current_layer_blend_mode != self.current_layer_blend_mode

        if layer_opacity_changed or layer_blend_changed:
            self.current_layer_opacity = current_layer_opacity
            self.current_layer_blend_mode = current_layer_blend_mode
            self.update_from_current_layer()

    def update_from_current_layer(self):
        if self.updating_from_layer:
            return

        app = Krita.instance()
        self.updating_from_layer = True

        if self.layer_opacity_slider is not None:
            try:
                active_node = (
                    app.activeDocument().activeNode() if app.activeDocument() else None
                )
                if active_node:
                    layer_opacity = active_node.opacity()
                    layer_opacity_percent = int(layer_opacity * 100 / 255)
                    self.layer_opacity_slider.setValue(layer_opacity_percent)
                    self.layer_opacity_value_label.setText(f"{layer_opacity_percent}%")
                    self.current_layer_opacity = layer_opacity
            except Exception:
                self.layer_opacity_slider.setValue(100)
                self.layer_opacity_value_label.setText("100%")
                self.current_layer_opacity = 255

        if self.layer_blend_combo is not None:
            try:
                active_node = (
                    app.activeDocument().activeNode() if app.activeDocument() else None
                )
                if active_node:
                    layer_blend_mode = active_node.blendingMode()
                    if layer_blend_mode:
                        index = self.layer_blend_combo.findData(layer_blend_mode)
                        if index >= 0:
                            self.layer_blend_combo.setCurrentIndex(index)
                        else:
                            self.layer_blend_combo.addItem(
                                layer_blend_mode.replace("_", " ").title(),
                                layer_blend_mode,
                            )
                            self.layer_blend_combo.setCurrentIndex(
                                self.layer_blend_combo.count() - 1
                            )
                        self.current_layer_blend_mode = layer_blend_mode
            except Exception:
                self.layer_blend_combo.setCurrentIndex(0)
                self.current_layer_blend_mode = "normal"
        self.updating_from_layer = False

    def on_layer_opacity_changed_debounced(self, value):
        if self.updating_from_layer or self.layer_opacity_slider is None:
            return
        self.layer_opacity_value_label.setText(f"{value}%")
        self.pending_layer_opacity_value = value
        self.layer_opacity_debounce_timer.start(300)

    def apply_layer_opacity_change(self):
        if self.pending_layer_opacity_value is None:
            return
        value = self.pending_layer_opacity_value
        opacity_int = int(value * 255 / 100)
        self.current_layer_opacity = opacity_int

        app = Krita.instance()
        active_doc = app.activeDocument()
        active_node = active_doc.activeNode() if active_doc else None
        if active_node:
            try:
                active_node.setOpacity(opacity_int)
                active_doc.refreshProjection()
            except Exception as e:
                print(f"Error setting layer opacity: {e}")

    def on_layer_blend_mode_changed(self, text):
        if self.updating_from_layer or self.layer_blend_combo is None:
            return

        layer_blend_mode = self.layer_blend_combo.currentData()
        if layer_blend_mode:
            self.current_layer_blend_mode = layer_blend_mode

            app = Krita.instance()
            active_doc = app.activeDocument()
            active_node = active_doc.activeNode() if active_doc else None
            if active_node:
                try:
                    active_node.setBlendingMode(layer_blend_mode)
                    active_doc.refreshProjection()
                except Exception as e:
                    print(f"Error setting layer blend mode: {e}")
