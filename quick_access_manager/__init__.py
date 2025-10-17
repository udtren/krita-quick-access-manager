from krita import Krita, Extension  # type: ignore
from PyQt5.QtWidgets import QMessageBox
from .quick_access_manager import QuickAccessDockerFactory
from .quick_brush_adjust import BrushAdjustDockerFactory
from .shortcut_manager import ShortcutAccessDockerFactory


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

    def createActions(self, window):
        pass


Krita.instance().addExtension(QuickAccessManagerExtension(Krita.instance()))
