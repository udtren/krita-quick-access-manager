import os
from ..preprocess import check_common_config

def get_common_config():
    """Get common configuration"""
    return check_common_config()

def get_spacing_between_buttons():
    """Get spacing between buttons from config"""
    config = get_common_config()
    return config["layout"]["spacing_between_buttons"]

def get_spacing_between_grids():
    """Get spacing between grids from config"""
    config = get_common_config()
    return config["layout"]["spacing_between_grids"]

def get_font_px(font_size_str):
    """Convert font size string to pixels"""
    try:
        return int(str(font_size_str).replace("px", ""))
    except Exception:
        return 12

def get_max_shortcut_per_row():
    """Get maximum shortcuts per row from config"""
    config = get_common_config()
    return int(config.get("layout", {}).get("max_shortcut_per_row", 3))

def get_shortcut_button_config():
    """Get shortcut button configuration"""
    config = get_common_config()
    return {
        'font_size': config["font"]["shortcut_button_font_size"],
        'font_color': config["color"]["shortcut_button_font_color"],
        'background_color': config["color"]["shortcut_button_background_color"]
    }