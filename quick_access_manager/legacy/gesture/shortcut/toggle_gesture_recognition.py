from krita import Krita, Extension
from ..gesture_main import (
    pause_gesture_event_filter,
    resume_gesture_event_filter,
    is_gesture_filter_paused,
    get_gesture_manager,
)


def toggle_gesture_recognition():
    """Enable or disable gesture recognition globally."""
    manager = get_gesture_manager()
    event_filter_installed = False
    if manager and manager.detector:
        event_filter_installed = manager.detector.event_filter_installed

    if event_filter_installed:
        pause_gesture_event_filter()
    else:
        resume_gesture_event_filter()


class ToggleGestureExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction(
            "toggle_gesture_recognition", "Toggle Gesture Recognition"
        )
        action.triggered.connect(toggle_gesture_recognition)
