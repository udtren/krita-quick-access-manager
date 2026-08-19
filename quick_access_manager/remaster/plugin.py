"""Krita registration entry point for the remastered Quick Access Palette."""

from krita import Extension, Krita  # type: ignore

from .features.quick_access_palette.docker import QuickAccessPaletteDockerFactory


class QuickAccessPaletteExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.palette_factory = None

    def setup(self):
        self.palette_factory = QuickAccessPaletteDockerFactory()
        Krita.instance().addDockWidgetFactory(self.palette_factory)

    def createActions(self, window):
        pass


app = Krita.instance()
app.addExtension(QuickAccessPaletteExtension(app))
