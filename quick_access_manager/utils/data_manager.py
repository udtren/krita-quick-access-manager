import os
import json
import shutil
import datetime

# Config dir is at krita/quick_access_manager/config (outside pykrita)
# __file__ => krita/pykrita/quick_access_manager/utils/data_manager.py
_utils_dir = os.path.dirname(os.path.abspath(__file__))
_krita_data_dir = os.path.dirname(os.path.dirname(os.path.dirname(_utils_dir)))
config_dir = os.path.join(_krita_data_dir, "quick_access_manager", "config")
config_path = os.path.join(config_dir, "common.json")


def get_default_common_config():
    """Get the default common configuration"""
    return {
        "color": {
            "docker_button_font_color": "#000000",
            "docker_button_background_color": "#63666a",
            "shortcut_button_font_color": "#eaeaea",
            "shortcut_button_background_color": "#2a1c2a",
        },
        "font": {
            "docker_button_font_size": "10px",
            "shortcut_button_font_size": "14px",
        },
        "layout": {
            "max_shortcut_per_row": 4,
            "max_brush_per_row": 8,
            "spacing_between_buttons": 1,
            "spacing_between_grids": 1,
            "brush_icon_size": 40,
        },
        "performance": {
            "enable_performance_mode": False,
        },
    }


def get_performance_mode():
    """Return True if Performance Mode is enabled in common.json."""
    config = check_common_config()
    return config.get("performance", {}).get("enable_performance_mode", False)


def save_common_config(config):
    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving common config: {e}")
        return False


def check_common_config():
    default_config = get_default_common_config()
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def log_save_grids_data(msg):
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_path = os.path.join(log_dir, "shortcut_grid.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")


def load_grids_data(data_file, preset_dict):
    grids = []
    grid_counter = 0
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for grid_data in data.get("grids", []):
                grid_counter += 1
                grid_name = grid_data.get("name", f"Grid {grid_counter}")
                brush_names = grid_data.get("brush_presets", [])
                brush_presets = []
                for name in brush_names:
                    preset = preset_dict.get(name)
                    if preset:
                        brush_presets.append(preset)
                grid_info = {
                    "container": None,
                    "widget": None,
                    "layout": None,
                    "name_label": None,
                    "rename_button": None,
                    "name": grid_name,
                    "brush_presets": brush_presets,
                    "is_active": False,
                }
                grids.append(grid_info)
        except Exception:
            pass
    return grids, grid_counter


def save_grids_data(data_file, grids):
    data = {
        "grids": [
            {
                "name": grid["name"],
                "brush_presets": [p.name() for p in grid["brush_presets"]],
            }
            for grid in grids
        ]
    }
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_tabs_data(data_file, preset_dict):
    """Load grids_data.json as a multi-tab structure.

    If the file uses the old flat {"grids": [...]} format it is backed up to
    grids_data.json.bak and then migrated in-place to the new format.

    Returns (tabs, grid_counter) where tabs is a list of:
        {"name": str, "grids": [grid_info, ...], "layout": None}
    """
    tabs = []
    grid_counter = 0

    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "grids" in data and "tabs" not in data:
                backup_path = data_file + ".bak"
                shutil.copy2(data_file, backup_path)
                data = {"tabs": [{"name": "Tab 1", "grids": data["grids"]}]}
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

            for tab_data in data.get("tabs", []):
                tab_name = tab_data.get("name", f"Tab {len(tabs) + 1}")
                grids = []
                for grid_data in tab_data.get("grids", []):
                    grid_counter += 1
                    grid_name = grid_data.get("name", f"Grid {grid_counter}")
                    brush_presets = [
                        preset_dict[name]
                        for name in grid_data.get("brush_presets", [])
                        if name in preset_dict
                    ]
                    grids.append({
                        "container": None,
                        "widget": None,
                        "layout": None,
                        "name_label": None,
                        "name": grid_name,
                        "brush_presets": brush_presets,
                        "is_active": False,
                    })
                tabs.append({"name": tab_name, "grids": grids, "layout": None})
        except Exception:
            pass

    if not tabs:
        tabs = [{"name": "Tab 1", "grids": [], "layout": None}]

    return tabs, grid_counter


def save_tabs_data(data_file, tabs):
    """Save the multi-tab brush-sets structure to grids_data.json."""
    data = {
        "tabs": [
            {
                "name": tab["name"],
                "grids": [
                    {
                        "name": grid["name"],
                        "brush_presets": [p.name() for p in grid["brush_presets"]],
                    }
                    for grid in tab["grids"]
                ],
            }
            for tab in tabs
        ]
    }
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_shortcut_grids_data(data_file, krita_instance):
    grids = []
    grid_counter = 0
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for grid_data in data.get("grids", []):
                grid_counter += 1
                grid_name = grid_data.get("name", f"Shortcut Grid {grid_counter}")
                max_shortcut_per_row = grid_data.get("max_shortcut_per_row", "")
                icon_size = grid_data.get("icon_size", "")
                shortcut_items = grid_data.get("shortcuts", [])
                actions = []
                shortcut_configs = []
                for shortcut in shortcut_items:
                    if isinstance(shortcut, dict):
                        action_id = shortcut.get("actionName")
                        action = krita_instance.action(action_id) if action_id else None
                        if action:
                            actions.append(action)
                            shortcut_configs.append(shortcut)
                    else:
                        # 旧形式（strのみ）
                        action = krita_instance.action(shortcut) if shortcut else None
                        if action:
                            actions.append(action)
                            shortcut_configs.append({"actionName": shortcut})
                grid_info = {
                    "name": grid_name,
                    "max_shortcut_per_row": max_shortcut_per_row,
                    "icon_size": icon_size,
                    "actions": actions,
                    "shortcut_configs": shortcut_configs,
                }
                grids.append(grid_info)
        except Exception:
            pass
    return grids


def save_shortcut_grids_data(data_file, grids):
    data = {
        "grids": [
            {
                "name": grid["name"],
                "max_shortcut_per_row": grid.get("max_shortcut_per_row", ""),
                "icon_size": grid.get("icon_size", ""),
                "shortcuts": grid["shortcuts"],
            }
            for grid in grids
        ]
    }
    # log_save_grids_data(f"save_shortcut_grids_data: {json.dumps(data, ensure_ascii=False)}")
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_save_grids_data(f"save_shortcut_grids_data ERROR: {str(e)}")


def load_shortcut_tabs_data(data_file):
    """Load shortcut_grid_data.json as a multi-tab structure.

    Migrates old flat {"grids": [...]} format: backs up to .bak then rewrites
    in-place as {"tabs": [{"name": "Tab 1", "grids": [...]}]}.

    Returns list of tab dicts:
        {"name": str, "grids": [{"name", "max_shortcut_per_row", "icon_size", "shortcuts"}, ...]}
    """
    tabs = []

    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "grids" in data and "tabs" not in data:
                backup_path = data_file + ".bak"
                shutil.copy2(data_file, backup_path)
                data = {"tabs": [{"name": "Tab 1", "grids": data["grids"]}]}
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            for tab_data in data.get("tabs", []):
                tab_name = tab_data.get("name", f"Tab {len(tabs) + 1}")
                grids = []
                for grid_data in tab_data.get("grids", []):
                    raw_shortcuts = grid_data.get("shortcuts", [])
                    shortcuts = [
                        s if isinstance(s, dict) else {"actionName": s}
                        for s in raw_shortcuts
                    ]
                    grids.append({
                        "name": grid_data.get("name", f"Shortcut Grid {len(grids) + 1}"),
                        "max_shortcut_per_row": grid_data.get("max_shortcut_per_row", ""),
                        "icon_size": grid_data.get("icon_size", ""),
                        "shortcuts": shortcuts,
                    })
                tabs.append({"name": tab_name, "grids": grids})
        except Exception:
            pass

    if not tabs:
        tabs = [{"name": "Tab 1", "grids": []}]

    return tabs


def save_shortcut_tabs_data(data_file, tabs_data):
    """Save shortcut grids as a multi-tab structure."""
    data = {
        "tabs": [
            {
                "name": tab["name"],
                "grids": [
                    {
                        "name": grid["name"],
                        "max_shortcut_per_row": grid.get("max_shortcut_per_row", ""),
                        "icon_size": grid.get("icon_size", ""),
                        "shortcuts": grid["shortcuts"],
                    }
                    for grid in tab["grids"]
                ],
            }
            for tab in tabs_data
        ]
    }
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_save_grids_data(f"save_shortcut_tabs_data ERROR: {str(e)}")
