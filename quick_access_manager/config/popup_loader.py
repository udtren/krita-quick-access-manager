import json
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence


class PopupConfigLoader:
    """Handles loading and saving popup shortcut configurations"""

    _instance = None
    _config = None
    _config_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PopupConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        """Load popup configuration from JSON file"""
        try:
            # Get the path to the config file
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            self._config_path = os.path.join(plugin_dir, "popup.json")

            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            else:
                # Default configuration
                self._config = {
                    "actions_popup_shortcut": "Tab",
                    "brush_sets_popup_shortcut": "W",
                    "brush_icon_size": 46,
                    "grid_label_width": 60,
                }
                self._save_config()
        except Exception as e:
            print(f"Error loading popup config: {e}")
            # Fallback to defaults
            self._config = {
                "actions_popup_shortcut": "Tab",
                "brush_sets_popup_shortcut": "W",
                "brush_icon_size": 46,
                "grid_label_width": 60,
            }

    def _save_config(self):
        """Save current configuration to JSON file"""
        try:
            if self._config_path:
                with open(self._config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving popup config: {e}")

    def get_actions_popup_shortcut(self):
        """Get the shortcut key sequence for actions popup"""
        shortcut_str = self._config.get("actions_popup_shortcut", "Tab")
        return self._parse_shortcut(shortcut_str)

    def get_brush_sets_popup_shortcut(self):
        """Get the shortcut key sequence for brush sets popup"""
        shortcut_str = self._config.get("brush_sets_popup_shortcut", "W")
        return self._parse_shortcut(shortcut_str)

    def set_actions_popup_shortcut(self, shortcut_str):
        """Set the shortcut for actions popup"""
        self._config["actions_popup_shortcut"] = shortcut_str
        self._save_config()

    def set_brush_sets_popup_shortcut(self, shortcut_str):
        """Set the shortcut for brush sets popup"""
        self._config["brush_sets_popup_shortcut"] = shortcut_str
        self._save_config()

    def get_actions_popup_shortcut_string(self):
        """Get the actions popup shortcut as a string"""
        return self._config.get("actions_popup_shortcut", "Tab")

    def get_brush_sets_popup_shortcut_string(self):
        """Get the brush sets popup shortcut as a string"""
        return self._config.get("brush_sets_popup_shortcut", "W")

    def get_brush_icon_size(self):
        """Get the brush icon size"""
        return self._config.get("brush_icon_size", 46)

    def set_brush_icon_size(self, size):
        """Set the brush icon size"""
        self._config["brush_icon_size"] = size
        self._save_config()

    def get_grid_label_width(self):
        """Get the grid label width"""
        return self._config.get("grid_label_width", 60)

    def set_grid_label_width(self, width):
        """Set the grid label width"""
        self._config["grid_label_width"] = width
        self._save_config()

    def _parse_shortcut(self, shortcut_str):
        """Parse shortcut string to QKeySequence"""
        try:
            # Handle special Qt key names
            key_map = {
                "Tab": Qt.Key_Tab,
                "W": Qt.Key_W,
                "A": Qt.Key_A,
                "S": Qt.Key_S,
                "D": Qt.Key_D,
                "Q": Qt.Key_Q,
                "E": Qt.Key_E,
                "R": Qt.Key_R,
                "F": Qt.Key_F,
                "Space": Qt.Key_Space,
                "Shift": Qt.Key_Shift,
                "Ctrl": Qt.Key_Control,
                "Alt": Qt.Key_Alt,
            }

            # Try direct mapping first
            if shortcut_str in key_map:
                return QKeySequence(key_map[shortcut_str])

            # Try QKeySequence parsing (handles combinations like "Ctrl+Tab")
            return QKeySequence(shortcut_str)
        except Exception as e:
            print(f"Error parsing shortcut '{shortcut_str}': {e}")
            # Return default Tab key on error
            return QKeySequence(Qt.Key_Tab)

    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
