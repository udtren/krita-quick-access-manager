from krita import DockWidgetFactory, DockWidgetFactoryBase  # type: ignore

from .widget import QuickAccessPaletteDockerWidget


class QuickAccessPaletteDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        try:
            dock_pos = DockWidgetFactory.DockRight
        except AttributeError:
            dock_pos = DockWidgetFactory.DockPosition.DockRight
        super().__init__("quick_access_palette_docker", dock_pos)

    def createDockWidget(self):
        return QuickAccessPaletteDockerWidget()
