import os
import json
import datetime


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
