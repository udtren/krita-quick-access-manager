# Krita Quick Access Manager

A plugin for Krita that provides quick access to brush presets and shortcut management.

The purpose of creating this plugin was to have a function similar to the Quick Access Tool in Clip Studio Paint.

![Sample](./quick_access_manager/image/000.jpg)
---

## How to Add a Brush Preset
1. In the "Quick Brush Access" section, activate the grid you want to add to.
2. Select the brush preset you want to add from Krita's brush preset.
3. Click the "AddBrush" button in the docker.
4. The selected preset will be added to the active grid.
![How to Add a Brush Preset](./quick_access_manager/image/image1.jpg)

## How to Add a Shortcut. 
1. In the "Quick Shortcut Access" section, activate the grid you want to add to.
2. Click the "ShowAllShortcut" button to open the shortcut selection popup.
3. Select the action you want to add from the table.
4. Click the "AddShortCut" button.
5. The selected shortcut will be added to the active grid.
![How to Add a Shortcut](./quick_access_manager/image/image2.jpg)

## How the config restore works
When Krita starts, the brush preset settings will be loaded automatically.

However, the shortcut settings will not be loaded automatically because it is difficult to track the timing when Krita loads all shortcut actions.

Therefore, you need to click the [RestoreShortcutGrid] button manually to restore the shortcut settings.

## Resize Docker
When resizing the docker, please do it slowly.

If you resize too quickly, small Brush Preset popup windows may appear repeatedly, and you will need to close them manually.

## Sort/Remove

**Sort:**  
To reorder a brush or shortcut button within a grid or move it between grids, hold <kbd>Ctrl</kbd> and left-click and drag the button to the desired position or grid.

**Remove:**  
To remove a brush or shortcut from a grid, hold <kbd>Ctrl</kbd> and right-click on the button you want to remove.

**Remove Grid:**  
To delete an entire grid, click the "Remove" button located at the top right of each grid's header.

## Config file

The configuration files for grids and shortcuts are stored in `./quick_access_manager/config`.

- `grids_data.json`: Stores the brush preset grids.
- `shortcut_grid_data.json`: Stores the shortcut grids.
- `common.json`: Stores UI and layout settings.

**Note:**  
There is no profile management function, but you can manually edit these files while Krita is closed.  
If you want to reset or backup your settings, you can copy or edit these files directly.

## Other Usage 
- Add a new grid: Click the "AddGrid" button to create a new grid.
- Rename a grid: Use the "Rename" button to edit the grid name.
- Reorder grids: Use the "↑" and "↓" buttons to change the grid order.
- Change settings: Use the "Setting" button to edit UI and layout settings.
![Setting](./quick_access_manager/image/image3.jpg)

## Notes- If you edit config files directly, please close Krita first.
