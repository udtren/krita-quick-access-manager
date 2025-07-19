import os
import json

def check_common_config():
    config_path = os.path.join(os.path.dirname(__file__), "config", "common.json")
    default_config = {
        "color": {
            "docker_button_font_color": "#ffffff",
            "docker_button_background_color": "#63666a",
            "shortcut_button_font_color": "#ffffff",
            "shortcut_button_background_color": "#6c408c"
        },
        "font": {
            "docker_button_font_size": "14px",
            "shortcut_button_font_size": "14px"
        },
        "layout": {
            "max_shortcut_per_row": 2,
            "max_brush_per_row": 8
        }
    }
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)