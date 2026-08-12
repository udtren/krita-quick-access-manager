# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

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
| [brush_adjust/](quick_access_manager/brush_adjust/) | "Quick Brush Adjustments" docker — sliders, history, temp-action keys, floating widgets; also home to `controls_builder.py`, `popup_controls_widget.py`, and `widgets/brush_toggle_widget.py`, all shared with the color selector popup |
| [gesture/](quick_access_manager/gesture/) | Application-level key+mouse gesture detection and execution |
| [popup/](quick_access_manager/popup/) | Frameless popup windows: `BrushSetsPopup`, `ActionsPopup`, `PresetSwitchManager` |
| [color_selector/](quick_access_manager/color_selector/) | HueSVC docker and popup — the popup also embeds `BrushLayerControlsWidget` and `BrushToggleWidget` from `brush_adjust/` as right-side panels |
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

### Shared brush/layer controls (docker + color selector popup)

[brush_adjust/controls_builder.py](quick_access_manager/brush_adjust/controls_builder.py) is the single source of truth for the brush/layer sliders and dropdowns (size, opacity, flow, blend mode, reset button, layer opacity, layer blend mode, rotation widget). `create_brush_layer_controls()` builds the individual widgets and assigns them as attributes on whatever widget is passed in; `build_docker_controls_layout()` and `build_popup_controls_layout()` arrange those same widgets differently for their two embedders:
- `BrushAdjustmentWidget` ([brush_adjust/adjustment_widget.py](quick_access_manager/brush_adjust/adjustment_widget.py)) — the Quick Brush Adjustments docker — uses `build_docker_controls_layout()` and reparents the rotation widget into a separate floating pad instead of placing it inline.
- `BrushLayerControlsWidget` ([brush_adjust/popup_controls_widget.py](quick_access_manager/brush_adjust/popup_controls_widget.py)) — embedded as the right-side panel of the color selector popup ([color_selector/color_selector_popup.py](quick_access_manager/color_selector/color_selector_popup.py)) — uses `build_popup_controls_layout()` (a simple vertical stack) and mixes in only `BrushMonitorMixin`/`LayerMonitorMixin` (no history widgets, docker toggle buttons, or global key listeners — those stay docker-only). Its `start_monitoring()`/`stop_monitoring()` are driven by the popup's `showEvent`/`hideEvent` so polling pauses while hidden.

The popup panel is sized to exactly 1/3 of the popup's total width (`color_selector_controls_panel_width` config adds to that total) and can be hidden entirely via `color_selector_controls_panel_enabled` (both in `popup.json`, editable from Settings → Popup tab).

### Brush pressure-toggle panel (preset XML editing)

[brush_adjust/widgets/brush_toggle_widget.py](quick_access_manager/brush_adjust/widgets/brush_toggle_widget.py) provides `BrushToggleWidget`, embedded below `BrushLayerControlsWidget` in the color selector popup's right panel (same `QVBoxLayout`, controlled independently via `color_selector_toggle_panel_enabled` in `popup.json`, default off). Unlike every other control in this plugin — which reads/writes brush state through `view.brushSize()`/`view.paintingOpacity()`/etc. — this widget edits the active preset's XML directly: `Preset(view.currentBrushPreset()).toXML()` → parse with `xml.etree.ElementTree` → flip the target `<param name="...">` element's text between `"true"`/`"false"` → `preset.fromXML(...)`. This is the same technique the sibling `CompactBrushToggler` plugin uses (see its AGENTS.md `### Preset XML manipulation`), including the workaround that strips a malformed `PatternMD5` CDATA block before parsing. It toggles 4 properties (`PressureSize`, `OpacityUseCurve`, `FlowUseCurve`, `PressureRotation`); `PressureSize`/`PressureRotation` each pair with a `SizeUseCurve`/`RotationUseCurve` sub-param that must be set alongside the primary one. `refresh_from_current_brush()` re-reads state on construction and on every popup `showEvent`, so switching brushes between opens doesn't leave stale button states.

### PyQt compatibility

[compat.py](quick_access_manager/compat.py) tries `PyQt5` first, falls back to `PyQt6`, and then patches all the flat enum aliases PyQt5 used (`Qt.AlignLeft`, `QEvent.KeyPress`, etc.) back onto the PyQt6 namespaced versions. Every file in the plugin imports Qt symbols from `compat.py`.
