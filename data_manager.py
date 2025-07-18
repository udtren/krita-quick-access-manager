import os
import json

# def log_shortcut_restore(msg):
#     import datetime
#     log_dir = os.path.join(os.path.dirname(__file__), "logs")
#     if not os.path.exists(log_dir):
#         os.makedirs(log_dir)
#     log_path = os.path.join(log_dir, "shortcut_grid.log")
#     with open(log_path, "a", encoding="utf-8") as f:
#         f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

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
                    'container': None,
                    'widget': None,
                    'layout': None,
                    'name_label': None,
                    'rename_button': None,
                    'name': grid_name,
                    'brush_presets': brush_presets,
                    'is_active': False
                }
                grids.append(grid_info)
        except Exception:
            pass
    return grids, grid_counter

def save_grids_data(data_file, grids):
    data = {
        "grids": [
            {
                "name": grid['name'],
                "brush_presets": [p.name() for p in grid['brush_presets']]
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
                shortcut_ids = grid_data.get("shortcuts", [])
                actions = []
                for action_id in shortcut_ids:
                    # log_shortcut_restore(f"load_shortcut_grids_data: grid={grid_name}, action_id={action_id}")
                    action = krita_instance.action(action_id) if action_id else None
                    # log_shortcut_restore(f"load_shortcut_grids_data: grid={grid_name}, action={action}")
                    if action:
                        actions.append(action)
                grid_info = {
                    'name': grid_name,
                    'actions': actions,
                    'shortcuts': shortcut_ids
                }
                grids.append(grid_info)
                # log_shortcut_restore(f"load_shortcut_grids_data: grid_info={grid_info}")
        except Exception as e:
            # log_shortcut_restore(f"load_shortcut_grids_data: Exception: {e}")
            pass
    return grids

def save_shortcut_grids_data(data_file, grids):
    data = {
        "grids": [
            {
                "name": grid['name'],
                "shortcuts": [
                    a.objectName() if hasattr(a, "objectName") else str(a)
                    for a in grid['actions']
                ]
            }
            for grid in grids
        ]
    }
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass
