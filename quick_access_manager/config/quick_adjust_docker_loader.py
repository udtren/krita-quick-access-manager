import json
import os


def _load_config():
    """Load the quick_adjust_docker.json configuration file."""
    config_path = os.path.join(os.path.dirname(__file__), "quick_adjust_docker.json")
    with open(config_path, 'r') as f:
        return json.load(f)


def get_brush_section():
    """Return the brush_section configuration.

    Returns:
        dict: Configuration for brush sliders (size, opacity, rotation)
    """
    config = _load_config()
    return config.get("brush_section", {})


def get_layer_section():
    """Return the layer_section configuration.

    Returns:
        dict: Configuration for layer opacity slider
    """
    config = _load_config()
    return config.get("layer_section", {})


def get_brush_history_section():
    """Return the brush_history_section configuration.

    Returns:
        dict: Configuration for brush history (enabled, total_items, icon_size)
    """
    config = _load_config()
    return config.get("brush_history_section", {})


def get_color_history_section():
    """Return the color_history_section configuration.

    Returns:
        dict: Configuration for color history (enabled, total_items, icon_size)
    """
    config = _load_config()
    return config.get("color_history_section", {})


def get_blender_mode_list():
    """Return the blender_mode_list configuration.

    Returns:
        list: List of blending modes
    """
    config = _load_config()
    return config.get("blender_mode_list", [])


def get_status_bar_section():
    """Return the status_bar_section configuration.

    Returns:
        dict: Configuration for status bar (enabled)
    """
    config = _load_config()
    return config.get("status_bar_section", {})


def get_font_size():
    """Return the configured font size for adjustments.

    Returns:
        str: Font size (e.g., "12px")
    """
    config = _load_config()
    # First check if there's a global font_size setting
    if "font_size" in config:
        return config["font_size"]

    # Otherwise try to get from brush section
    brush_section = config.get("brush_section", {})
    if brush_section:
        # Get from any slider config, they should all be the same
        for key in ["size_slider", "opacity_slider", "rotation_slider"]:
            slider = brush_section.get(key, {})
            if slider and "number_size" in slider:
                return slider["number_size"]
    return "12px"  # Default fallback


def get_number_size():
    """Return the configured number size for adjustments.
    This is an alias for get_font_size() for backwards compatibility.

    Returns:
        str: Number size (e.g., "12px")
    """
    return get_font_size()


def get_color_history_total():
    """Return the total items for color history.

    Returns:
        int: Number of color history items
    """
    config = _load_config()
    return config.get("color_history_section", {}).get("total_items", 20)


def get_color_history_icon_size():
    """Return the icon size for color history.

    Returns:
        int: Icon size in pixels
    """
    config = _load_config()
    return config.get("color_history_section", {}).get("icon_size", 30)


def get_brush_history_total():
    """Return the total items for brush history.

    Returns:
        int: Number of brush history items
    """
    config = _load_config()
    return config.get("brush_history_section", {}).get("total_items", 20)


def get_brush_history_icon_size():
    """Return the icon size for brush history.

    Returns:
        int: Icon size in pixels
    """
    config = _load_config()
    return config.get("brush_history_section", {}).get("icon_size", 34)


def get_all_config():
    """Return the complete configuration.

    Returns:
        dict: Complete configuration from quick_adjust_docker.json
    """
    return _load_config()
