"""
Main gesture system for the remastered plugin.
Handles key+mouse gesture detection and execution.
"""

import json
import math
import os

from krita import Krita  # type: ignore

from ..compat import QApplication, QCursor, QEvent, QObject, Qt
from ..infrastructure import get_gesture_data_dir
from .gesture_actions import execute_gesture
from .log_utils import write_log
from .widgets.gesture_preview import GesturePreviewWidget

_GESTURE_EVENT_TYPES = frozenset((QEvent.KeyPress, QEvent.KeyRelease, QEvent.MouseMove))


class GestureDetector(QObject):
    """Detects and executes key+mouse gestures.

    Tracks mouse movement while a key is held and mouse button is pressed.
    """

    def __init__(self):
        super().__init__()
        self.gesture_configs = {}  # {key: {direction: gesture_config}}
        self.active_key = None
        self.gesture_active = False
        self.start_pos = None
        self.last_pos = None
        self.threshold = 20
        self.show_preview = True
        self.event_filter_installed = False
        self.window_created_connected = False
        self.config_dialog_active = False
        self.event_filter_call_count = 0
        self.max_event_filter_depth = 0
        self.preview_widget = None
        self.load_settings()

    def load_gesture_configs(self):
        """Load all gesture configurations from config directory"""
        config_dir = os.path.join(get_gesture_data_dir(), "config")
        if not os.path.exists(config_dir):
            write_log("Gesture config directory not found")
            return

        self.gesture_configs = {}

        json_files = [
            f
            for f in os.listdir(config_dir)
            if f.endswith(".json") and f != "gesture.json"
        ]

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

        for json_file in sorted(json_files):
            config_path = os.path.join(config_dir, json_file)
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                gesture_key = config_data.get("gesture_key", "").upper()
                if not gesture_key:
                    write_log(f"No gesture_key in {json_file}, skipping")
                    continue

                if gesture_key in self.gesture_configs:
                    write_log(
                        f"Gesture key '{gesture_key}' already registered, skipping {json_file}"
                    )
                    continue

                gesture_map = {}
                for direction in directions:
                    if config_data.get(direction):
                        gesture_map[direction] = config_data[direction]

                if gesture_map:
                    self.gesture_configs[gesture_key] = gesture_map
            except Exception as e:
                write_log(f"Error loading gesture config {json_file}: {e}")

        write_log(f"Total gesture configs loaded: {len(self.gesture_configs)}")

    def load_settings(self):
        """Load settings from gesture.json (threshold, preview flag)"""
        try:
            settings_path = os.path.join(get_gesture_data_dir(), "gesture.json")
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.threshold = settings.get("minimum_pixels_to_move", 20)
                    self.show_preview = settings.get("show_preview", True)
        except Exception as e:
            write_log(f"Error loading settings: {e}")

    # ------------------------------------------------------------------
    # Event filter installation and handling
    # ------------------------------------------------------------------
    def install_event_filter(self):
        if self.event_filter_installed:
            return

        try:
            app = Krita.instance()
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()
                if main_window:
                    QApplication.instance().installEventFilter(self)
                    self.event_filter_installed = True
                    write_log("Gesture event filter installed")
            elif not self.window_created_connected:
                app_notifier = app.notifier()
                app_notifier.windowCreated.connect(self._on_window_created)
                self.window_created_connected = True
        except Exception as e:
            write_log(f"Error installing event filter: {e}")

    def _on_window_created(self):
        try:
            app = Krita.instance()
            if self.window_created_connected:
                app_notifier = app.notifier()
                try:
                    app_notifier.windowCreated.disconnect(self._on_window_created)
                except Exception:
                    pass
                self.window_created_connected = False

            if app.activeWindow():
                main_window = app.activeWindow().qwindow()
                if main_window:
                    QApplication.instance().installEventFilter(self)
                    self.event_filter_installed = True
        except Exception as e:
            write_log(f"Error in windowCreated callback: {e}")

    def uninstall_event_filter(self):
        if self.event_filter_installed:
            try:
                QApplication.instance().removeEventFilter(self)
                self.event_filter_installed = False
                if self.preview_widget is not None:
                    self.preview_widget.hide_preview()
                    self.preview_widget.deleteLater()
                    self.preview_widget = None
            except Exception as e:
                write_log(f"Error uninstalling event filter: {e}")

    def pause_event_filter(self):
        if self.event_filter_installed:
            try:
                QApplication.instance().removeEventFilter(self)
                self.event_filter_installed = False
            except Exception as e:
                write_log(f"Error pausing event filter: {e}")

    def resume_event_filter(self):
        if not self.event_filter_installed:
            try:
                app = Krita.instance()
                if app.activeWindow() and app.activeWindow().qwindow():
                    QApplication.instance().installEventFilter(self)
                    self.event_filter_installed = True
            except Exception as e:
                write_log(f"Error resuming event filter: {e}")

    # ------------------------------------------------------------------
    # Gesture detection and execution
    # ------------------------------------------------------------------
    def eventFilter(self, _obj, event):
        self.event_filter_call_count += 1
        current_depth = self.event_filter_call_count
        self.max_event_filter_depth = max(self.max_event_filter_depth, current_depth)
        if current_depth > 100:
            self.event_filter_call_count -= 1
            return False

        try:
            if self.config_dialog_active:
                self.event_filter_call_count -= 1
                return False

            event_type = event.type()
            if event_type not in _GESTURE_EVENT_TYPES:
                return False

            if event_type == QEvent.KeyPress:
                key_text = self._key_text(event)
                if key_text and key_text in self.gesture_configs:
                    self.active_key = key_text
                    if not self.gesture_active:
                        cursor_pos = QCursor.pos()
                        self.start_gesture(cursor_pos)
                        if self.show_preview:
                            if self.preview_widget is None:
                                self.preview_widget = GesturePreviewWidget()
                            gesture_map = self.gesture_configs[key_text]
                            self.preview_widget.show_preview(gesture_map, cursor_pos)

            elif event_type == QEvent.KeyRelease:
                key_text = self._key_text(event)
                if key_text and key_text == self.active_key:
                    if self.preview_widget is not None:
                        self.preview_widget.hide_preview()
                    if self.gesture_active:
                        self.execute_current_gesture()
                    else:
                        self.cancel_gesture()

            elif event_type == QEvent.MouseMove:
                if self.gesture_active and self.active_key:
                    self.update_gesture(event.globalPos())

        except Exception as e:
            write_log(f"Error in eventFilter: {e}")
        finally:
            self.event_filter_call_count -= 1

        return False

    def _key_text(self, event):
        key_text = event.text().upper()
        if not key_text:
            key = event.key()
            if Qt.Key_F1 <= key <= Qt.Key_F12:
                key_text = f"F{key - Qt.Key_F1 + 1}"
        return key_text

    def calculate_direction(self, dx, dy):
        """Return one of 8 compass directions based on movement angle."""
        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0:
            angle += 360

        if angle >= 337.5 or angle < 22.5:
            return "right"
        if angle < 67.5:
            return "right_up"
        if angle < 112.5:
            return "up"
        if angle < 157.5:
            return "left_up"
        if angle < 202.5:
            return "left"
        if angle < 247.5:
            return "left_down"
        if angle < 292.5:
            return "down"
        return "right_down"

    def start_gesture(self, pos):
        self.gesture_active = True
        self.start_pos = pos
        self.last_pos = pos

    def update_gesture(self, pos):
        self.last_pos = pos

    def cancel_gesture(self):
        self.gesture_active = False
        self.active_key = None
        self.start_pos = None
        self.last_pos = None
        if self.preview_widget is not None:
            self.preview_widget.hide_preview()

    def execute_current_gesture(self):
        if not self.gesture_active or not self.start_pos or not self.last_pos:
            self.cancel_gesture()
            return

        dx = self.last_pos.x() - self.start_pos.x()
        dy = self.last_pos.y() - self.start_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5

        if distance < self.threshold:
            gesture_map = self.gesture_configs.get(self.active_key, {})
            if "center" in gesture_map:
                execute_gesture(gesture_map["center"])
            self.cancel_gesture()
            return

        direction = self.calculate_direction(dx, dy)
        gesture_map = self.gesture_configs.get(self.active_key, {})
        if direction in gesture_map:
            execute_gesture(gesture_map[direction])
        else:
            write_log(f"No gesture configured for direction: {direction}")

        self.cancel_gesture()

    def set_config_dialog_active(self, active):
        self.config_dialog_active = active

    def enable_gesture_preview(self, enable):
        self.show_preview = enable


class GestureManager:
    """Manager for the gesture system lifecycle."""

    def __init__(self):
        self.detector = None

    def initialize(self):
        if self.detector is None:
            self.detector = GestureDetector()
            self.detector.load_gesture_configs()
            self.detector.install_event_filter()

    def reload_configs(self):
        if self.detector:
            self.detector.load_gesture_configs()

    def shutdown(self):
        if self.detector:
            self.detector.uninstall_event_filter()
            self.detector = None


_gesture_manager = None


def get_gesture_manager():
    global _gesture_manager
    if _gesture_manager is None:
        _gesture_manager = GestureManager()
    return _gesture_manager


def initialize_gesture_system():
    get_gesture_manager().initialize()


def reload_gesture_configs():
    get_gesture_manager().reload_configs()


def shutdown_gesture_system():
    get_gesture_manager().shutdown()


def set_config_dialog_active(active):
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.set_config_dialog_active(active)


def pause_gesture_event_filter():
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.pause_event_filter()


def resume_gesture_event_filter():
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.resume_event_filter()


def is_gesture_filter_paused():
    manager = get_gesture_manager()
    if manager.detector:
        return not manager.detector.event_filter_installed
    return None


def is_gesture_enabled():
    """Check if gesture system is enabled in settings (defaults to enabled)."""
    settings_path = os.path.join(get_gesture_data_dir(), "gesture.json")
    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f).get("enabled", True)
    except Exception as e:
        write_log(f"Error reading gesture settings: {e}")
    return True


def set_gesture_enabled(enabled):
    """Persist the enabled flag in gesture.json and pause/resume the live filter."""
    settings_path = os.path.join(get_gesture_data_dir(), "gesture.json")
    settings = {}
    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
    except Exception as e:
        write_log(f"Error reading gesture settings: {e}")

    settings["enabled"] = bool(enabled)
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        write_log(f"Error saving gesture settings: {e}")

    manager = get_gesture_manager()
    if enabled:
        if manager.detector is None:
            initialize_gesture_system()
        else:
            resume_gesture_event_filter()
    else:
        if manager.detector is not None:
            pause_gesture_event_filter()


def enable_gesture_preview(enable):
    manager = get_gesture_manager()
    if manager.detector:
        manager.detector.enable_gesture_preview(enable)
