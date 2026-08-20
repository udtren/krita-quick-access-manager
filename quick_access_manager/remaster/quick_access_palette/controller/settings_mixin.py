"""Settings storage/retrieval for the Quick Access Palette controller.

`PaletteController.settings()` merges `document.settings` on top of
DEFAULT_SETTINGS section by section, so any setting missing from the saved
JSON (a fresh install, or one saved before a new setting existed) still
gets a value.
"""

DEFAULT_SETTINGS = {
    "default": {
        "docker_icon_size": 42,
        "config_dialog_width": 340,
        "config_dialog_height": 480,
        "huesvc_enabled": True,
        "quick_adjust_enabled": True,
        "header_button_color": "#828282",
        "tab_active_font_size": 12,
        "tab_active_font_color": "#ffffff",
        "tab_active_background_color": "#3f3f3f",
        "tab_inactive_font_size": 12,
        "tab_inactive_font_color": "#a0a0a0",
        "tab_inactive_background_color": "#2b2b2b",
    },
    "popup": {"popup_icon_size": 42},
    "huesvc": {
        "value_font_size": 10,
        "poll_interval": 250,
        "rgb_display_mode": "percentage",
        "popup_width": 350,
        "popup_height": 550,
        "controls_panel_width": 220,
        "controls_panel_font_size": 12,
    },
    "quick_adjust": {
        "font_size": "12px",
        "size_slider_enabled": True,
        "opacity_slider_enabled": True,
        "flow_slider_enabled": True,
        "layer_opacity_slider_enabled": True,
        "color_history_enabled": True,
        "color_history_total": 14,
        "color_history_icon_size": 30,
        "brush_history_enabled": True,
        "brush_history_total": 14,
        "brush_history_icon_size": 34,
        "alt_erase_key": "",
        "preserve_alpha_key": "",
        "select_outline_key": "",
        "tool_options_enabled": False,
        "tool_options_start_visible": True,
        "tool_options_position": "left_align_top",
        "temp_brush_sets": [],
        "blender_mode_list": [
            "normal",
            "multiply",
            "screen",
            "dodge",
            "overlay",
            "soft_light_svg",
            "hard_light",
            "darken",
            "lighten",
            "greater",
        ],
    },
}


class SettingsMixin:
    """Docker/popup/HueSVC/Quick Adjust settings, all backed by
    `document.settings` and merged with DEFAULT_SETTINGS. Requires
    `self.document` and `self.save()` from the composed controller."""

    def settings(self):
        merged = {
            "default": dict(DEFAULT_SETTINGS["default"]),
            "popup": dict(DEFAULT_SETTINGS["popup"]),
            "huesvc": dict(DEFAULT_SETTINGS["huesvc"]),
            "quick_adjust": dict(DEFAULT_SETTINGS["quick_adjust"]),
        }
        for section, values in self.document.settings.items():
            if isinstance(values, dict):
                merged.setdefault(section, {}).update(values)
        return merged

    def docker_icon_size(self):
        return self._bounded_icon_size(
            self.settings()["default"].get("docker_icon_size", 42)
        )

    def popup_icon_size(self):
        return self._bounded_icon_size(
            self.settings()["popup"].get("popup_icon_size", 42)
        )

    def config_dialog_size(self):
        default = self.settings()["default"]
        return (
            int(default.get("config_dialog_width", 340)),
            int(default.get("config_dialog_height", 480)),
        )

    def is_huesvc_enabled(self):
        return bool(self.settings()["default"].get("huesvc_enabled", True))

    def is_quick_adjust_enabled(self):
        return bool(self.settings()["default"].get("quick_adjust_enabled", True))

    def header_button_color(self):
        return self.settings()["default"].get("header_button_color", "#828282")

    def tab_bar_settings(self):
        """Active-vs-other tab styling for the docker/popup's QTabBar.

        A single pair of styles applies across every tab, not per-tab -
        matching the "individual tab styling not needed" scope this was
        built for.
        """
        default = self.settings()["default"]
        return {
            "active_font_size": int(default.get("tab_active_font_size", 12)),
            "active_font_color": default.get("tab_active_font_color", "#ffffff"),
            "active_background_color": default.get(
                "tab_active_background_color", "#3f3f3f"
            ),
            "inactive_font_size": int(default.get("tab_inactive_font_size", 12)),
            "inactive_font_color": default.get("tab_inactive_font_color", "#a0a0a0"),
            "inactive_background_color": default.get(
                "tab_inactive_background_color", "#2b2b2b"
            ),
        }

    def update_settings(
        self,
        docker_icon_size=None,
        popup_icon_size=None,
        config_dialog_width=None,
        config_dialog_height=None,
        huesvc_enabled=None,
        quick_adjust_enabled=None,
        header_button_color=None,
        tab_active_font_size=None,
        tab_active_font_color=None,
        tab_active_background_color=None,
        tab_inactive_font_size=None,
        tab_inactive_font_color=None,
        tab_inactive_background_color=None,
    ):
        settings = self.settings()
        if docker_icon_size is not None:
            settings["default"]["docker_icon_size"] = self._bounded_icon_size(
                docker_icon_size
            )
        if popup_icon_size is not None:
            settings["popup"]["popup_icon_size"] = self._bounded_icon_size(
                popup_icon_size
            )
        if config_dialog_width is not None:
            settings["default"]["config_dialog_width"] = int(config_dialog_width)
        if config_dialog_height is not None:
            settings["default"]["config_dialog_height"] = int(config_dialog_height)
        if huesvc_enabled is not None:
            settings["default"]["huesvc_enabled"] = bool(huesvc_enabled)
        if quick_adjust_enabled is not None:
            settings["default"]["quick_adjust_enabled"] = bool(quick_adjust_enabled)
        if header_button_color is not None:
            settings["default"]["header_button_color"] = str(header_button_color)
        if tab_active_font_size is not None:
            settings["default"]["tab_active_font_size"] = int(tab_active_font_size)
        if tab_active_font_color is not None:
            settings["default"]["tab_active_font_color"] = str(tab_active_font_color)
        if tab_active_background_color is not None:
            settings["default"]["tab_active_background_color"] = str(
                tab_active_background_color
            )
        if tab_inactive_font_size is not None:
            settings["default"]["tab_inactive_font_size"] = int(tab_inactive_font_size)
        if tab_inactive_font_color is not None:
            settings["default"]["tab_inactive_font_color"] = str(
                tab_inactive_font_color
            )
        if tab_inactive_background_color is not None:
            settings["default"]["tab_inactive_background_color"] = str(
                tab_inactive_background_color
            )
        self.document.settings = settings
        self.save()

    def huesvc_settings(self):
        return self.settings()["huesvc"]

    def update_huesvc_settings(
        self,
        value_font_size=None,
        poll_interval=None,
        rgb_display_mode=None,
        popup_width=None,
        popup_height=None,
        controls_panel_font_size=None,
    ):
        settings = self.settings()
        if value_font_size is not None:
            settings["huesvc"]["value_font_size"] = int(value_font_size)
        if poll_interval is not None:
            settings["huesvc"]["poll_interval"] = int(poll_interval)
        if rgb_display_mode is not None:
            settings["huesvc"]["rgb_display_mode"] = rgb_display_mode
        if popup_width is not None:
            settings["huesvc"]["popup_width"] = int(popup_width)
        if popup_height is not None:
            settings["huesvc"]["popup_height"] = int(popup_height)
        if controls_panel_font_size is not None:
            settings["huesvc"]["controls_panel_font_size"] = int(
                controls_panel_font_size
            )
        self.document.settings = settings
        self.save()

    def quick_adjust_settings(self):
        return self.settings()["quick_adjust"]

    def update_quick_adjust_settings(self, **kwargs):
        settings = self.settings()
        settings["quick_adjust"].update(kwargs)
        self.document.settings = settings
        self.save()

    def _bounded_icon_size(self, value):
        try:
            return max(24, min(96, int(value)))
        except Exception:
            return 42
