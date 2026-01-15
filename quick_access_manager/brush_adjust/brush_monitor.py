"""
Brush state monitoring and control functionality.
"""

from PyQt5.QtCore import QTimer
from krita import Krita  # type: ignore

from .utils_adjust import slider_to_brush_size, brush_size_to_slider


class BrushMonitorMixin:
    """
    Mixin class providing brush monitoring and control methods.
    Should be mixed into BrushAdjustmentWidget.
    """

    def setup_brush_monitoring(self):
        """Initialize brush monitoring timers and state"""
        # State tracking
        self.current_brush_name = None
        self.current_brush_size = None
        self.current_brush_opacity = None
        self.current_brush_flow = None
        self.current_brush_rotation = None
        self.current_blend_mode = None
        self.updating_from_brush = False

        # Debounce timers
        self.opacity_debounce_timer = QTimer()
        self.opacity_debounce_timer.setSingleShot(True)
        self.opacity_debounce_timer.timeout.connect(self.apply_opacity_change)

        self.size_debounce_timer = QTimer()
        self.size_debounce_timer.setSingleShot(True)
        self.size_debounce_timer.timeout.connect(self.apply_size_change)

        self.flow_debounce_timer = QTimer()
        self.flow_debounce_timer.setSingleShot(True)
        self.flow_debounce_timer.timeout.connect(self.apply_flow_change)

        # Pending values
        self.pending_opacity_value = None
        self.pending_size_value = None
        self.pending_flow_value = None

        # Periodic check timer
        self.brush_check_timer = QTimer()
        self.brush_check_timer.timeout.connect(self.check_brush_change)
        self.brush_check_timer.start(200)

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
                    current_flow = None
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
                        current_flow = view.paintingFlow()
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
                    self.size_slider.setValue(brush_size_to_slider(int(size)))
                    self.size_value_label.setText(str(int(size)))
                    self.current_brush_size = size
                except:
                    # Fallback to default if brushSize() doesn't work
                    self.size_slider.setValue(brush_size_to_slider(10))
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

            # Get current flow
            if self.flow_slider is not None:
                try:
                    flow = view.paintingFlow()
                    flow_percent = int(flow * 100)  # Convert from 0-1 to 0-100
                    self.flow_slider.setValue(flow_percent)
                    self.flow_value_label.setText(f"{flow_percent}%")
                    self.current_brush_flow = flow
                except:
                    # Fallback if flow method doesn't work
                    self.flow_slider.setValue(100)
                    self.flow_value_label.setText("100%")
                    self.current_brush_flow = 1.0

            # Get brush rotation
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

        brush_size = slider_to_brush_size(slider_value)

        # Update UI immediately
        self.size_value_label.setText(str(brush_size))

        # Store pending value
        self.pending_size_value = brush_size

        # Restart timer (300ms delay)
        self.size_debounce_timer.start(300)

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

    def on_flow_changed_debounced(self, value):
        """Handle flow slider with debouncing"""
        if self.updating_from_brush or self.flow_slider is None:
            return

        # Update UI immediately for responsive feel
        self.flow_value_label.setText(f"{value}%")

        # Store the pending value
        self.pending_flow_value = value

        # Restart timer (300ms delay)
        self.flow_debounce_timer.start(300)

    def apply_flow_change(self):
        """Apply the pending flow change to Krita"""
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
        """Handle brush rotation change"""
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
        """Handle blend mode change"""
        if self.updating_from_brush or self.blend_combo is None:
            return

        # Get the blend mode data from the combo box
        blend_mode = self.blend_combo.currentData()
        if blend_mode:
            self.current_blend_mode = blend_mode

            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                try:
                    view.setCurrentBlendingMode(blend_mode)
                    print(f"Set blend mode to: {blend_mode}")
                except Exception as e:
                    print(f"Error setting blend mode: {e}")

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
            self.current_brush_flow = None
            self.current_brush_rotation = None
            self.current_blend_mode = None

            # Update UI after a short delay to let Krita finish the reload
            QTimer.singleShot(150, self.update_from_current_brush)

        except Exception as e:
            print(f"Error triggering reload_preset_action: {e}")
            # Fallback - just refresh the UI
            self.update_from_current_brush()
