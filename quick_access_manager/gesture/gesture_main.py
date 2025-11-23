"""
Main gesture system for Krita plugin.
Handles key+mouse gesture detection and execution.
"""

import json
import os
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import QApplication
from krita import Krita  # type: ignore
from .gesture_actions import execute_gesture
from ..utils.logs import write_log


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
        self.threshold = 20  # Minimum pixels to move before registering a gesture
        self.event_filter_installed = False
        self.window_created_connected = False

        # Gesture uses pen hover mode - tracks pen movement without touching tablet
        # When gesture key is pressed, starts tracking immediately
        # When gesture key is released, executes the gesture based on direction

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

    def install_event_filter(self):
        """Install event filter to capture key and mouse events"""
        if self.event_filter_installed:
            return

        try:
            app = Krita.instance()
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()
                if main_window:
                    QApplication.instance().installEventFilter(self)
                    self.event_filter_installed = True
                    write_log("✅ Gesture event filter installed")
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
        if self.event_filter_installed:
            try:
                QApplication.instance().removeEventFilter(self)
                self.event_filter_installed = False
                write_log("Gesture event filter uninstalled")
            except Exception as e:
                write_log(f"Error uninstalling event filter: {e}")

    def eventFilter(self, _obj, event):
        """Filter events to detect key+mouse gestures"""
        try:
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
                    write_log(f"Gesture key '{key_text}' pressed")
                    write_log(f"Current Gesture Configs: {self.gesture_configs}")

                    # Start gesture immediately using current cursor position
                    if not self.gesture_active:
                        from PyQt5.QtGui import QCursor

                        self.start_gesture(QCursor.pos())

            # Key release - deactivate gesture
            elif event_type == QEvent.KeyRelease:
                key_text = event.text().upper()
                if not key_text:
                    # Handle special keys
                    key = event.key()
                    if key >= Qt.Key_F1 and key <= Qt.Key_F12:
                        key_text = f"F{key - Qt.Key_F1 + 1}"

                if key_text and key_text == self.active_key:
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

        # Always pass events through
        return False

    def start_gesture(self, pos):
        """Start tracking a gesture"""
        self.gesture_active = True
        self.start_pos = pos
        self.last_pos = pos
        write_log(f"Gesture started at {pos}")

    def update_gesture(self, pos):
        """Update gesture tracking with new mouse position"""
        self.last_pos = pos

    def cancel_gesture(self):
        """Cancel the current gesture"""
        self.gesture_active = False
        self.active_key = None
        self.start_pos = None
        self.last_pos = None

    def execute_current_gesture(self):
        """Determine gesture direction and execute corresponding action"""
        if not self.gesture_active or not self.start_pos or not self.last_pos:
            self.cancel_gesture()
            return

        # Calculate movement
        dx = self.last_pos.x() - self.start_pos.x()
        dy = self.last_pos.y() - self.start_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5

        write_log(f"Gesture: dx={dx}, dy={dy}, distance={distance}")

        # Check if movement is significant enough
        if distance < self.threshold:
            write_log(f"Gesture too small (threshold: {self.threshold})")
            # Execute center action if configured
            if self.active_key in self.gesture_configs:
                gesture_map = self.gesture_configs[self.active_key]
                if "center" in gesture_map:
                    gesture_config = gesture_map["center"]
                    write_log(f"Executing center action: {gesture_config}")
                    execute_gesture(gesture_config)
                else:
                    write_log("No center action configured")
            self.cancel_gesture()
            return

        # Determine direction based on angle
        direction = self.calculate_direction(dx, dy)
        write_log(f"Gesture direction: {direction}")

        # Get gesture config for this key and direction
        if self.active_key in self.gesture_configs:
            gesture_map = self.gesture_configs[self.active_key]
            if direction in gesture_map:
                gesture_config = gesture_map[direction]
                write_log(f"Executing gesture: {gesture_config}")
                execute_gesture(gesture_config)
            else:
                write_log(f"No gesture configured for direction: {direction}")
        else:
            write_log(f"No gesture config for key: {self.active_key}")

        # Reset gesture state
        self.cancel_gesture()

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


# Global gesture manager instance
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
