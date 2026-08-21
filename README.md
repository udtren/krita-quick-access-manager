# Krita Quick Access Manager

Krita Quick Access Manager is a Krita Python plugin focused on quickly accessing
various Krita resources by arranging them all in one place.
The original concept was to bring Clip Studio Paint's Quick Access palette to Krita.

![alt text](image/1_overview.png)


## Table of Contents

- [Quick Access Palette](#quick-access-palette)
- [Palette Item Types](#palette-item-types)
- [Grid Edit](#grid-edit)
- [Resources And Aliases](#resources-and-aliases)
- [Popup](#popup)
- [Gesture System](#gesture-system)
- [Quick Adjust Docker](#quick-adjust-docker)
- [HueSVC](#huesvc)
- [Settings](#settings)
- [Config Files](#config-files)
- [Development Notes](#development-notes)

## Quick Access Palette

![alt text](image/2_quick_access_palette.png)

The Quick Access Palette is the main docker used to manage quick access to
supported Krita resources and settings.

### Palette Item Types

The following item types are supported:

| Item Type | Purpose | Size Behavior |
| --- | --- | --- |
| Brush | Switch to a brush preset | Fixed 1x1 |
| Action | Run a Krita action | Text mode defaults to 2x1 and is resizable; icon mode is fixed 1x1 |
| Docker Toggle | Show/hide a Krita docker | Text mode defaults to 2x1 and is resizable; icon mode is fixed 1x1 |
| Color | Set foreground color | Fixed 1x1 |
| Brush Size | Set the active brush size | Fixed 1x1 |
| Brush Blend Mode | Set the active brush blend mode | Fixed 2x1 |
| Script | Execute a Python script | Text mode defaults to 2x1 and is resizable; icon mode is fixed 1x1 |
| Label | Display custom text | Resizable width |
| Separator | Horizontal or vertical separator | Resizable on its orientation axis |

### Resources And Aliases

To add a Brush, Action, or Docker Toggle item, click the **Resources** button
to open the Resources dialog. From there, pick a brush/action/docker and click
**Add** to place it on the palette.

For brushes, you can select multiple presets and add them all at once. You can
also use **Add Brush** in the header menu to add the currently active brush
preset directly.

Every other item type (Label, Separator, Color, Script, Brush Size, Brush
Blend Mode) is added from the header **Menu** button instead.

The Resources dialog also manages **aliases**: a custom display name, icon,
and color for a given Krita action or docker. Aliases are shared, so setting
one updates every Action/Docker Toggle item — and every Gesture binding — that
references that action or docker.

### Manage Item Property

Most item properties can be edited by right-clicking the item and choosing
**Property**. This opens a dialog where you can change the text, color, or
icon, depending on the item type.

For Action and Docker Toggle items, you can also edit these properties from
the Resources dialog, which updates the shared alias everywhere it's used.

### Move Item

Ctrl + left-drag moves a single item within the grid. You can remove an item
via its right-click menu, or drop it onto another item to push that item
aside and take its place. For multi-item selection, cross-tab moves, or
resizing, use Grid Edit.

### Grid Edit

Click **Grid Edit** to open the Grid Edit dialog, where you can:

- Select multiple items and move them together
- Select multiple items and copy/move them to another tab
- Resize text-mode items by dragging their edge
- Undo an accidental move or resize with the Undo button

### Popup

The Quick Access Palette can also open as a popup at the cursor position via
its shortcut. The popup shares the same tabs and items as the docker but is
execution-only — layout editing is only available in the docker.

The docker itself also supports **Move To Cursor**, which floats it and
centers it on the cursor (or re-docks it if it's already floating), letting
you reposition it without leaving the canvas.


## Gesture System
![alt text](image/3_gesture.png)

Documentation draft:

- Multiple gesture pages.
- Center action plus 8 directional actions.
- Supported targets: brush preset, Krita action, docker toggle.
- Gesture preview overlay.
- Temporary pause/resume support.

## Quick Adjust Docker
![alt text](image/4_quick_adjust.png)
Documentation draft:

- Brush controls: size, opacity, flow, blend mode, reset, rotation.
- Layer controls: opacity and blend mode.
- Color history and brush history.
- Temporary key modes:
  - Erase
  - Preserve Alpha
  - Select Outline
- Temporary brush sets.
- Floating Tool Options widget.
- Floating Rotation widget.

## HueSVC
![alt text](image/5_huesvc.png)
Documentation draft:

- Hue bar and SV box.
- H/S/V/R/G/B channel bars.
- Foreground/background color swatch.
- Docker and popup variants.
- Popup includes the shared brush/layer controls panel.

## Settings

Documentation draft:

- Default tab: columns, icon sizes, feature toggles, settings dialog size, tab style.
- Popup tab.
- HueSVC tab.
- Quick Adjust tab.

## Config Files

Remaster stores user configuration outside `pykrita`, under Krita's data folder:

```text
krita/
|- pykrita/
|  |- quick_access_manager/
|  `- quick_access_manager.desktop
`- quick_access_manager/
   `- remaster/
      |- quick_access_palette.json
      |- settings.json
      |- alias_config.json
      `- gesture/
         |- gesture.json
         `- config/
```

