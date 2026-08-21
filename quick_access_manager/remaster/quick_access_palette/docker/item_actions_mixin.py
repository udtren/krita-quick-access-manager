"""Header-menu "Add" handlers and the dialogs they open (Grid Edit, Gesture
Settings, Resources, Settings)."""

from ...compat import QInputDialog
from ...gesture import GestureConfigDialog, set_gesture_enabled
from ...shared import SEPARATOR_ORIENTATION_VERTICAL
from ..alias_config_dialog import AliasConfigDialog
from ..dialogs import (
    BrushBlendModeItemConfigDialog,
    BrushSizeItemConfigDialog,
    ColorItemConfigDialog,
    GridEditDialog,
    PaletteConfigDialog,
    ScriptItemConfigDialog,
)


class ItemActionsMixin:
    """Requires `self.controller`, `self.reload_tabs()`, `self.active_view()`
    and `self.apply_header_button_color()` from the composed docker widget."""

    def add_tab(self):
        name, ok = QInputDialog.getText(
            self,
            "Add Tab",
            "Tab name:",
            text=f"Tab {len(self.controller.document.tabs) + 1}",
        )
        if ok and name.strip():
            self.controller.add_tab(name.strip())
            self.reload_tabs()

    def add_current_brush(self):
        view = self.active_view()
        if not view:
            return
        preset = view.currentBrushPreset()
        if not preset:
            return
        self.controller.add_brush(preset.name())
        self.reload_tabs()

    def add_label(self):
        text, ok = QInputDialog.getText(self, "Add Label", "Label text:")
        if ok and text:
            self.controller.add_label(text)
            self.reload_tabs()

    def add_separator(self):
        self.controller.add_separator()
        self.reload_tabs()

    def add_v_separator(self):
        self.controller.add_separator(orientation=SEPARATOR_ORIENTATION_VERTICAL)
        self.reload_tabs()

    def add_color(self):
        dialog = ColorItemConfigDialog(
            config={"color": self.current_foreground_color()}, parent=self
        )
        if dialog.exec():
            self.controller.add_color(dialog.get_config().get("color", "#ffffff"))
            self.reload_tabs()

    def current_foreground_color(self):
        view = self.active_view()
        if not view:
            return "#ffffff"
        managed_color = view.foregroundColor()
        qcolor = managed_color.colorForCanvas(view.canvas()) if managed_color else None
        return qcolor.name() if qcolor and qcolor.isValid() else "#ffffff"

    def add_script(self):
        dialog = ScriptItemConfigDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            script_path = config.pop("script_path", "")
            self.controller.add_script(script_path, config=config)
            self.reload_tabs()

    def add_brush_size(self):
        dialog = BrushSizeItemConfigDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            text = config.pop("text", "1")
            self.controller.add_brush_size(text, config=config)
            self.reload_tabs()

    def add_brush_blend_mode(self):
        dialog = BrushBlendModeItemConfigDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            text = config.pop("text", "")
            self.controller.add_brush_blend_mode(text, config=config)
            self.reload_tabs()

    def show_grid_edit_dialog(self):
        tabs = self.controller.document.tabs
        if not tabs:
            return
        dialog = GridEditDialog(
            tabs, active_tab_id=self.controller.active_tab_id, parent=self
        )
        if dialog.exec() and dialog.saved_tabs is not None:
            for tab_id, items in dialog.saved_tabs.items():
                self.controller.replace_tab_grid_items(tab_id, items, compact=False)
            self.reload_tabs()

    def show_gesture_config_dialog(self):
        dialog = GestureConfigDialog(parent=self)
        dialog.exec()

    def show_alias_config_dialog(self):
        # on_item_added repaints the grid immediately on every Add click, while
        # the (modal) dialog is still open - without it, added items only
        # became visible once the dialog was closed.
        dialog = AliasConfigDialog(
            parent=self, controller=self.controller, on_item_added=self.reload_tabs
        )
        dialog.exec()
        # Reload once more regardless of Save/Cancel, in case the alias
        # name/color/icon fields themselves (not the Add buttons) changed how
        # an already-placed item should render.
        self.reload_tabs()

    def show_config_dialog(self):
        grid = self.controller.active_grid()
        if not grid:
            return
        huesvc_settings = self.controller.huesvc_settings()
        dialog_width, dialog_height = self.controller.config_dialog_size()
        dialog = PaletteConfigDialog(
            grid.columns,
            docker_icon_size=self.controller.docker_icon_size(),
            popup_icon_size=self.controller.popup_icon_size(),
            huesvc_value_font_size=huesvc_settings["value_font_size"],
            huesvc_poll_interval=huesvc_settings["poll_interval"],
            huesvc_rgb_display_mode=huesvc_settings["rgb_display_mode"],
            huesvc_popup_width=huesvc_settings.get("popup_width", 350),
            huesvc_popup_height=huesvc_settings.get("popup_height", 550),
            huesvc_controls_panel_font_size=huesvc_settings.get(
                "controls_panel_font_size", 12
            ),
            quick_adjust_settings=self.controller.quick_adjust_settings(),
            config_dialog_width=dialog_width,
            config_dialog_height=dialog_height,
            huesvc_enabled=self.controller.is_huesvc_enabled(),
            quick_adjust_enabled=self.controller.is_quick_adjust_enabled(),
            header_button_color=self.controller.header_button_color(),
            **{
                f"tab_{key}": value
                for key, value in self.controller.tab_bar_settings().items()
            },
            parent=self,
        )
        if dialog.exec():
            self.controller.set_columns(dialog.get_columns())
            self.controller.update_settings(
                docker_icon_size=dialog.get_docker_icon_size(),
                popup_icon_size=dialog.get_popup_icon_size(),
                config_dialog_width=dialog.get_config_dialog_width(),
                config_dialog_height=dialog.get_config_dialog_height(),
                huesvc_enabled=dialog.get_huesvc_enabled(),
                quick_adjust_enabled=dialog.get_quick_adjust_enabled(),
                header_button_color=dialog.get_header_button_color(),
                tab_active_font_size=dialog.get_tab_active_font_size(),
                tab_active_font_color=dialog.get_tab_active_font_color(),
                tab_active_background_color=dialog.get_tab_active_background_color(),
                tab_inactive_font_size=dialog.get_tab_inactive_font_size(),
                tab_inactive_font_color=dialog.get_tab_inactive_font_color(),
                tab_inactive_background_color=dialog.get_tab_inactive_background_color(),
            )
            self.controller.update_huesvc_settings(
                value_font_size=dialog.get_huesvc_value_font_size(),
                poll_interval=dialog.get_huesvc_poll_interval(),
                rgb_display_mode=dialog.get_huesvc_rgb_display_mode(),
                popup_width=dialog.get_huesvc_popup_width(),
                popup_height=dialog.get_huesvc_popup_height(),
                controls_panel_font_size=dialog.get_huesvc_controls_panel_font_size(),
            )
            self.controller.update_quick_adjust_settings(
                **dialog.get_quick_adjust_settings()
            )
            set_gesture_enabled(dialog.get_gesture_enabled())
            self.apply_header_button_color()
            self.reload_tabs()
