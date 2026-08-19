from krita import Extension  # type: ignore

from ..gesture_main import (
    get_gesture_manager,
    pause_gesture_event_filter,
    resume_gesture_event_filter,
)


def toggle_gesture_recognition():
    """Enable or disable gesture recognition globally."""
    manager = get_gesture_manager()
    event_filter_installed = bool(
        manager and manager.detector and manager.detector.event_filter_installed
    )

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
