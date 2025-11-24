"""
Main gesture system for Krita plugin.
Handles key+mouse gesture detection and execution.
"""

import json
import os
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCursor
from krita import Krita  # type: ignore
from .gesture_actions import execute_gesture
from .widgets.gesture_preview import GesturePreviewWidget
from ..utils.logs import write_log


# ==================================================================
# Gesture Detector Class
# ==================================================================
class GestureDetector(QObject):
    """
    Detects and executes key+mouse gestures.
    Tracks mouse movement while a key is held and mouse button is pressed.
    """

    def __init__(self):
        super().__init__()
        self.gesture_configs = {}  # {key: {direction: gesture_config}}
        self.active_key = None
        self.gesture_active = False
        self.start_pos = None
        self.last_pos = None
        self.threshold = 20  # Default minimum pixels, will be loaded from settings
        self.show_preview = True  # Whether to show preview widget, loaded from settings
        self.event_filter_installed = False
        self.window_created_connected = False
        self.config_dialog_active = False  # Track if config dialog is open
        self.event_filter_call_count = 0  # Track eventFilter calls to detect recursion
        self.max_event_filter_depth = 0  # Track max recursion depth
        self.preview_widget = None  # Preview widget for showing gestures (lazy init)
        self.load_settings()

    def load_gesture_configs(self):
        """Load all gesture configurations from config directory"""
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        if not os.path.exists(config_dir):
            write_log("Gesture config directory not found")
            return

        # Clear existing configs
        self.gesture_configs = {}

        # Find all JSON files (excluding gesture.json which is for settings)
        json_files = [
            f
            for f in os.listdir(config_dir)
            if f.endswith(".json") and f != "gesture.json"
        ]

        for json_file in sorted(json_files):
            config_path = os.path.join(config_dir, json_file)
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Get gesture key
                gesture_key = config_data.get("gesture_key", "").upper()
                if not gesture_key:
                    write_log(f"No gesture_key in {json_file}, skipping")
                    continue

                # Check if this key is already registered
                if gesture_key in self.gesture_configs:
                    write_log(
                        f"Gesture key '{gesture_key}' already registered, skipping {json_file}"
                    )
                    continue

                # Extract gesture configurations for each direction
                gesture_map = {}
                directions = [
                    "left_up",
                    "up",
                    "right_up",
                    "left",
                    "right",
                    "left_down",
                    "down",
                    "right_down",
                    "center",
                ]

                for direction in directions:
                    if direction in config_data:
                        gesture_config = config_data[direction]
                        if gesture_config:  # Only add non-empty configurations
                            gesture_map[direction] = gesture_config

                if gesture_map:
                    self.gesture_configs[gesture_key] = gesture_map
                    write_log(
                        f"Loaded gesture config for key '{gesture_key}' from {json_file}"
                    )

            except Exception as e:
                write_log(f"Error loading gesture config {json_file}: {e}")

        write_log(f"Total gesture configs loaded: {len(self.gesture_configs)}")

    def load_settings(self):
        """Load settings from gesture.json (threshold and preview flag)"""
        try:
            settings_path = os.path.join(os.path.dirname(__file__), "gesture.json")
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.threshold = settings.get("minimum_pixels_to_move", 20)
                    self.show_preview = settings.get("show_preview", True)
                    write_log(
                        f"Loaded settings - threshold: {self.threshold}, show_preview: {self.show_preview}"
                    )
            else:
                write_log(
                    "No gesture.json found, using defaults: threshold=20, show_preview=True"
                )
        except Exception as e:
            write_log(f"Error loading settings: {e}")

    # ==================================================================
    # Event Filter Installation and Handling
    # ==================================================================
    def install_event_filter(self):
        """Install event filter to capture key and mouse events"""
        if self.event_filter_installed:
            write_log("⚠️ Event filter already installed, skipping")
            return

        try:
            app = Krita.instance()
            write_log(f"Installing event filter... App: {app}")
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()
                write_log(f"Main window: {main_window}")
                if main_window:
                    QApplication.instance().installEventFilter(self)
                    self.event_filter_installed = True
                    write_log("✅ Gesture event filter installed successfully")
                    write_log(f"Event filter object: {self}")
                else:
                    write_log("⚠️ Could not get main window for event filter")
            else:
                # No active window yet - wait for windowCreated signal
                if not self.window_created_connected:
                    write_log(
                        "⏳ No active window yet, waiting for windowCreated signal..."
                    )
                    appNotifier = app.notifier()
                    appNotifier.windowCreated.connect(self._on_window_created)
                    self.window_created_connected = True
        except Exception as e:
            write_log(f"❌ Error installing event filter: {e}")

    def _on_window_created(self):
        """Called when a Krita window is created"""
        write_log("🔔 Window created signal received")
        try:
            # Disconnect the signal to avoid multiple calls
            app = Krita.instance()
            if self.window_created_connected:
                appNotifier = app.notifier()
                try:
                    appNotifier.windowCreated.disconnect(self._on_window_created)
                except:
                    pass  # Already disconnected
                self.window_created_connected = False

            # Now try to install the event filter
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()
                if main_window:
                    QApplication.instance().installEventFilter(self)
                    self.event_filter_installed = True
                    write_log("✅ Gesture event filter installed after window created")
                else:
                    write_log("⚠️ Still could not get main window")
            else:
                write_log("⚠️ No active window in windowCreated callback")
        except Exception as e:
            write_log(f"❌ Error in windowCreated callback: {e}")

    def uninstall_event_filter(self):
        """Uninstall event filter"""
        write_log(
            f"Attempting to uninstall event filter. Installed: {self.event_filter_installed}"
        )
        if self.event_filter_installed:
            try:
                QApplication.instance().removeEventFilter(self)
                self.event_filter_installed = False
                # Clean up preview widget if it exists
                if self.preview_widget is not None:
                    self.preview_widget.hide_preview()
                    self.preview_widget.deleteLater()
                    self.preview_widget = None
                write_log("✅ Gesture event filter uninstalled successfully")
                write_log(
                    f"Max recursion depth reached during session: {self.max_event_filter_depth}"
                )
            except Exception as e:
                write_log(f"Error uninstalling event filter: {e}")

    # ==================================================================

    # ==================================================================
    # Gesture Pasuse/Resume API
    # ==================================================================

    def pause_event_filter(self):
        """Pause event filtering by removing the filter (API for external use)"""
        if self.event_filter_installed:
            try:
                QApplication.instance().removeEventFilter(self)
                self.event_filter_installed = False
                write_log("⏸️ Gesture event filter paused (removed from QApplication)")
            except Exception as e:
                write_log(f"Error pausing event filter: {e}")
        else:
            write_log("⚠️ Event filter not installed, cannot pause")

    def resume_event_filter(self):
        """Resume event filtering by re-installing the filter (API for external use)"""
        if not self.event_filter_installed:
            try:
                app = Krita.instance()
                if app.activeWindow():
                    main_window = app.activeWindow().qwindow()
                    if main_window:
                        QApplication.instance().installEventFilter(self)
                        self.event_filter_installed = True
                        write_log(
                            "▶️ Gesture event filter resumed (re-installed to QApplication)"
                        )
                    else:
                        write_log("⚠️ Cannot resume: No main window available")
                else:
                    write_log("⚠️ Cannot resume: No active window")
            except Exception as e:
                write_log(f"Error resuming event filter: {e}")
        else:
            write_log("⚠️ Event filter already installed, cannot resume")

    # ==================================================================

    # ==================================================================
    # Gesture Detection and Execution
    # ==================================================================

    def eventFilter(self, _obj, event):
        """Filter events to detect key+mouse gestures"""
        # Track recursion depth
        self.event_filter_call_count += 1
        current_depth = self.event_filter_call_count

        # Detect potential stack overflow
        if current_depth > self.max_event_filter_depth:
            self.max_event_filter_depth = current_depth
            if current_depth > 10:
                write_log(f"⚠️ WARNING: eventFilter recursion depth: {current_depth}")

        if current_depth > 100:
            write_log(
                f"🔴 CRITICAL: eventFilter recursion depth exceeded 100! Depth: {current_depth}"
            )
            self.event_filter_call_count -= 1
            return False

        try:
            # Ignore events when config dialog is active
            if self.config_dialog_active:
                self.event_filter_call_count -= 1
                return False

            event_type = event.type()

            # Key press - check if it's a gesture key
            if event_type == QEvent.KeyPress:
                key_text = event.text().upper()
                if not key_text:
                    # Handle special keys
                    key = event.key()
                    if key >= Qt.Key_F1 and key <= Qt.Key_F12:
                        key_text = f"F{key - Qt.Key_F1 + 1}"

                if key_text and key_text in self.gesture_configs:
                    self.active_key = key_text
                    # write_log(f"Gesture key '{key_text}' pressed")
                    # write_log(f"Current Gesture Configs: {self.gesture_configs}")

                    # Start gesture immediately using current cursor position
                    if not self.gesture_active:
                        cursor_pos = QCursor.pos()
                        self.start_gesture(cursor_pos)

                        # Show preview widget if enabled
                        if self.show_preview:
                            # Lazy initialization of preview widget
                            if self.preview_widget is None:
                                self.preview_widget = GesturePreviewWidget()

                            gesture_map = self.gesture_configs[key_text]
                            self.preview_widget.show_preview(gesture_map, cursor_pos)

            # Key release - deactivate gesture
            elif event_type == QEvent.KeyRelease:
                key_text = event.text().upper()
                if not key_text:
                    # Handle special keys
                    key = event.key()
                    if key >= Qt.Key_F1 and key <= Qt.Key_F12:
                        key_text = f"F{key - Qt.Key_F1 + 1}"

                if key_text and key_text == self.active_key:
                    # Hide preview widget if it exists
                    if self.preview_widget is not None:
                        self.preview_widget.hide_preview()

                    # Execute gesture on key release
                    if self.gesture_active:
                        self.execute_current_gesture()
                    else:
                        self.cancel_gesture()

            # Mouse/Pen move - track movement while gesture is active
            elif event_type == QEvent.MouseMove:
                if self.gesture_active and self.active_key:
                    self.update_gesture(event.globalPos())

        except Exception as e:
            write_log(f"Error in eventFilter: {e}")
            import traceback

            traceback.print_exc()
        finally:
            # Always decrement counter when exiting
            self.event_filter_call_count -= 1

        # Always pass events through
        return False

    # ==================================================================

    # ==================================================================
    # Gesture Tracking and Execution
    # ==================================================================
    def calculate_direction(self, dx, dy):
        """
        Calculate gesture direction based on movement.

        Returns one of: 'left_up', 'up', 'right_up', 'left', 'right',
                        'left_down', 'down', 'right_down'
        """
        import math

        # Calculate angle in degrees (0 = right, 90 = up, 180 = left, 270 = down)
        angle = math.degrees(
            math.atan2(-dy, dx)
        )  # Negative dy because Y increases downward
        if angle < 0:
            angle += 360

        # Map angles to 8 directions
        # Each direction covers 45 degrees (360/8)
        # Right: -22.5 to 22.5 (337.5 to 360, 0 to 22.5)
        # Right-Up: 22.5 to 67.5
        # Up: 67.5 to 112.5
        # Left-Up: 112.5 to 157.5
        # Left: 157.5 to 202.5
        # Left-Down: 202.5 to 247.5
        # Down: 247.5 to 292.5
        # Right-Down: 292.5 to 337.5

        if angle >= 337.5 or angle < 22.5:
            return "right"
        elif angle < 67.5:
            return "right_up"
        elif angle < 112.5:
            return "up"
        elif angle < 157.5:
            return "left_up"
        elif angle < 202.5:
            return "left"
        elif angle < 247.5:
            return "left_down"
        elif angle < 292.5:
            return "down"
        else:  # 292.5 to 337.5
            return "right_down"

    def start_gesture(self, pos):
        """Start tracking a gesture"""
        self.gesture_active = True
        self.start_pos = pos
        self.last_pos = pos
        # write_log(f"Gesture started at {pos}")

    def update_gesture(self, pos):
        """Update gesture tracking with new mouse position"""
        self.last_pos = pos

    def cancel_gesture(self):
        """Cancel the current gesture"""
        self.gesture_active = False
        self.active_key = None
        self.start_pos = None
        self.last_pos = None
        # Hide preview if still showing
        if self.preview_widget is not None:
            self.preview_widget.hide_preview()

    def execute_current_gesture(self):
        """Determine gesture direction and execute corresponding action"""
        if not self.gesture_active or not self.start_pos or not self.last_pos:
            self.cancel_gesture()
            return

        # Calculate movement
        dx = self.last_pos.x() - self.start_pos.x()
        dy = self.last_pos.y() - self.start_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5

        # write_log(f"Gesture: dx={dx}, dy={dy}, distance={distance}")

        # Check if movement is significant enough
        if distance < self.threshold:
            # write_log(f"Gesture too small (threshold: {self.threshold})")
            # Execute center action if configured
            if self.active_key in self.gesture_configs:
                gesture_map = self.gesture_configs[self.active_key]
                if "center" in gesture_map:
                    gesture_config = gesture_map["center"]
                    # write_log(f"Executing center action: {gesture_config}")
                    execute_gesture(gesture_config)
                else:
                    # write_log("No center action configured")
                    pass
            self.cancel_gesture()
            return

        # Determine direction based on angle
        direction = self.calculate_direction(dx, dy)
        # write_log(f"Gesture direction: {direction}")

        # Get gesture config for this key and direction
        if self.active_key in self.gesture_configs:
            gesture_map = self.gesture_configs[self.active_key]
            if direction in gesture_map:
                gesture_config = gesture_map[direction]
                # write_log(f"Executing gesture: {gesture_config}")
                execute_gesture(gesture_config)
            else:
                write_log(f"No gesture configured for direction: {direction}")
        else:
            write_log(f"No gesture config for key: {self.active_key}")

        # Reset gesture state
        self.cancel_gesture()

    # ==================================================================

    # ==================================================================
    # Configuration Dialog State Management
    # ==================================================================
    def set_config_dialog_active(self, active):
        """Set whether config dialog is currently active"""
        self.config_dialog_active = active
        write_log(f"Config dialog active state: {active}")

    def enable_gesture_preview(self, enable):
        """Enable or disable gesture preview widget"""
        self.show_preview = enable
        write_log(f"Gesture preview enabled: {enable}")


# ==================================================================
# Gesture Manager Singleton and API Functions
# ==================================================================
class GestureManager:
    """
    Manager for the gesture system.
    Handles initialization, registration, and lifecycle.
    """

    def __init__(self):
        self.detector = None

    def initialize(self):
        """Initialize the gesture system"""
        if self.detector is None:
            self.detector = GestureDetector()
            self.detector.load_gesture_configs()
            self.detector.install_event_filter()
            write_log("Gesture system initialized")

    def reload_configs(self):
        """Reload gesture configurations (call this after saving config dialog)"""
        if self.detector:
            write_log("Reloading gesture configurations...")
            self.detector.load_gesture_configs()
        else:
            write_log("Gesture detector not initialized")

    def shutdown(self):
        """Shutdown the gesture system"""
        if self.detector:
            self.detector.uninstall_event_filter()
            self.detector = None
            write_log("Gesture system shutdown")


# ==================================================================
# Global Gesture Manager Instance and API Functions
# ==================================================================

_gesture_manager = None


def get_gesture_manager():
    """Get the global gesture manager instance"""
    global _gesture_manager
    if _gesture_manager is None:
        _gesture_manager = GestureManager()
    return _gesture_manager


def initialize_gesture_system():
    """Initialize the gesture system (call on plugin load)"""
    manager = get_gesture_manager()
    manager.initialize()


def reload_gesture_configs():
    """Reload gesture configurations (call after saving config dialog)"""
    manager = get_gesture_manager()
    manager.reload_configs()


def shutdown_gesture_system():
    """Shutdown the gesture system (call on plugin unload)"""
    manager = get_gesture_manager()
    manager.shutdown()


def set_config_dialog_active(active):
    """Set whether config dialog is active (disables gesture detection)"""
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.set_config_dialog_active(active)


def pause_gesture_event_filter():
    """
    Pause the gesture event filter (API for external use).
    Call this before operations that might trigger many events.
    """
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.pause_event_filter()
    else:
        write_log("⚠️ Cannot pause: Gesture detector not initialized")


def resume_gesture_event_filter():
    """
    Resume the gesture event filter (API for external use).
    Call this after operations that required the filter to be paused.
    """
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.resume_event_filter()
    else:
        write_log("⚠️ Cannot resume: Gesture detector not initialized")


def is_gesture_filter_paused():
    """
    Check if the gesture event filter is currently paused (not installed).
    Returns True if paused (not installed), False if active (installed), None if detector not initialized.
    """
    manager = get_gesture_manager()
    if manager.detector:
        return not manager.detector.event_filter_installed
    return None


def is_gesture_enabled():
    """Check if gesture system is enabled in settings"""
    import os

    # gesture.json is now in the gesture folder, not in config subfolder
    gesture_dir = os.path.dirname(__file__)
    settings_path = os.path.join(gesture_dir, "gesture.json")

    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("enabled", True)
    except Exception as e:
        write_log(f"Error reading gesture settings: {e}")

    return True  # Default to enabled


def enable_gesture_preview(enable):
    """Enable or disable gesture preview widget"""
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.enable_gesture_preview(enable)
    else:
        write_log("⚠️ Cannot set preview: Gesture detector not initialized")
