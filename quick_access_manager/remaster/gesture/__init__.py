"""
Gesture module for the remastered Quick Access Manager.
Provides key+mouse gesture functionality.
"""

from .gesture_config_dialog import GestureConfigDialog
from .gesture_main import (
    get_gesture_manager,
    initialize_gesture_system,
    is_gesture_enabled,
    is_gesture_filter_paused,
    pause_gesture_event_filter,
    reload_gesture_configs,
    resume_gesture_event_filter,
    set_gesture_enabled,
    shutdown_gesture_system,
)
from .shortcut.toggle_gesture_recognition import ToggleGestureExtension

__all__ = [
    "GestureConfigDialog",
    "ToggleGestureExtension",
    "get_gesture_manager",
    "initialize_gesture_system",
    "is_gesture_enabled",
    "is_gesture_filter_paused",
    "pause_gesture_event_filter",
    "reload_gesture_configs",
    "resume_gesture_event_filter",
    "set_gesture_enabled",
    "shutdown_gesture_system",
]
