# Quick Access Manager Remaster TODO

## Architecture

- `remaster/` is the sole active plugin entry point (`quick_access_manager/__init__.py` only loads `remaster/plugin.py`). `legacy/` is inactive, kept only as porting reference.
- `remaster/quick_access_palette/` (moved out of `remaster/features/`, which has been removed) — Quick Access Palette docker, popup, controller, dialogs, Alias Config dialog.
- `remaster/gesture/` — Gesture system (own config storage).
- `remaster/color_selector/` — HueSVC docker + popup.
- `remaster/quick_adjust/` — Quick Adjust docker (minus DockerButtonWidget, minus non-ToolOptions floating widgets).
- `remaster/infrastructure/` — `ActionManager`, `AliasRepository`, `DockerManager`, `PaletteRepository`, path helpers.
- `remaster/shared/` — shared models (`PaletteItem`, `PaletteGrid`, `PaletteTab`) and layout engine.
- Config files live outside pykrita under `AppData/Roaming/krita/quick_access_manager/remaster/`: `quick_access_palette.json` (grid/tab data only), `settings.json` (all settings, all features), `alias_config.json` (shared action/docker alias config), `gesture/` subfolder.

## Completed

### Palette Item Types
- [X] Docker toggle items, color picker/swatch items, script file execution items.
- [X] Per-item-type default size/icon/payload schema and config dialog fields.
- [X] Vertical Separator orientation (`payload.orientation`, header menu "Add H Separator" / "Add V Separator") alongside the original horizontal one. A vertical Separator resizes by `row_span` instead of `col_span`; Grid Edit's Wider/Narrower buttons and the drag resize handle both switch axis automatically based on the selection.
- [X] Brush Size item (`BRUSH_SIZE_ITEM`, header menu "Add Brush Size"): a fixed 1x1 button showing a digits-only number (text/font size/font color/background color set via a config popup at add time and from the right-click Property menu). Click sets the active brush's size to that number via `view.setBrushSize()`. Not resizable in Grid Edit (fixed 1x1, like Color Swatch/Script).
- [X] Brush Blend Mode item (`BRUSH_BLEND_MODE_ITEM`, header menu "Add Brush Blend Mode"): a fixed 2x1 button showing free-text (a Krita blend mode id, e.g. "multiply" - not restricted to `quick_adjust`'s `blender_mode_list`, which is only a dropdown curation list, not a validator) with the same text/font size/font color/background color popup and right-click Property editing as Brush Size. Click sets the active brush's blend mode via `view.setCurrentBlendingMode()`, the same call `quick_adjust/brush_monitor.py`'s blend combo uses. Not resizable in Grid Edit.

### Alias Config
- [X] Shared Alias Config system (`AliasRepository` + `AliasConfigDialog`) for custom name/color/icon per Krita action or docker, wired into Action/DockerToggle items and Gesture.

### Gesture System
- [X] Full migration to `remaster/gesture/` with its own config storage, independent from the palette settings.

### HueSVC (Color Selector)
- [X] Docker migration (`remaster/color_selector/docker.py`).
- [X] Popup migration (`remaster/color_selector/popup.py`) — color picker only; the legacy embedded brush/layer controls panel was intentionally not ported.
- [X] Popup shortcut (`hue_svc_popup` action in `actions.action`) with toggle-close-on-repress behavior identical to the Quick Access Palette popup.
- [X] Popup width/height configurable from the Settings dialog's HueSVC tab.

### Quick Adjust
- [X] Docker migration minus `DockerButtonWidget` and all floating widgets except Tool Options.
- [X] Temp Brush Set settings exposed in the Settings dialog.

### Settings / Config Dialog
- [X] Split settings out of `quick_access_palette.json` into a dedicated `settings.json` (grid file now holds only tab/grid data).
- [X] Settings dialog renamed to "Settings"; vertical scrollbar added; configurable dialog width/height.
- [X] "Features" section with Gesture/HueSVC/Quick Adjust enable checkboxes, wired into `plugin.py`'s conditional docker registration.
- [X] Active-vs-other tab bar styling (font size/color, background color) in the Default tab, applied via `QTabBar::tab`/`QTabBar::tab:selected` in both the docker and popup. One shared style pair across all tabs, not per-tab.

### Grid Editing
- [X] Marquee (rubber-band) multi-select.
- [X] Move/resize undo (history stack, `Undo` button).
- [X] Overflow markers in normal Docker view when column reduction leaves items outside the grid.
- [X] **Multi-tab Grid Edit**: all tabs are shown as pages in one dialog instead of only the active tab; per-tab item/selection/history state is preserved when switching tabs.
- [X] Right-click context menu on selected item(s) to **Copy to Tab** / **Move to Tab**; items land below the target tab's last existing row (same placement rule as adding a new item).
- [X] Fixed: initial item selection not showing the highlight border until after the first move (stale `item_widgets` reference not synced back into per-tab state during dialog init).
- [X] Fixed: cross-tab copy/move not reflected in real time when the target tab wasn't the one currently shown (added `_rebuild_tab()` to rebuild any tab's canvas immediately, not just the active one).

### Performance
- [X] Removed dead `ActionManager.get_actions_dict()` call in the palette popup's `__init__` (was doing a full recursive Krita main-window widget-tree scan on every popup open, unused result).
- [X] Cached `AliasRepository().load()` once per popup/controller construction instead of reloading from disk per grid item (was happening once per item in both `PaletteController.normalize_action_spans()` and the popup's `alias_entry()`).

### Cleanup
- [X] Removed unused empty `remaster/core/` and `remaster/ui/` placeholder packages.
- [X] Moved `remaster/features/quick_access_palette/` to `remaster/quick_access_palette/` and removed the now-empty `remaster/features/` package.
- [X] Maintainability split of the largest files, done in 6 mechanical, behavior-preserving steps (each verified with `tests/` + `py_compile` and committed separately):
  1. `quick_access_palette/item_style_mixin.py`: `ItemStyleMixin` shared by the docker and popup for item styling/icon lookups (`apply_action_style`, `apply_label_style`, `apply_brush_size_style`, `apply_brush_blend_mode_style`, `tab_bar_stylesheet`, `resolve_icon_path`, `alias_entry`, `item_icon_size`) - previously duplicated in both files, meaning every new palette item type needed the same style edit twice.
  2. `quick_access_palette/dialogs.py` (2119 lines) → `dialogs/` package: `item_config_dialogs.py` (the 7 per-item-type config dialogs), `palette_settings_dialog.py` (`PaletteConfigDialog`), `grid_edit/{canvas,item_button,dialog}.py` (the Grid Edit feature). `dialogs/__init__.py` re-exports everything.
  3. `quick_access_palette/controller.py` (683 lines, one class) → `controller/` package: `settings_mixin.py`, `tab_mixin.py`, `placement_mixin.py`, `item_crud_mixin.py`, composed by `base.py`'s `PaletteController`. `controller/__init__.py` re-exports `PaletteController`/`DEFAULT_SETTINGS`.
  4. `quick_access_palette/docker.py` (1103 lines, one class) → `docker/` package: `drag_filter.py`, `ui_builder_mixin.py`, `item_rendering_mixin.py`, `item_actions_mixin.py`, `activation_mixin.py`, `alias_bridge_mixin.py`, composed by `widget.py`'s `QuickAccessPaletteDockerWidget`, plus `factory.py`. `docker/__init__.py` re-exports the public names.
  5. `color_selector/docker.py` (698 lines): extracted the generic, docker-independent `HueBar`/`SVBox`/`ChannelBar`/`FgBgColorWidget` widgets into `color_selector/widgets/`.
  6. `gesture/gesture_config_dialog.py` (672 lines): extracted the self-contained `KeyCaptureDialog` into its own `gesture/key_capture_dialog.py`.

  Every step kept the pre-existing import surface (`from .dialogs import X`, `from .controller import PaletteController`, `from .quick_access_palette.docker import QuickAccessPaletteDockerFactory`, etc.) unchanged via `__init__.py` re-exports, so no caller needed editing.

## Open Items

### Popup
- [ ] Add screen-edge clamping so the cursor-centered popup never opens partly outside the visible screen.
- [ ] Decide whether Pin state should be runtime-only or persisted in config.
- [ ] Add optional popup width/height settings if icon-size-only control is not enough (already done for HueSVC popup; still open for the Quick Access Palette popup).

### Grid Editing
- [X] Add drag resize handles for Label and Separator width changes (right-edge grip on the item button; Wider/Narrower buttons still work too).
- [ ] Extend multi-select UX: Shift+click range selection, Ctrl+A select-all, Escape-to-clear.
- [ ] Add "confirm discard on close if dirty" safety net around Grid Edit changes (undo history currently covers move/resize only).
- [X] Horizontal-only drag resize for Action item width (col_span) in Grid Edit, reusing the Label/Separator resize handle/axis machinery via `GridEditDialog.is_resizable()`. An icon-mode Action (has an alias icon) is excluded - it's pinned to col_span=1 by `PaletteController._action_col_span()` on every load, so widening it in Grid Edit would just get silently reverted; `is_resizable()` hides the grip/cursor for it entirely rather than letting the resize appear to work.
- [ ] Full free-size Action items (and other text buttons) beyond the col_span-only resize above: row_span resizing plus auto text wrap for a tall/narrow layout. Deferred - needs (1) reworking `PaletteController._action_col_span()`/`normalize_action_spans()`'s min-2 floor so a manual narrower-than-2 resize sticks across reload, (2) extending Grid Edit's resize UI from single-axis to independent row+col handles on one item, and (3) a custom word-wrapping button widget since QPushButton has no native wrap (QLabel overlay or custom paintEvent). Scope decision still open: Action items only, or also Docker Toggle's text-fallback mode.

### Tabs And Config
- [ ] Consider per-tab or per-grid column settings UI if one global active-grid column control becomes confusing.
- [ ] Add explicit tab ordering/reorder support.
- [ ] Confirm whether tab removal should ask for confirmation when the tab contains items.

### Action / Label Properties
- [ ] Add icon preview to the Action property dialog.
- [ ] Add a clear-icon option to the Action property dialog.
- [ ] Consider shared color-button helper for Action and Label property dialogs.

### Packaging / Cleanup
- [ ] Update `SPEC.md` so it matches current decisions: no UseGlobalSetting, Label/Separator width-only resize, popup shortcut behavior, new settings tabs, multi-tab Grid Edit, and the `remaster/quick_access_palette/` path (no longer under `features/`).
- [ ] Review `actions.action` placement and confirm Krita reliably discovers it from the remaster folder.
- [X] Add lightweight model/layout tests that can run outside Krita (`tests/`, stdlib `unittest`, covers `shared/` and `quick_access_palette/controller.py`; `AliasRepository` gained a `path` constructor param and `PaletteController` an `alias_repository` param so tests never touch the real Krita config dir).
- [ ] Runtime-test all migrated features inside actual Krita — everything so far has only been verified via static diagnostics (`get_errors`), never run inside Krita.
