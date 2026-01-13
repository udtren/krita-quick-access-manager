"""
Layer state monitoring and control functionality.
"""

from PyQt5.QtCore import QTimer
from krita import Krita  # type: ignore


class LayerMonitorMixin:
    """
    Mixin class providing layer monitoring and control methods.
    Should be mixed into BrushAdjustmentWidget.
    """

    def setup_layer_monitoring(self):
        """Initialize layer monitoring timers and state"""
        # State tracking
        self.current_layer_opacity = None
        self.current_layer_blend_mode = None
        self.updating_from_layer = False

        # Debounce timer
        self.layer_opacity_debounce_timer = QTimer()
        self.layer_opacity_debounce_timer.setSingleShot(True)
        self.layer_opacity_debounce_timer.timeout.connect(
            self.apply_layer_opacity_change
        )

        # Pending value
        self.pending_layer_opacity_value = None

        # Periodic check timer
        self.layer_check_timer = QTimer()
        self.layer_check_timer.timeout.connect(self.check_layer_change)
        self.layer_check_timer.start(200)

    def check_layer_change(self):
        """Check if the current layer has changed and update sliders if needed"""
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

        # Check if layer properties changed
        layer_opacity_changed = current_layer_opacity != self.current_layer_opacity
        layer_blend_changed = current_layer_blend_mode != self.current_layer_blend_mode

        if layer_opacity_changed or layer_blend_changed:
            self.current_layer_opacity = current_layer_opacity
            self.current_layer_blend_mode = current_layer_blend_mode
            self.update_from_current_layer()

    def update_from_current_layer(self):
        """Update sliders to match current layer settings"""
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

    def on_layer_blend_mode_changed(self, text):
        """Handle layer blend mode change"""
        if self.updating_from_layer or self.layer_blend_combo is None:
            return

        # Get the blend mode data from the combo box
        layer_blend_mode = self.layer_blend_combo.currentData()
        if layer_blend_mode:
            self.current_layer_blend_mode = layer_blend_mode

            app = Krita.instance()
            activeDoc = app.activeDocument()
            activeNode = activeDoc.activeNode() if activeDoc else None
            if activeNode:
                try:
                    activeNode.setBlendingMode(layer_blend_mode)
                    activeDoc.refreshProjection()
                    print(f"Set layer blend mode to: {layer_blend_mode}")
                except Exception as e:
                    print(f"Error setting layer blend mode: {e}")
