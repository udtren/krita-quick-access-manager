from PyQt5.QtWidgets import QPushButton, QApplication
from PyQt5.QtCore import Qt, QPoint, QMimeData, QSize
from PyQt5.QtGui import QDrag, QIcon, QPixmap
import os
from ..utils.shortcut_utils import get_font_px, get_shortcut_button_config
from ..dialogs.button_config_dialog import ShortcutButtonConfigDialog
from ..gesture.gesture_main import (
    pause_gesture_event_filter,
    resume_gesture_event_filter,
    is_gesture_filter_paused,
)

# from ..utils.data_manager import write_log

DEFAULT_CONFIG = get_shortcut_button_config()
DEFAULT_FONT_COLOR = DEFAULT_CONFIG["font_color"]
DEFAULT_BG_COLOR = DEFAULT_CONFIG["background_color"]


class ShortcutDraggableButton(QPushButton):
    """A draggable button for shortcut actions"""

    def __init__(self, action, grid_info, parent_section, config=None):
        # Determine display name
        display_name = self.get_display_name(action, config)
        super().__init__(display_name)

        # Store references
        self.action = action
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.config = config or {}
        self.drag_start_position = QPoint()
        self.has_icon = False

        # Setup button
        self.setup_button()
        self.setup_connections()

    def get_display_name(self, action, config):
        """Get the display name for the button"""
        if config and config.get("customName"):
            return config.get("customName")
        return action.objectName()

    def setup_button(self):
        """Setup button appearance and properties"""
        # Try to load icon first
        self.load_icon()

        # Apply font settings (only if no icon)
        if not self.has_icon:
            self.apply_font_settings()

        # Apply colors
        self.apply_color_settings()

        if self.has_icon:
            self.setFixedSize(self.iconSize().width() + 5, self.iconSize().height() + 5)

    def load_icon(self):
        """Load and set icon if available"""
        # Check if config has icon_name
        icon_name = self.config.get("icon_name", "")
        if not icon_name or not icon_name.strip():
            return

        # Check if grid has icon_size
        icon_size_str = self.grid_info.get("icon_size", "24")

        # Parse icon size
        try:
            icon_size = int(icon_size_str)
        except ValueError:
            return

        # Build icon path
        current_dir = os.path.dirname(os.path.dirname(__file__))
        icon_path = os.path.join(current_dir, "config", "icon", icon_name)

        # Check if icon file exists
        if not os.path.exists(icon_path):
            return

        # Load and set icon
        try:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap)
                self.setIcon(icon)
                self.setIconSize(QSize(icon_size, icon_size))
                self.setText("")  # Clear text when showing icon
                self.has_icon = True
        except Exception:
            pass

    def apply_font_settings(self):
        """Apply font size settings"""
        font = self.font()

        # Get font size from config or default
        default_config = get_shortcut_button_config()
        font_size_str = self.config.get("fontSize", default_config["font_size"])

        try:
            font_size = int(str(font_size_str).replace("px", ""))
            if font_size < 7:
                font_size = get_font_px(default_config["font_size"])
        except Exception:
            font_size = get_font_px(default_config["font_size"])

        font.setPointSize(font_size)
        self.setFont(font)

    def apply_color_settings(self):
        """Apply color settings"""
        default_config = get_shortcut_button_config()

        font_color = self.config.get("fontColor", default_config["font_color"])
        bg_color = self.config.get(
            "backgroundColor", default_config["background_color"]
        )

        # Check if using custom colors
        is_custom = not self.config.get("useGlobalSettings")

        if is_custom:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {bg_color}; 
                    color: {font_color};
                    border-radius: 6px;
                    border: 1px solid #555;
                    padding: 3px 6px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(bg_color, 15)};
                    border: 1px solid #777;
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(bg_color, 15)};
                    border: 1px solid #333;
                }}
            """
            )
        else:
            from ..utils.styles import shortcut_btn_style

            self.setStyleSheet(shortcut_btn_style())

    def lighten_color(self, color_hex, amount):
        """Lighten a hex color"""
        try:
            from PyQt5.QtGui import QColor

            color = QColor(color_hex)
            h, s, v, a = color.getHsv()
            v = min(255, v + amount)
            color.setHsv(h, s, v, a)
            return color.name()
        except:
            return color_hex

    def darken_color(self, color_hex, amount):
        """Darken a hex color"""
        try:
            from PyQt5.QtGui import QColor

            color = QColor(color_hex)
            h, s, v, a = color.getHsv()
            v = max(0, v - amount)
            color.setHsv(h, s, v, a)
            return color.name()
        except:
            return color_hex

    def setup_connections(self):
        """Setup button connections"""
        self.clicked.connect(
            lambda: self.parent_section.run_krita_action(self.action.objectName())
        )

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        modifiers = QApplication.keyboardModifiers()

        # Shift + Left click: Move up in order
        if event.button() == Qt.LeftButton and modifiers == Qt.ShiftModifier:
            self.move_button_up()
            return

        # Shift + Right click: Move down in order
        elif event.button() == Qt.RightButton and modifiers == Qt.ShiftModifier:
            self.move_button_down()
            return

        # Ctrl + Left click: Start drag operation
        elif event.button() == Qt.LeftButton and modifiers == Qt.ControlModifier:
            self.drag_start_position = event.pos()

        # Ctrl + Right click: Remove button
        elif event.button() == Qt.RightButton and modifiers == Qt.ControlModifier:
            self.remove_button()
            return

        # Alt + Right click: Configure button
        elif event.button() == Qt.RightButton and modifiers == Qt.AltModifier:
            self.configure_button()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if not (event.buttons() & Qt.LeftButton):
            return

        if QApplication.keyboardModifiers() != Qt.ControlModifier:
            return

        if (
            event.pos() - self.drag_start_position
        ).manhattanLength() < QApplication.startDragDistance():
            return

        self.start_drag()

    def start_drag(self):
        """Start drag operation"""
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"shortcut_action:{self.action.objectName()}")
        drag.setMimeData(mime_data)
        drag.setHotSpot(QPoint(16, 16))
        drag.exec_(Qt.MoveAction)

    def move_button_up(self):
        """Move button up in the grid order"""
        actions = self.grid_info["actions"]
        try:
            idx = actions.index(self.action)
            if idx > 0:
                # Move action
                actions.pop(idx)
                actions.insert(idx - 1, self.action)

                # Move config if exists
                self.move_config(idx, idx - 1)

                self.update_grid_and_save()
        except ValueError:
            pass

    def move_button_down(self):
        """Move button down in the grid order"""
        actions = self.grid_info["actions"]
        try:
            idx = actions.index(self.action)
            if idx < len(actions) - 1:
                # Move action
                actions.pop(idx)
                actions.insert(idx + 1, self.action)

                # Move config if exists
                self.move_config(idx, idx + 1)

                self.update_grid_and_save()
        except ValueError:
            pass

    def move_config(self, old_idx, new_idx):
        """Move configuration data along with action"""
        configs = self.grid_info.get("shortcut_configs", [])
        if old_idx < len(configs):
            config = configs.pop(old_idx)
            configs.insert(new_idx, config)

    def remove_button(self):
        """Remove button from grid"""
        actions = self.grid_info["actions"]
        try:
            idx = actions.index(self.action)

            # Remove action
            actions.pop(idx)

            # Remove config if exists
            configs = self.grid_info.get("shortcut_configs", [])
            if idx < len(configs):
                configs.pop(idx)

            self.update_grid_and_save()
        except ValueError:
            pass

    def configure_button(self):
        """Open configuration dialog for button"""
        gesture_filter_state = is_gesture_filter_paused()
        if not gesture_filter_state:
            pause_gesture_event_filter()
        dialog = ShortcutButtonConfigDialog(self)
        if dialog.exec_():
            self.apply_configuration(dialog)
        if not gesture_filter_state:
            resume_gesture_event_filter()

    def apply_configuration(self, dialog):
        """Apply configuration from dialog"""
        # Validate font size
        try:
            font_size = int(dialog.font_size_edit.text().strip())
            if font_size < 7:
                font_size = 12
        except Exception:
            font_size = 12

        # Update configuration
        actions = self.grid_info["actions"]
        try:
            idx = actions.index(self.action)

            # Ensure configs list exists and is long enough
            configs = self.grid_info.setdefault("shortcut_configs", [])
            while len(configs) <= idx:
                configs.append({})

            # Update config
            configs[idx] = {
                "actionName": self.action.objectName(),
                "customName": dialog.name_edit.text(),
                "fontSize": str(font_size),
                "fontColor": (
                    DEFAULT_FONT_COLOR
                    if dialog.use_global_settings_flag.isChecked()
                    else dialog.get_font_color_hex()
                ),
                "backgroundColor": (
                    DEFAULT_BG_COLOR
                    if dialog.use_global_settings_flag.isChecked()
                    else dialog.get_bg_color_hex()
                ),
                "icon_name": dialog.icon_name_edit.text().strip(),
                "useGlobalSettings": dialog.use_global_settings_flag.isChecked(),
            }

            self.update_grid_and_save()
        except ValueError:
            pass

    def update_grid_and_save(self):
        """Update grid display and save data"""
        # Find and update the grid widget
        for grid_widget in self.parent_section.grids:
            if grid_widget.grid_info is self.grid_info:
                grid_widget.update_grid()
                break

        # Save data
        self.parent_section.save_grids_data()
