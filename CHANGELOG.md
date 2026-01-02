# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 2026-01-02
### Added
- Popup configuration system (`popup.json`)
  - Configurable keyboard shortcuts for Actions Popup and Brush Sets Popup
  - Configurable appearance settings (brush icon size, grid label width)
  - All popup settings accessible via new "Popup" tab in Settings dialog
- `PopupConfigLoader` module for centralized popup configuration management
  - Singleton pattern ensures consistent configuration access
  - Automatic default configuration creation if file is missing
  - Runtime configuration updates with automatic file persistence
- System icon buttons for cleaner UI
  - Icon-based buttons in Quick Brush Sets docker (Add Brush, Add Grid, Gesture, Settings)
  - Icon-based buttons in Quick Actions docker (Actions, Add Grid)
  - Icon-based buttons in Gesture Config dialog (Add Config, Settings)
  - All buttons use consistent 18×18px icons with #828282 background color

### Changed
- Settings dialog now uses `QTabWidget` for cleaner tab interface
- Removed hardcoded popup shortcuts (`ActionsPopupShortcut`, `BrushSetsPopupShortcut`)
- Removed hardcoded appearance constants (`BrushIconSize`, `GridLabelWidth`)
- All popup-related constants now loaded from configuration file
- Popup shortcuts support both simple keys and key combinations (e.g., "Tab", "Ctrl+W")
- Docker control buttons replaced text labels with icons for more compact design
- Button sizes standardized to 22×22px across all dockers and dialogs

## 2025-12-25
### Added
- Gesture system status icon in status bar
  - Displays gesture on/off state next to alpha lock indicator
  - Click icon to toggle gesture system on/off
  - Updates in real-time to reflect current gesture state

## 2025-12-17
### Added
- Icon support for shortcut buttons
  - Buttons can now display PNG icons instead of text
  - Configure icon via button config dialog (Alt + right-click button)
  - Icon files stored in `config/icon/` directory
  - Grid-level `icon_size` parameter controls icon dimensions
- Grid-level configuration parameters
  - `max_shortcut_per_row`: Override global column count per grid
  - `icon_size`: Set icon size for buttons in the grid (required for icon display)
  - Access via grid parameter dialog (Alt + right-click grid name)
- Actions popup now supports icon buttons and grid-specific column settings

### Changed
- Button config dialog now reads button name from config data instead of button text (fixes empty name for icon buttons)
- Grid parameter dialog renamed from "rename_grid" to "edit_grid_parameter" with expanded functionality
- Text buttons use `setMinimumSize(QSize(40, 28))` for dynamic sizing
- Icon buttons automatically hide text when icon is present

### Fixed
- Layout spacing issues: grids now stay compact and don't expand when docker is resized
- Button config dialog showing empty name for icon buttons
- Grid column stretch properly applied to prevent unwanted expansion

## 2025-12-16
### Added
- Quick Adjust Docker configuration system (`quick_adjust_docker.json`)
  - Conditional widget creation based on enabled/disabled flags
  - Individual enable/disable controls for all sliders (size, opacity, rotation, layer opacity)
  - Configurable font sizes and number display sizes per slider
  - Configurable icon sizes and total items for history widgets
  - Custom blending modes list configuration
- Settings dialog with tabbed interface
  - Main tab for general plugin settings (color, font, layout)
  - Quick Adjust tab for docker-specific configuration
- Configuration loader module with automatic file creation
  - Creates default configuration file if missing
  - Provides getter functions for all configuration sections
  - Automatic recovery if config file is deleted

### Changed
- Quick Adjust Docker widgets are now dynamically created based on configuration
- Blend mode combo boxes only appear when their corresponding opacity sliders are enabled
- All hardcoded constants replaced with configuration-driven values
- Settings changes now reload the Quick Adjust Docker UI immediately

## 2025-12-06
### Changed
- Gesture system will be paused during individual shortcut button configuration 

## 2025-12-02
### Added
- Alias settings for gesture actions and docker toggles in preview overlay
  - Display custom names instead of internal action IDs
  - Support custom icons (PNG files) for actions and dockers
  - Configure aliases via JSON in the gesture settings dialog

### Changed
- Improved gesture preview overlay styling with better contrast and borders
- Gesture now support the backtick (`) key
