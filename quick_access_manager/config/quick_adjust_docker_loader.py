import json
import os


def _get_default_config():
    """Return the default configuration structure."""
    return {
        "floating_widgets": {
            "tool_options": {"enabled": True, "start_visible": True},
        },
        "brush_section": {
            "size_slider": {"enabled": True, "number_size": "12px"},
            "opacity_slider": {"enabled": True, "number_size": "12px"},
            "flow_slider": {"enabled": True, "number_size": "12px"},
        },
        "layer_section": {"opacity_slider": {"enabled": True, "number_size": "12px"}},
        "brush_history_section": {"enabled": True, "total_items": 14, "icon_size": 34},
        "color_history_section": {"enabled": True, "total_items": 14, "icon_size": 30},
        "docker_toggle_section": {"enabled": True},
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
        "font_size": "12px",
    }


def ensure_config_exists():
    """Check if config file exists, create it with defaults if it doesn't.

    Returns:
        bool: True if config was created, False if it already existed
    """
    config_path = os.path.join(os.path.dirname(__file__), "quick_adjust_docker.json")

    if not os.path.exists(config_path):
        # Create the config file with default values
        default_config = _get_default_config()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return True

    return False


def _load_config():
    """Load the quick_adjust_docker.json configuration file."""
    # Ensure config exists before loading
    ensure_config_exists()

    config_path = os.path.join(os.path.dirname(__file__), "quick_adjust_docker.json")
    with open(config_path, "r", encoding="utf-8") as f:
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


def get_docker_toggle_section():
    """Return the docker_toggle_section configuration.

    Returns:
        dict: Configuration for docker toggle buttons (enabled)
    """
    config = _load_config()
    return config.get("docker_toggle_section", {})


def get_floating_widgets_section():
    """Return the floating_widgets section configuration.

    Returns:
        dict: Configuration for floating widgets (tool_options)
    """
    config = _load_config()
    default_floating = _get_default_config().get("floating_widgets", {})
    return config.get("floating_widgets", default_floating)


def is_tool_options_enabled():
    """Check if the floating tool options widget is enabled.

    Returns:
        bool: True if tool options should be enabled (default: True)
    """
    floating_config = get_floating_widgets_section()
    return floating_config.get("tool_options", {}).get("enabled", True)


def is_tool_options_start_visible():
    """Check if the floating tool options widget should start visible.

    Returns:
        bool: True if tool options should start visible (default: True)
    """
    floating_config = get_floating_widgets_section()
    return floating_config.get("tool_options", {}).get("start_visible", True)


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
        for key in ["size_slider", "opacity_slider"]:
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


def _get_docker_buttons_config_path():
    """Get the path to docker_buttons.json configuration file.

    Returns:
        str: Path to docker_buttons.json
    """
    return os.path.join(os.path.dirname(__file__), "docker_buttons.json")


def _get_default_docker_buttons():
    """Return the default docker buttons configuration.

    Returns:
        dict: Default docker buttons configuration
    """
    return {
        "docker_buttons": [
            {
                "button_name": "Tool",
                "button_width": 40,
                "button_icon": "",
                "docker_keywords": ["tool", "option"],
                "description": "Tool Options Docker",
            },
            {
                "button_name": "Layers",
                "button_width": 50,
                "button_icon": "",
                "docker_keywords": ["layer"],
                "description": "Layers Docker",
            },
            {
                "button_name": "Brush",
                "button_width": 50,
                "button_icon": "",
                "docker_keywords": ["brush", "preset"],
                "description": "Brush Presets Docker",
            },
        ]
    }


def ensure_docker_buttons_config_exists():
    """Check if docker_buttons.json exists, create it with defaults if it doesn't.

    Returns:
        bool: True if config was created, False if it already existed
    """
    config_path = _get_docker_buttons_config_path()

    if not os.path.exists(config_path):
        # Create the config file with default values
        default_config = _get_default_docker_buttons()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return True

    return False


def get_docker_buttons():
    """Load and return the docker_buttons configuration.

    Returns:
        list: List of docker button configurations
    """
    ensure_docker_buttons_config_exists()

    config_path = _get_docker_buttons_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config.get("docker_buttons", [])
