# Krita Quick Access Manager

Krita Quick Access Manager is Krita Python plugin focused on a free-layout Quick Access Palette, gesture input,
quick brush/layer adjustments, and the HueSVC color selector.
The orignal concept was to bring the Clip Studio Paint's quick access palette to the krita.

![alt text](image/1_overview.png)


## Features

![alt text](image/2_quick_access_palette.png)
- **Quick Access Palette**: A tabbed, free-layout grid for brushes, Krita actions,
  docker toggles, colors, scripts, labels, separators, brush-size buttons, and
  brush-blend-mode buttons.

![alt text](image/3_gesture.png)
- **Gesture System**: Executes brush/action/docker commands through key + mouse
  directional gestures with preview support.

![alt text](image/4_quick_adjust.png) 
- **Quick Adjust Docker**: Brush and layer sliders/dropdowns, color history, brush
  history, temporary key modes, temporary brush sets, and floating Tool Options /
  Rotation widgets.

![alt text](image/5_huesvc.png)
- **HueSVC Color Selector**: Hue/SV color selector docker and popup. The popup also
  includes the shared brush/layer controls panel.

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

The Quick Access Palette is the main Remaster docker.

Documentation draft:

- Add/remove tabs.
- Add items from the header menu or Resources dialog.
- Use Ctrl + drag to move placed items directly in the docker.
- Use the popup action for cursor-centered access.

## Palette Item Types

Documentation draft:

| Item Type | Purpose | Size Behavior |
| --- | --- | --- |
| Brush | Switch to a brush preset | Fixed 1x1 |
| Action | Run a Krita action | Text mode defaults to 2x1 and is resizable; icon mode is fixed 1x1 |
| Docker Toggle | Show/hide a Krita docker | Text mode defaults to 2x1 and is resizable; icon mode is fixed 1x1 |
| Color | Set foreground color | Fixed 1x1 |
| Script | Execute a Python script | Text mode defaults to 2x1 and is resizable; icon mode is fixed 1x1 |
| Label | Display custom text | Resizable width |
| Separator | Horizontal or vertical separator | Resizable on its orientation axis |
| Brush Size | Set the active brush size | Fixed 1x1 |
| Brush Blend Mode | Set the active brush blend mode | Fixed 2x1 |

## Grid Edit

Documentation draft:

- Open Grid Edit from the palette header.
- Select one or more items.
- Move or resize supported item types.
- Right-click selected items to copy, move, or remove them.
- Use Undo for layout move/resize operations.

## Resources And Aliases

Documentation draft:

- Resources dialog tabs: Actions, Dockers, Brushes.
- Action and Docker entries can use aliases.
- Aliases can override display name, background color, and icon.
- Qt mnemonic ampersands in Krita action names are removed for display.

## Popup

Documentation draft:

- Quick Access Palette popup action.
- Toggle-close-on-repress behavior.
- Popup icon size and related settings.

## Gesture System

Documentation draft:

- Multiple gesture pages.
- Center action plus 8 directional actions.
- Supported targets: brush preset, Krita action, docker toggle.
- Gesture preview overlay.
- Temporary pause/resume support.

## Quick Adjust Docker

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

Main files:

- `quick_access_palette.json`: tabs, grids, and palette items.
- `settings.json`: shared Remaster settings.
- `alias_config.json`: action/docker alias settings.
- `gesture/`: gesture settings and per-page gesture config.

## Development Notes

Run the lightweight tests outside Krita:

```bash
python -m unittest discover -s tests -t . -v
```

The test suite covers pure model/layout/controller logic. Qt/Krita-dependent UI
features still need runtime testing inside Krita.
