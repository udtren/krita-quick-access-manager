from krita import *  # type: ignore
from .quick_access_manager import QuickAccessDockerFactory
from .brush_adjust import BrushAdjustDockerFactory
from .shortcut_manager import ShortcutAccessDockerFactory
from .color_selector.color_selector_dock import ColorSelectorDock
from .gesture import (
    initialize_gesture_system,
    shutdown_gesture_system,
    is_gesture_enabled,
)
from .gesture.shortcut.toggle_gesture_recognition import (
    ToggleGestureExtension,
)
from .utils.data_manager import get_performance_mode

performance_mode = get_performance_mode()


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

        if not performance_mode:
            Krita.instance().addDockWidgetFactory(self.brush_adjust_factory)

        Krita.instance().addDockWidgetFactory(self.shortcut_docker_factory)

        # Initialize gesture system if enabled
        if not performance_mode:
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


# -------------------
# Register all extensions with Krita
# -------------------
app = Krita.instance()
extensions = [
    QuickAccessManagerExtension,
    ToggleGestureExtension,
]

for extension_class in extensions:
    app.addExtension(extension_class(app))

# -------------------
# HueSVC Docker
# -------------------
DOCKER_ID = "HueSVC"

try:
    _dock_pos = DockWidgetFactoryBase.DockRight
except AttributeError:
    _dock_pos = DockWidgetFactoryBase.DockPosition.DockRight  # Krita 6

instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID, _dock_pos, ColorSelectorDock)
if not performance_mode:
    instance.addDockWidgetFactory(dock_widget_factory)
