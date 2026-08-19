"""Krita registration entry point for the remastered Quick Access Palette."""

from krita import Extension, Krita  # type: ignore

from .color_selector.docker import ColorSelectorDockFactory
from .compat import QApplication
from .features.quick_access_palette.docker import QuickAccessPaletteDockerFactory
from .features.quick_access_palette.popup import QuickAccessPalettePopup
from .gesture import (
    ToggleGestureExtension,
    initialize_gesture_system,
    is_gesture_enabled,
    shutdown_gesture_system,
)
from .quick_adjust.docker import QuickAdjustDockerFactory

_popup_window = None


def close_visible_palette_popups():
    """Close any visible palette popup, even if another action instance owns it."""
    global _popup_window
    closed = False
    candidates = []
    if _popup_window is not None:
        candidates.append(_popup_window)
    app = QApplication.instance()
    if app is not None:
        for widget in app.topLevelWidgets():
            if isinstance(widget, QuickAccessPalettePopup):
                candidates.append(widget)

    seen = set()
    for popup in candidates:
        if popup is None:
            continue
        key = id(popup)
        if key in seen:
            continue
        seen.add(key)
        try:
            if popup.isVisible():
                popup.close_popup()
                closed = True
        except RuntimeError:
            pass

    if closed:
        _popup_window = None
    return closed


class QuickAccessPaletteExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.palette_factory = None
        self.color_selector_factory = None
        self.quick_adjust_factory = None
        self.popup_window = None
        self.popup_action = None

    def setup(self):
        self.palette_factory = QuickAccessPaletteDockerFactory()
        Krita.instance().addDockWidgetFactory(self.palette_factory)

        self.color_selector_factory = ColorSelectorDockFactory()
        Krita.instance().addDockWidgetFactory(self.color_selector_factory)

        self.quick_adjust_factory = QuickAdjustDockerFactory()
        Krita.instance().addDockWidgetFactory(self.quick_adjust_factory)

        if is_gesture_enabled():
            try:
                initialize_gesture_system()
            except Exception as exc:
                print(f"Quick Access Palette: error initializing gesture system: {exc}")

    def __del__(self):
        try:
            shutdown_gesture_system()
        except Exception as exc:
            print(f"Quick Access Palette: error shutting down gesture system: {exc}")

    def createActions(self, window):
        action = window.createAction(
            "quick_access_palette_popup", "Quick Access Palette Popup"
        )
        self.popup_action = action
        action.triggered.connect(self.show_palette_popup)

    def show_palette_popup(self):
        global _popup_window
        if close_visible_palette_popups():
            self.popup_window = None
            return

        close_shortcuts = self.popup_action.shortcuts() if self.popup_action else []
        popup = QuickAccessPalettePopup(close_shortcuts=close_shortcuts)
        _popup_window = popup
        self.popup_window = popup

        def clear_popup_reference(*_):
            global _popup_window
            if _popup_window is popup:
                _popup_window = None
            if self.popup_window is popup:
                self.popup_window = None

        popup.destroyed.connect(clear_popup_reference)
        popup.show_at_cursor()


app = Krita.instance()
app.addExtension(QuickAccessPaletteExtension(app))
app.addExtension(ToggleGestureExtension(app))
