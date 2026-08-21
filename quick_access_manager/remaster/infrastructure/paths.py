"""Filesystem paths for the remastered palette."""

import os

PLUGIN_CONFIG_DIR_NAME = "quick_access_manager"
PALETTE_CONFIG_FILE = "quick_access_palette.json"
PALETTE_SETTINGS_FILE = "settings.json"


def get_package_dir():
    """Return the top-level quick_access_manager package directory."""
    paths_dir = os.path.dirname(os.path.abspath(__file__))
    remaster_dir = os.path.dirname(paths_dir)
    return os.path.dirname(remaster_dir)


def get_krita_data_dir():
    """Return Krita's user data directory from a pykrita plugin install path."""
    package_dir = get_package_dir()
    pykrita_dir = os.path.dirname(package_dir)
    return os.path.dirname(pykrita_dir)


def get_remaster_config_dir():
    config_dir = os.path.join(get_krita_data_dir(), PLUGIN_CONFIG_DIR_NAME, "remaster")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_gesture_data_dir():
    gesture_dir = os.path.join(get_remaster_config_dir(), "gesture")
    os.makedirs(gesture_dir, exist_ok=True)
    return gesture_dir


def get_palette_config_path():
    return os.path.join(get_remaster_config_dir(), PALETTE_CONFIG_FILE)


def get_palette_settings_path():
    return os.path.join(get_remaster_config_dir(), PALETTE_SETTINGS_FILE)


def get_default_icons_dir():
    remaster_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(remaster_dir, "resources", "default_icons")


def get_system_icons_dir():
    remaster_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(remaster_dir, "resources", "system_icons")


def get_gesture_images_dir():
    remaster_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(remaster_dir, "resources", "gesture")


def get_quick_adjust_icons_dir():
    remaster_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(remaster_dir, "resources", "quick_adjust")
