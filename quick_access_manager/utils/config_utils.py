import os
import json
from ..preprocess import check_common_config

_cached_config = None

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