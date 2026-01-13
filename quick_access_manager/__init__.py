from krita import *  # type: ignore
from PyQt5.QtWidgets import QMessageBox
from .quick_access_manager import QuickAccessDockerFactory
from .brush_adjust import BrushAdjustDockerFactory
from .shortcut_manager import ShortcutAccessDockerFactory
from .gesture import (
    initialize_gesture_system,
    shutdown_gesture_system,
    is_gesture_enabled,
)
from .gesture.shortcut.toggle_gesture_recognition import (
    ToggleGestureExtension,
)


class QuickAccessManagerExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.docker_factory = None
        self.brush_adjust_factory = None
        self.shortcut_docker_factory = None

    def setup(self):
        self.docker_factory = QuickAccessDockerFactory()
        self.brush_adjust_factory = BrushAdjustDockerFactory()
        self.shortcut_docker_factory = ShortcutAccessDockerFactory()
        Krita.instance().addDockWidgetFactory(self.docker_factory)
        Krita.instance().addDockWidgetFactory(self.brush_adjust_factory)
        Krita.instance().addDockWidgetFactory(self.shortcut_docker_factory)

        # Initialize gesture system if enabled
        try:
            if is_gesture_enabled():
                initialize_gesture_system()
                print("✅ Gesture system initialized")
            else:
                print("⏸️ Gesture system is disabled")
        except Exception as e:
            print(f"❌ Error initializing gesture system: {e}")

    def createActions(self, window):
        pass

    def __del__(self):
        """Cleanup when extension is destroyed"""
        try:
            shutdown_gesture_system()
            print("✅ Gesture system shutdown")
        except Exception as e:
            print(f"❌ Error shutting down gesture system: {e}")


# Register all extensions with Krita
app = Krita.instance()
extensions = [
    QuickAccessManagerExtension,
    ToggleGestureExtension,
]

for extension_class in extensions:
    app.addExtension(extension_class(app))
