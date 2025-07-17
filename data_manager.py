import os
import json

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
