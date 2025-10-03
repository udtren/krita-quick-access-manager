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
        # Kritaのウィンドウが初期化された後に呼ばれる
        for d in window.dockers():
            try:
                widget = None
                if hasattr(d, "widget"):
                    w = d.widget
                    widget = w() if callable(w) else w
                # For the new ShortcutAccessDockerWidget, restore grids data
                if widget and hasattr(widget, "restore_grids_from_file"):
                    widget.restore_grids_from_file()
            except Exception:
                QMessageBox.warning(
                    None,
                    "QuickAccessManagerExtension Error",
                    "Something wrong is happening on QuickAccessManagerExtension.createActions.\n\nYou can try disable other plugin and start Krita again.",
                )


Krita.instance().addExtension(QuickAccessManagerExtension(Krita.instance()))
