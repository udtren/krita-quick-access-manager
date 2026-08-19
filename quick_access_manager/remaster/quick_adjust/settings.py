"""Quick Adjust settings, stored in the shared Quick Access Palette config
(document.settings["quick_adjust"]) instead of a dedicated JSON file.
"""

from ..infrastructure import PaletteRepository

DEFAULT_QUICK_ADJUST_SETTINGS = {
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
}

BLENDER_MODE_LIST = [
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
]


def _load():
    """Merged Quick Adjust settings.

    Every getter below calls this, and building the docker hits a dozen of them
    in a row, so the underlying JSON reads go through the mtime-validated cache
    in `infrastructure.json_cache` rather than the filesystem each time.
    """
    document = PaletteRepository().load()
    settings = dict(DEFAULT_QUICK_ADJUST_SETTINGS)
    settings.update(document.settings.get("quick_adjust", {}))
    return settings


def get_brush_section():
    settings = _load()
    number_size = settings["font_size"]
    return {
        "size_slider": {
            "enabled": settings["size_slider_enabled"],
            "number_size": number_size,
        },
        "opacity_slider": {
            "enabled": settings["opacity_slider_enabled"],
            "number_size": number_size,
        },
        "flow_slider": {
            "enabled": settings["flow_slider_enabled"],
            "number_size": number_size,
        },
        "rotation_slider": {"number_size": number_size},
    }


def get_layer_section():
    settings = _load()
    return {
        "opacity_slider": {
            "enabled": settings["layer_opacity_slider_enabled"],
            "number_size": settings["font_size"],
        }
    }


def get_brush_history_section():
    settings = _load()
    return {
        "enabled": settings["brush_history_enabled"],
        "total_items": settings["brush_history_total"],
        "icon_size": settings["brush_history_icon_size"],
    }


def get_color_history_section():
    settings = _load()
    return {
        "enabled": settings["color_history_enabled"],
        "total_items": settings["color_history_total"],
        "icon_size": settings["color_history_icon_size"],
    }


def get_blender_mode_list():
    return list(BLENDER_MODE_LIST)


def get_font_size():
    return _load()["font_size"]


def get_number_size():
    """Alias for get_font_size() for backwards compatibility with ported code."""
    return get_font_size()


def get_color_history_total():
    return _load()["color_history_total"]


def get_color_history_icon_size():
    return _load()["color_history_icon_size"]


def get_brush_history_total():
    return _load()["brush_history_total"]


def get_brush_history_icon_size():
    return _load()["brush_history_icon_size"]


def get_alt_erase_key():
    return _load()["alt_erase_key"]


def get_preserve_alpha_key():
    return _load()["preserve_alpha_key"]


def get_select_outline_key():
    return _load()["select_outline_key"]


def get_temp_brush_sets():
    return _load().get("temp_brush_sets", [])


def is_tool_options_enabled():
    return _load()["tool_options_enabled"]


def is_tool_options_start_visible():
    return _load()["tool_options_start_visible"]


def get_tool_options_position():
    return _load()["tool_options_position"]


def set_tool_options_start_visible(visible):
    repository = PaletteRepository()
    document = repository.load()
    quick_adjust = dict(DEFAULT_QUICK_ADJUST_SETTINGS)
    quick_adjust.update(document.settings.get("quick_adjust", {}))
    quick_adjust["tool_options_start_visible"] = bool(visible)
    document.settings["quick_adjust"] = quick_adjust
    repository.save(document)
