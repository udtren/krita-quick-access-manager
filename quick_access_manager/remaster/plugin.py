"""Krita registration entry point for the remastered Quick Access Palette."""

from krita import Extension, Krita  # type: ignore

from .color_selector.docker import ColorSelectorDockFactory
from .color_selector.popup import HueSvcPopup
from .compat import QApplication
from .gesture import (
    ToggleGestureExtension,
    initialize_gesture_system,
    is_gesture_enabled,
    shutdown_gesture_system,
)
from .infrastructure import DockerManager
from .quick_access_palette.controller import PaletteController
from .quick_access_palette.docker import QuickAccessPaletteDockerFactory
from .quick_access_palette.popup import QuickAccessPalettePopup
from .quick_adjust.docker import QuickAdjustDockerFactory

_popup_window = None
_huesvc_popup_window = None


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


def close_visible_huesvc_popups():
    """Close any visible HueSVC popup, even if another action instance owns it."""
    global _huesvc_popup_window
    closed = False
    candidates = []
    if _huesvc_popup_window is not None:
        candidates.append(_huesvc_popup_window)
    app = QApplication.instance()
    if app is not None:
        for widget in app.topLevelWidgets():
            if isinstance(widget, HueSvcPopup):
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
        _huesvc_popup_window = None
    return closed


class QuickAccessPaletteExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.palette_factory = None
        self.color_selector_factory = None
        self.quick_adjust_factory = None
        self.popup_window = None
        self.popup_action = None
        self.huesvc_popup_window = None
        self.huesvc_popup_action = None

    def setup(self):
        self.palette_factory = QuickAccessPaletteDockerFactory()
        Krita.instance().addDockWidgetFactory(self.palette_factory)

        controller = PaletteController()

        if controller.is_huesvc_enabled():
            self.color_selector_factory = ColorSelectorDockFactory()
            Krita.instance().addDockWidgetFactory(self.color_selector_factory)

        if controller.is_quick_adjust_enabled():
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

        huesvc_action = window.createAction("hue_svc_popup", "HueSVC Popup")
        self.huesvc_popup_action = huesvc_action
        huesvc_action.triggered.connect(self.show_huesvc_popup)

        move_palette_action = window.createAction(
            "move_quick_access_palette_docker_to_cursor",
            "Move Quick Access Palette Docker to Cursor",
        )
        move_palette_action.triggered.connect(self.move_palette_docker_to_cursor)

        move_quick_adjust_action = window.createAction(
            "move_quick_adjust_docker_to_cursor",
            "Move Quick Adjust Docker to Cursor",
        )
        move_quick_adjust_action.triggered.connect(self.move_quick_adjust_docker_to_cursor)

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

    def show_huesvc_popup(self):
        global _huesvc_popup_window
        if close_visible_huesvc_popups():
            self.huesvc_popup_window = None
            return

        close_shortcuts = (
            self.huesvc_popup_action.shortcuts() if self.huesvc_popup_action else []
        )
        popup = HueSvcPopup(close_shortcuts=close_shortcuts)
        _huesvc_popup_window = popup
        self.huesvc_popup_window = popup

        def clear_popup_reference(*_):
            global _huesvc_popup_window
            if _huesvc_popup_window is popup:
                _huesvc_popup_window = None
            if self.huesvc_popup_window is popup:
                self.huesvc_popup_window = None

        popup.destroyed.connect(clear_popup_reference)
        popup.show_at_cursor()

    def move_palette_docker_to_cursor(self):
        DockerManager.toggle_docker_position_at_cursor("quick_access_palette_docker")

    def move_quick_adjust_docker_to_cursor(self):
        DockerManager.toggle_docker_position_at_cursor("brush_adjust_docker")


app = Krita.instance()
app.addExtension(QuickAccessPaletteExtension(app))
app.addExtension(ToggleGestureExtension(app))
