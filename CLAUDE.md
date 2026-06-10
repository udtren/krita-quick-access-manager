# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Krita Python plugin (pykrita) that adds several workflow enhancement features: Quick Brush Sets docker, Quick Actions docker, Brush Adjustments docker, a gesture system, a HueSVC color selector, and preset XML config switching. It uses the Krita Python API and PyQt5/PyQt6.

## Installation / Development

No build step. To test changes, copy `quick_access_manager/` and `quick_access_manager.desktop` into Krita's pykrita folder and restart Krita:

- Source: `c:\Users\udtre\Projects\krita-plugin\quick_access_manager\`
- Install target: `C:\Users\udtre\AppData\Roaming\krita\pykrita\`

The installed copy is in the additional working directory `C:\Users\udtre\AppData\Roaming\krita\quick_access_manager` (config) and `C:\Users\udtre\AppData\Roaming\krita\pykrita\quick_access_manager` (plugin code).

There are no tests, no linter config, and no package manager. The `.venv` at the project root is for IDE support only.

## Architecture overview

### Entry point

[quick_access_manager/\_\_init\_\_.py](quick_access_manager/__init__.py) is the pykrita entry point. It:
1. Reads `performance_mode` from config at import time.
2. Registers `QuickAccessManagerExtension` (manages lifecycle), `ToggleGestureExtension`, and `SavePresetsExtension` via `Krita.instance().addExtension()`.
3. Registers all docker factories via `Krita.instance().addDockWidgetFactory()`.
4. Conditionally skips the heavy features (brush adjust docker, gesture system, HueSVC) when performance mode is on.

### Krita extension patterns

- **Dockers** are registered by subclassing `DockWidgetFactoryBase` and overriding `createDockWidget()`. The Krita 5/6 API changed `DockPosition` enum location — always use the `try/except AttributeError` pattern seen throughout the factories.
- **Actions/shortcuts** are registered by subclassing `Extension` and implementing `createActions(window)`.
- The gesture system uses `QApplication.instance().installEventFilter(self)` to capture all key and mouse events application-wide.

### Module map

| Module | Responsibility |
|--------|---------------|
| [quick_access_manager.py](quick_access_manager/quick_access_manager.py) | "Quick Brush Sets" docker — tab/grid/brush-preset management |
| [shortcut_manager.py](quick_access_manager/shortcut_manager.py) | "Quick Actions" docker — tab/grid/Krita-action button management |
| [brush_adjust/](quick_access_manager/brush_adjust/) | "Quick Brush Adjustments" docker — sliders, history, temp-action keys, floating widgets |
| [gesture/](quick_access_manager/gesture/) | Application-level key+mouse gesture detection and execution |
| [popup/](quick_access_manager/popup/) | Frameless popup windows: `BrushSetsPopup`, `ActionsPopup`, `PresetSwitchManager` |
| [color_selector/](quick_access_manager/color_selector/) | HueSVC docker and popup |
| [widgets/](quick_access_manager/widgets/) | Shared widget components: `DraggableBrushButton`, `DraggableGridContainer`, `SingleShortcutGridWidget`, `ShortcutPopup` |
| [dialogs/](quick_access_manager/dialogs/) | Settings dialogs and per-button config dialogs |
| [utils/](quick_access_manager/utils/) | `data_manager.py` (JSON load/save), `config_utils.py` (path resolution + cached config), `action_manager.py` (Krita action discovery) |
| [config/](quick_access_manager/config/) | Config loaders (`popup_loader.py`, `quick_adjust_docker_loader.py`), system icons, default JSON backups |
| [compat.py](quick_access_manager/compat.py) | PyQt5/PyQt6 shim — **always import Qt symbols from here**, never directly from PyQt5/PyQt6 |

### Configuration file layout

All user configs are stored **outside** pykrita so they survive plugin updates. Path resolution in [utils/config_utils.py](quick_access_manager/utils/config_utils.py) navigates up from `__file__` to find the krita data dir:

```
krita_data/ (e.g. AppData/Roaming/krita/)
├── pykrita/quick_access_manager/   ← plugin source code
└── quick_access_manager/
    ├── config/
    │   ├── common.json             ← global UI settings + performance mode flag
    │   ├── grids_data.json         ← brush sets (tabs/grids/preset names)
    │   ├── shortcut_grid_data.json ← action grids (tabs/grids/action IDs)
    │   ├── popup.json              ← popup shortcut keys and sizes
    │   ├── quick_adjust_docker.json← brush adjust docker options
    │   ├── docker_buttons.json     ← docker toggle button config
    │   └── icon/                   ← user-supplied PNG icons for buttons
    ├── gesture/
    │   ├── gesture.json            ← gesture settings (threshold, preview, alias)
    │   ├── config/1.json …         ← one file per gesture page (trigger key + 9 directions)
    │   └── icon/                   ← user-supplied icons for gesture preview overlay
    └── presets/
        └── {brush_name}.json       ← preset XML configs for the preset switcher
```

### Data format: tabs/grids

Both `grids_data.json` and `shortcut_grid_data.json` use the same top-level multi-tab structure:
```json
{ "tabs": [{ "name": "Tab 1", "grids": [...] }] }
```
Old single-tab format (`{"grids": [...]}`) is automatically migrated and backed up to `.bak` on first load. Migration logic is in `data_manager.py` (`load_tabs_data`, `load_shortcut_tabs_data`).

### Gesture system

`GestureDetector` (in [gesture/gesture_main.py](quick_access_manager/gesture/gesture_main.py)) is a `QObject` event filter installed on `QApplication`. It fires on `KeyPress`/`KeyRelease`/`MouseMove`. A module-level singleton `_gesture_manager: GestureManager` owns the detector instance. The public API exported from `gesture_main.py` (`initialize_gesture_system`, `pause_gesture_event_filter`, `resume_gesture_event_filter`, etc.) is what external callers use.

### Floating widget system

[brush_adjust/floating_widgets/base_tools/widget_pad.py](quick_access_manager/brush_adjust/floating_widgets/base_tools/widget_pad.py) provides `ntWidgetPad` — a frameless overlay widget that "borrows" an existing Krita docker and positions it relative to another docker or canvas edge. The positioning reference is configured via `WidgetPadPosition`. See [USAGE_EXAMPLES.md](quick_access_manager/brush_adjust/floating_widgets/base_tools/USAGE_EXAMPLES.md) for configuration examples and common Krita docker object names.

### PyQt compatibility

[compat.py](quick_access_manager/compat.py) tries `PyQt5` first, falls back to `PyQt6`, and then patches all the flat enum aliases PyQt5 used (`Qt.AlignLeft`, `QEvent.KeyPress`, etc.) back onto the PyQt6 namespaced versions. Every file in the plugin imports Qt symbols from `compat.py`.
