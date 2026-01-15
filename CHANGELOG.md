# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 2026-01-14
### Added
- Preserve Alpha toggle button in Quick Adjust Docker control panel
  - Click to toggle Krita's preserve alpha mode on/off
  - Visual indicator shows current preserve alpha status

### Changed
- Floating Tool Options widget now checks Krita's `ToolOptionsInDocker` setting before initialization
  - Only enables when Tool Options is set to "In Docker" mode (not "In Toolbar" mode)
  - Prevents conflicts and ensures proper widget borrowing from docker
  - Toggle button automatically hidden when Tool Options is in Toolbar mode

## 2026-01-13
### Added
- Docker buttons configuration system (`docker_buttons.json`)
  - Configure docker toggle buttons via Settings dialog under "Quick Adjust" tab
  - Add/remove docker buttons dynamically through UI
  - Customize button properties: name, width, icon, keywords, and description
  - Docker keywords used to match and toggle corresponding Krita docker panels
  - Default configuration auto-created if file doesn't exist
  - Changes saved to `config/docker_buttons.json` file
- Docker buttons UI editor in Settings dialog
  - Add new docker button configurations with "Add Button" button
  - Remove existing configurations with "Remove This Button" button
  - Group box for each button with all editable fields
  - Real-time group box title update when button name changes
  - Validation and parsing for button width (integer) and keywords (comma-separated list)
- Flexible widget positioning system for floating widgets
  - New `WidgetPadPosition` configuration class for positioning widgets relative to any Krita docker
  - Support for all four sides (LEFT, RIGHT, TOP, BOTTOM) relative to reference docker
  - Alignment options: ALIGN_TOP/ALIGN_BOTTOM for vertical sides, ALIGN_LEFT/ALIGN_RIGHT for horizontal sides
  - Configurable gap between widgets
  - Optional fallback to canvas edge positioning when reference docker not found/visible
  - Comprehensive usage examples and documentation in USAGE_EXAMPLES.md
- Floating Tool Options widget positioned relative to Quick Brush Adjust docker
  - Tool Options widget now appears to the left of the Brush Adjust docker
  - Dynamic positioning with 5px gap between widgets
  - Event filter system tracks docker movement, resize, and visibility changes

## 2026-01-12
### Changed
- Color History Widget now uses event-based color detection
  - Switched from timer polling (200ms intervals) to QEvent.MouseButtonPress detection
  - Event filter installed on QApplication for application-wide monitoring
  - Only checks foreground color when pure mouse button is pressed (no modifier keys)
  - Ignores Ctrl+Click, Shift+Click, and other modified clicks
  - Significantly improved performance by eliminating continuous polling
- Brush History Widget now uses event-based brush detection
  - Switched from timer polling (500ms intervals) to QEvent.MouseButtonPress detection
  - Event filter installed on QApplication for application-wide monitoring
  - Only checks current brush when pure mouse button is pressed (no modifier keys)
  - Ignores Ctrl+Click, Shift+Click, and other modified clicks
  - Significantly improved performance by eliminating continuous polling

## 2026-01-11
### Added
- Pin functionality for popup windows
  - Pin button in toolbar allows keeping popups open
  - When pinned, popups remain visible when selecting brushes/actions
  - When pinned, popups remain visible when pressing shortcut key again
  - Pin status indicated by icon toggle (pin_pinned.png / pin_unpinned.png)
- Close button in popup toolbar
  - Closes popup window and resets pin status
  - Uses circle-xmark.png icon
- Popup window drag-to-move functionality
  - Left-click drag anywhere on popup to reposition
  - Works for both Brush Sets Popup and Actions Popup
- Toolbar in popup windows
  - Pin and close buttons (16×16px) aligned to the right
  - Consistent styling with application theme (#828282 background)
  - Buttons have hover and pressed states

### Changed
- Popup windows now have toolbar at the top with control buttons
- Both Brush Sets Popup and Actions Popup support pin/close/drag functionality

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
