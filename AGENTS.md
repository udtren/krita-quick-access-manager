# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What this is

A Krita Python plugin (pykrita). The active implementation is the **Quick Access Palette** — a single free-layout grid docker/popup that replaces the legacy Quick Brush Sets and Quick Actions dockers — plus a Quick Adjust docker (brush/layer sliders + history), a HueSVC color selector, and a gesture system.

## Installation / Development

No build step. To test changes, copy `quick_access_manager/` and `quick_access_manager.desktop` into Krita's pykrita folder and restart Krita:

- Source: `c:\Users\udtre\Projects\krita-plugin\quick_access_manager\`
- Install target: `C:\Users\udtre\AppData\Roaming\krita\pykrita\`

The installed copy is in the additional working directory `C:\Users\udtre\AppData\Roaming\krita\quick_access_manager` (config) and `C:\Users\udtre\AppData\Roaming\krita\pykrita\quick_access_manager` (plugin code).

There is no linter config and no package manager. The `.venv` at the project root is for IDE support only.

A `tests/` directory at the repo root holds a lightweight `unittest` suite that runs **outside Krita** — no `krita` module, no PyQt install needed. It covers `remaster/shared/` (pure layout/model logic) and `remaster/quick_access_palette/controller.py` (document mutations), both of which have no Qt dependency. Everything that imports `compat.py` (dockers, popups, dialogs, gesture, color_selector, quick_adjust) is out of scope for it — that needs a real PyQt5/PyQt6 install to import at all, and can only really be exercised inside Krita. Run it from the repo root:

```
python3 -m unittest discover -s tests -t . -v
```

## Architecture overview

### Entry point and active vs. legacy code

`remaster/` is the **sole active plugin namespace**. `legacy/` sits alongside it and is kept only as porting reference — its dockers are never registered.

[quick_access_manager/\_\_init\_\_.py](quick_access_manager/__init__.py) just does `from .remaster.plugin import *`, swallowing the `ModuleNotFoundError` for `krita` so the package still imports (e.g. for the `tests/` suite) outside Krita.

[remaster/plugin.py](quick_access_manager/remaster/plugin.py) is the real Krita registration entry point. `QuickAccessPaletteExtension.setup()`:
1. Always registers the Quick Access Palette docker factory.
2. Conditionally registers the HueSVC docker (`controller.is_huesvc_enabled()`) and Quick Adjust docker (`controller.is_quick_adjust_enabled()`).
3. Conditionally initializes the gesture system (`is_gesture_enabled()`).

It also registers two popup actions (`quick_access_palette_popup`, `hue_svc_popup`), each with toggle-close-on-repress behavior tracked via a module-level `_popup_window`/`_huesvc_popup_window` singleton (so a shortcut press closes an already-open popup instead of stacking a second one, even across separate `QuickAccessPaletteExtension` instances).

### Krita extension patterns

- **Dockers** are registered by subclassing `DockWidgetFactoryBase` and overriding `createDockWidget()`. The Krita 5/6 API changed `DockPosition` enum location — always use the `try/except AttributeError` pattern seen throughout the factories.
- **Actions/shortcuts** are registered by subclassing `Extension` and implementing `createActions(window)`.
- The gesture system uses `QApplication.instance().installEventFilter(self)` to capture all key and mouse events application-wide.

### Module map (`quick_access_manager/remaster/`)

| Module | Responsibility |
|--------|---------------|
| [quick_access_palette/](quick_access_manager/remaster/quick_access_palette/) | The Quick Access Palette: `docker.py` (docker widget + rendering + drag-move), `popup.py` (execution-only popup, mirrors the docker's renderers), `controller.py` (`PaletteController` — all document mutations and settings), `dialogs.py` (per-item-type config dialogs + `GridEditDialog`), `alias_config_dialog.py` (shared "Resources" dialog for Action/Docker aliases and bulk Add) |
| [shared/](quick_access_manager/remaster/shared/) | `models.py` (`PaletteItem`, `PaletteGrid`, `PaletteTab`, `PaletteDocument` — Krita/Qt-free) and `layout_engine.py` (`FreeGridLayoutEngine` — placement/overlap/bounds/compact, also Krita/Qt-free). This is what `tests/` exercises directly. |
| [infrastructure/](quick_access_manager/remaster/infrastructure/) | `PaletteRepository`/`AliasRepository` (JSON load/save, both take an optional `path`/constructor override for test isolation), `json_cache.py` (mtime-validated read cache), `paths.py` (config dir resolution), `ActionManager`/`DockerManager` (Krita action/docker discovery — `None` outside Krita, see below) |
| [gesture/](quick_access_manager/remaster/gesture/) | Application-level key+mouse gesture detection and execution; own config storage under `remaster/gesture/` |
| [color_selector/](quick_access_manager/remaster/color_selector/) | HueSVC docker + popup. Unlike the legacy popup, the popup's right-side panel (`BrushLayerControlsWidget`/`BrushToggleWidget`, both imported from `quick_adjust/`) is always shown, not config-gated. |
| [quick_adjust/](quick_access_manager/remaster/quick_adjust/) | Brush/layer adjustment docker: sliders, color/brush history, temp-action keys, Tool Options floating pad. Ported from legacy minus `DockerButtonWidget` and every floating widget except Tool Options. |
| [compat.py](quick_access_manager/remaster/compat.py) | PyQt5/PyQt6 shim — **always import Qt symbols from here**, never directly from PyQt5/PyQt6 |
| [focus_utils.py](quick_access_manager/remaster/focus_utils.py) | `is_text_input_focused()` — used by the gesture system to avoid firing gestures while the user is typing |
| [actions.action](quick_access_manager/remaster/actions.action) | Krita action registration XML for the popup shortcuts |
| [resources/](quick_access_manager/remaster/resources/) | Bundled default icons (`default_icons/`, `system_icons/`, `quick_adjust/`, `gesture/`) |

`ActionManager`/`DockerManager` (from `infrastructure/`) are `None` when the `krita` module isn't importable — `infrastructure/__init__.py` catches that specific `ModuleNotFoundError` so the rest of `infrastructure/` (and everything built on `PaletteRepository`/`AliasRepository`) still imports cleanly outside Krita.

### Configuration file layout

All user configs are stored **outside** pykrita so they survive plugin updates. [infrastructure/paths.py](quick_access_manager/remaster/infrastructure/paths.py) navigates up from `__file__` to find the krita data dir (`get_krita_data_dir()` assumes the standard `krita_data/pykrita/quick_access_manager/` install layout — see the caveat below):

```
krita_data/ (e.g. AppData/Roaming/krita/)
├── pykrita/quick_access_manager/          ← plugin source code (legacy/ + remaster/)
└── quick_access_manager/remaster/
    ├── quick_access_palette.json          ← tab/grid/item data only
    ├── settings.json                      ← all settings, all features (docker icon size, tab bar style, HueSVC, Quick Adjust, ...)
    ├── alias_config.json                  ← shared action/docker alias config (custom name/color/icon)
    └── gesture/
        ├── gesture.json                   ← gesture settings (threshold, preview, alias)
        └── config/1.json …                ← one file per gesture page (trigger key + 9 directions)
```

**Test isolation caveat:** `PaletteRepository()`/`AliasRepository()` constructed with no path override resolve to this real Krita data dir and `os.makedirs()` it on first use — including when just running outside a real Krita install (e.g. from a repo checkout, the resolved "krita data dir" is one level above the repo root (`dirname(dirname(quick_access_manager/))`)). Any code that needs to run outside Krita (tests, scripts) must pass explicit `path=`/`settings_path=` overrides — both repositories, and `PaletteController.__init__(repository=..., alias_repository=...)`, accept them for exactly this reason.

### Data model: the free-layout grid

`PaletteDocument` → `tabs: [PaletteTab]` → `grids: [PaletteGrid]` → `items: [PaletteItem]`. A grid has a `columns` count; each item has `row`/`col`/`row_span`/`col_span` and a `type`-specific `payload` dict. Item types (`shared/models.py`):

| Type | Fixed size? | Notes |
|------|-------------|-------|
| `brush` | 1x1 (enforced in `__post_init__`) | `payload.brush_name` |
| `action` | default 2x1, resizable (col only unless icon-mode) | `payload.action_id`; col_span floored to 2 (or pinned to 1 if the alias has an icon) by `PaletteController._action_col_span()`/`normalize_action_spans()` on every load |
| `label` | row fixed at 1, col resizable | `payload.text/fontSize/backgroundColor/fontColor` |
| `separator` | horizontal: row=1, col resizable; vertical: col=1, row resizable (`payload.orientation`) | see "Separator orientation" below |
| `docker_toggle` | 1x1 | `payload.docker_id` |
| `color` | 1x1 | `payload.color` — sets the active view's foreground color |
| `script` | 1x1 | `payload.script_path` — executes the file with a minimal globals dict (`Krita` only) |
| `brush_size` | 1x1, never resizable | `payload.text` (digits only) `/fontSize/backgroundColor/fontColor` — click sets the active brush's size via `view.setBrushSize()` |

Placement rules (`FreeGridLayoutEngine` in `shared/layout_engine.py`, fully generic over `row_span`/`col_span` — no item-type special-casing at the engine level):
- Dropping/adding an item onto occupied cells pushes the *existing* items to the next free cell; the newly placed/moved item always keeps its requested position.
- Reducing the column count never deletes items — overflowing items are kept and flagged via `LayoutResult.issues` (shown as an error-styled border in the docker).
- `compact()` packs items left-to-right/top-to-bottom without holes, used by "Compact" operations, not on every load.

**Sequential placement** (`PaletteController.begin_sequential_placement()`/`end_sequential_placement()`): while the Resources ("Add" from the alias/brush picker) dialog is open, new items fill the grid's last row left-to-right and wrap to the next row, instead of each Add starting a fresh row (the default behavior for header-menu Adds, via `_resolve_position()`'s "row below the last item" fallback). The cursor is scoped to the grid it was opened on and is inert if the active tab changes mid-session.

**Separator orientation**: `payload.orientation` is `"horizontal"` (default) or `"vertical"`. A horizontal separator's `col_span` is the resizable axis; a vertical one's `row_span` is. `GridEditDialog.resize_axis(item)` picks the axis per item, so the drag-resize handle and the Wider/Narrower buttons (relabeled Taller/Shorter for a "row"-axis selection) both adapt automatically; a mixed-axis multi-selection disables resizing rather than guessing.

### Grid Edit dialog

`GridEditDialog` (`quick_access_palette/dialogs.py`) edits every tab's grid without auto-compacting on save. Notable pieces:
- Marquee (rubber-band) multi-select, Copy/Move-to-Tab context menu.
- `GridEditItemButton` supports both a whole-item drag (move) and, for resizable types, an edge-grip drag (resize) — which edge and which cursor depends on `resize_axis()`/`is_resizable()`.
- `is_resizable(item)` centralizes "can this item be resized here": Label and Separator always; Action only when its alias has no icon (an icon-mode Action is pinned to `col_span=1` by the controller, so offering a resize handle that gets silently reverted would be misleading); everything else (Brush, Docker Toggle, Color, Script, Brush Size) never.
- Undo history covers move/resize only (not add/remove).

The docker itself also supports one direct manipulation: **Ctrl + left-drag** on a placed item moves it within the active grid (`GridItemDragFilter` in `docker.py`), independent of opening Grid Edit.

### Tab bar styling

The docker/popup's `QTabWidget` gets a `QTabBar::tab` / `QTabBar::tab:selected` stylesheet built from `PaletteController.tab_bar_settings()` (font size/color, background color, one shared pair for Active vs. every other tab — not per-tab), reapplied on every `reload_tabs()`. Configurable from Settings → Default tab.

### Gesture system

`GestureDetector` (in [gesture/gesture_main.py](quick_access_manager/remaster/gesture/gesture_main.py)) is a `QObject` event filter installed on `QApplication`. It fires on `KeyPress`/`KeyRelease`/`MouseMove`. A module-level singleton owns the detector instance; the public API exported from `gesture/__init__.py` (`initialize_gesture_system`, `pause_gesture_event_filter`, `resume_gesture_event_filter`, etc.) is what external callers use. Its own config lives under `remaster/gesture/` (see file layout above), independent of the palette's `settings.json`.

### Shared brush/layer controls (Quick Adjust docker + HueSVC popup)

[quick_adjust/controls_builder.py](quick_access_manager/remaster/quick_adjust/controls_builder.py) is the single source of truth for the brush/layer sliders and dropdowns (size, opacity, flow, blend mode, reset button, layer opacity, layer blend mode, rotation widget). `create_brush_layer_controls()` builds the individual widgets; `build_docker_controls_layout()` and `build_popup_controls_layout()` arrange those same widgets differently for their two embedders:
- `BrushAdjustmentWidget` ([quick_adjust/adjustment_widget.py](quick_access_manager/remaster/quick_adjust/adjustment_widget.py)) — the Quick Adjust docker — uses `build_docker_controls_layout()` and reparents the rotation widget into a separate floating pad instead of placing it inline.
- `BrushLayerControlsWidget` ([quick_adjust/popup_controls_widget.py](quick_access_manager/remaster/quick_adjust/popup_controls_widget.py)) — embedded as the right-side panel of the HueSVC popup — uses `build_popup_controls_layout()` (a simple vertical stack) and mixes in only `BrushMonitorMixin`/`LayerMonitorMixin` (no history widgets, docker toggle buttons, or global key listeners — those stay docker-only). Its `start_monitoring()`/`stop_monitoring()` are driven by the popup's `showEvent`/`hideEvent`.

### Floating widget system

[quick_adjust/floating_widgets/tool_options.py](quick_access_manager/remaster/quick_adjust/floating_widgets/tool_options.py) (`FloatToolOptions`) is the one floating widget ported from legacy — it "borrows" Krita's own Tool Options docker (`sharedtooldocker`) and repositions it via `ntWidgetPad`/`WidgetPadPosition`. Every other legacy floating widget (widget pads for other dockers) was intentionally not ported.

### PyQt compatibility

Both `legacy/compat.py` and [remaster/compat.py](quick_access_manager/remaster/compat.py) try `PyQt5` first, fall back to `PyQt6`, and then patch the flat enum aliases PyQt5 used (`Qt.AlignLeft`, `QEvent.KeyPress`, `QFrame.HLine`/`VLine`, `QRubberBand.Rectangle`, etc.) back onto the PyQt6 namespaced versions. Every file under `remaster/` imports Qt symbols from `remaster/compat.py` — never directly from PyQt5/PyQt6, and never from `legacy/compat.py`.

### Legacy namespace

`quick_access_manager/legacy/` is the pre-rewrite implementation (separate Quick Brush Sets docker, Quick Actions docker, Brush Adjustments docker with its own docker-toggle-button row and full floating-widget set, preset XML pressure-toggle panel, preset switcher). It is not imported by `quick_access_manager/__init__.py` and its dockers are never registered — kept only as a reference for porting remaining functionality into `remaster/`. Treat any AGENTS.md-adjacent notes about `quick_access_manager.py`, `shortcut_manager.py`, `brush_adjust/`, `popup/`, `widgets/`, `dialogs/`, `utils/`, `config/` at the top level of `quick_access_manager/` as describing `legacy/`, not the active plugin.

### Remaster's own docs

[remaster/TODO.md](quick_access_manager/remaster/TODO.md) tracks completed work and open items in detail (grid editing, settings, per-feature status). [remaster/SPEC.md](quick_access_manager/remaster/SPEC.md) is the original design spec for the palette rewrite — it predates several since-implemented features (e.g. it doesn't mention the `brush_size` item type or vertical separators) and is flagged in TODO.md as needing a refresh; prefer this file and TODO.md over SPEC.md when they disagree.
