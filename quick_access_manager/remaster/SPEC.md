# Quick Access Palette Remaster Spec

## Scope

Quick Access Palette replaces the legacy Quick Brush Sets and Quick Actions dockers.
The legacy dockers are not registered in the remastered version.

## Data Model

Palette data is new-only. Legacy `grids_data.json` and `shortcut_grid_data.json` are not migrated.

```text
tabs[]
  grids[]
    items[]
      type: brush | action | label | separator | docker_toggle | color | script
      row: int
      col: int
      row_span: int
      col_span: int
      payload: type-specific settings
```

## Layout

The palette uses a free-layout GridContainer.

- Brush and Action items can coexist in the same tab and grid.
- Brush items are fixed at 1x1 cell.
- Action items use the same grid unit, but may span multiple columns and rows.
- Labels and separators are grid items so they can be placed, moved, and stored consistently.
- Reducing the configured column count must not delete item data. Overflowing items are preserved and shown in an overflow/invalid-placement state until the user resolves the layout.
- When an item is dropped onto occupied cells, the existing items are pushed forward instead of being overwritten or swapped.
- The default Action item size is 2x1 cells.
- Label and Separator items can be resized by dragging their resize handles to change `col_span` and `row_span`.

## Action Item Configuration

When adding an Action item, open a popup configuration dialog based on the legacy `ShortcutButtonConfigDialog` fields:

- Button name
- Font size
- Background color
- Font color
- Icon name
- Use global settings

The remastered dialog should operate on an item config object, not on a live legacy button instance.

## Docker Toggle / Color / Script Items

All three item types are fixed at 1x1 cells and rendered as icon-first buttons, matching the icon variant of Action items.

- Docker toggle: `payload = {docker_id, customName, icon_name}`. Discovers dockers via `QDockWidget` children of the active Krita main window and toggles their visibility on click.
- Color swatch: `payload = {color}`. Clicking sets the active view's foreground color; the button itself is rendered filled with the stored color instead of an icon.
- Script execution: `payload = {script_path, customName, icon_name}`. Clicking executes the selected `.py` file's contents with a minimal globals dict (`Krita` only). Errors are shown in a message box instead of raising.

Config dialogs for these three types follow the same "config object in, dict out" pattern as `ActionItemConfigDialog`/`LabelItemConfigDialog`.

## Popup

The shortcut-opened popup dialog shares the same tabs, grids, and item data as the Docker.
Popup-specific settings should only control presentation details such as size, position, and pin behavior.
The popup is execution-only: items can be triggered from it, but layout editing is only available in the Docker.

## Bundled Icons

Default action icons are bundled in:

```text
quick_access_manager/remaster/resources/default_icons/
```

These icons are copied from the user's current Krita config icon folder and should be treated as plugin-provided defaults for the remastered palette.
## Resolved Interaction Decisions

- Collision behavior: push existing items forward.
- Column-count overflow: keep item data and show invalid/overflow placement.
- Default Action size: 2x1 cells.
- Label/Separator resizing: drag resize handles.
- Popup editing: disabled; popup is execution-only.