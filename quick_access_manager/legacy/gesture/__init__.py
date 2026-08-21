"""
Gesture module for Krita Quick Access Manager.
Provides key+mouse gesture functionality.
"""

from .gesture_main import (
    initialize_gesture_system,
    reload_gesture_configs,
    shutdown_gesture_system,
    get_gesture_manager,
    is_gesture_enabled,
)
from .gesture_config_dialog import GestureConfigDialog

__all__ = [
    'initialize_gesture_system',
    'reload_gesture_configs',
    'shutdown_gesture_system',
    'get_gesture_manager',
    'is_gesture_enabled',
    'GestureConfigDialog',
]
