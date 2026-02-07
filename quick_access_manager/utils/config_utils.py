import os

from .data_manager import check_common_config

_cached_config = None


def _get_krita_data_dir():
    """Get the Krita appdata directory (e.g. AppData/Roaming/krita).

    Computed by navigating up from pykrita/quick_access_manager/utils/.
    """
    # __file__ => krita/pykrita/quick_access_manager/utils/config_utils.py
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_dir = os.path.dirname(utils_dir)           # .../quick_access_manager/
    pykrita_dir = os.path.dirname(plugin_dir)          # .../pykrita/
    return os.path.dirname(pykrita_dir)                # .../krita/


def get_config_dir():
    """Get user config directory outside of pykrita so configs survive plugin updates.

    Returns path like: AppData/Roaming/krita/quick_access_manager/config
    """
    config_dir = os.path.join(_get_krita_data_dir(), "quick_access_manager", "config")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_plugin_dir():
    """Get the plugin source directory inside pykrita.

    Returns path like: AppData/Roaming/krita/pykrita/quick_access_manager
    """
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(utils_dir)


def get_gesture_data_dir():
    """Get gesture data directory outside of pykrita.

    Returns path like: AppData/Roaming/krita/quick_access_manager/gesture
    """
    gesture_dir = os.path.join(_get_krita_data_dir(), "quick_access_manager", "gesture")
    os.makedirs(gesture_dir, exist_ok=True)
    return gesture_dir


def get_common_config():
    """Get common configuration, cached for performance"""
    global _cached_config
    if _cached_config is None:
        _cached_config = check_common_config()
    return _cached_config


def reload_config():
    """Force reload of configuration"""
    global _cached_config
    _cached_config = None
    return get_common_config()


def get_font_px(font_size_str):
    """Convert font size string to pixels"""
    try:
        return int(str(font_size_str).replace("px", ""))
    except Exception:
        return 12


def get_spacing_between_buttons():
    """Get spacing between buttons from config"""
    return get_common_config()["layout"]["spacing_between_buttons"]


def get_spacing_between_grids():
    """Get spacing between grids from config"""
    return get_common_config()["layout"]["spacing_between_grids"]


def get_brush_icon_size():
    """Get brush icon size from config"""
    return get_common_config()["layout"]["brush_icon_size"]


def get_dynamic_columns():
    """Get dynamic columns from config"""
    config = get_common_config()
    max_brush = config.get("layout", {}).get("max_brush_per_row", 8)
    return int(max_brush)
