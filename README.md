# Krita Quick Access Manager

A plugin for Krita that provides quick access to brush presets and shortcut management.

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

## Other Usage 
- Add a new grid: Click the "AddGrid" button to create a new grid.
- Rename a grid: Use the "Rename" button to edit the grid name.
- Reorder grids: Use the "↑" and "↓" buttons to change the grid order.
- Sort a brush or shortcut: Ctrl + left-click on the icon/button to move it inside the same or different grid.
- Remove a brush or shortcut: Ctrl + right-click on the icon/button to remove it from the grid.
- Change settings: Use the "Setting" button to edit UI and layout settings.

## Notes- If you edit config files directly, please close Krita first.
