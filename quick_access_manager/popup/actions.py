from ..compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QShortcut, QFrame, QTabWidget,
    Qt, QSize,
    QCursor, QIcon, QPixmap,
)
from krita import Krita  # type: ignore
from ..utils.action_manager import ActionManager
from ..config.popup_loader import PopupConfigLoader
from ..utils.config_utils import get_config_dir, get_plugin_dir
import json
import os


class ActionsPopup:
    """Handles the popup functionality for action shortcuts"""

    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
        self.popup_window = None
        self.popup_shortcut = None
        self.popup_loader = PopupConfigLoader()
        self.shortcut_grid_data = self.load_shortcut_grid_data()
        self.is_pinned = False
        self.drag_position = None
        self.pin_button = None

    def load_shortcut_grid_data(self):
        """Load shortcut grid data from JSON file"""
        try:
            config_path = os.path.join(get_config_dir(), "shortcut_grid_data.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading shortcut grid data: {e}")
            return {}

    def load_common_config(self):
        """Load max_shortcut_per_row from common config"""
        try:
            config_path = os.path.join(get_config_dir(), "common.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                return config_data.get("layout", {}).get("max_shortcut_per_row", 4)
            return 4
        except Exception:
            return 4

    def _get_tabs_from_data(self):
        """Return tabs list from loaded data (handles both old flat and new tab formats)."""
        if not self.shortcut_grid_data:
            return []
        if "tabs" in self.shortcut_grid_data:
            return self.shortcut_grid_data["tabs"]
        grids = self.shortcut_grid_data.get("grids", [])
        if grids:
            return [{"name": "Tab 1", "grids": grids}]
        return []

    def _get_all_grids_from_data(self):
        """Return flat list of all grid dicts across all tabs."""
        grids = []
        for tab in self._get_tabs_from_data():
            grids.extend(tab.get("grids", []))
        return grids

    def get_custom_name_for_action(self, action):
        """Get custom name for action if available"""
        try:
            action_id = action.objectName() if hasattr(action, "objectName") else str(action)
            for grid in self._get_all_grids_from_data():
                for shortcut_data in grid.get("shortcuts", []):
                    if (
                        shortcut_data.get("actionName") == action_id
                        and "customName" in shortcut_data
                    ):
                        return shortcut_data["customName"]
            return action.text() if hasattr(action, "text") else str(action)
        except Exception:
            return action.text() if hasattr(action, "text") else str(action)

    def get_action_style_info(self, action):
        """Get custom styling information for action if available"""
        try:
            action_id = action.objectName() if hasattr(action, "objectName") else str(action)
            for grid in self._get_all_grids_from_data():
                for shortcut_data in grid.get("shortcuts", []):
                    if shortcut_data.get("actionName") == action_id:
                        return {
                            "customName": shortcut_data.get("customName"),
                            "fontColor": shortcut_data.get("fontColor"),
                            "backgroundColor": shortcut_data.get("backgroundColor"),
                            "fontSize": shortcut_data.get("fontSize"),
                        }
            return {
                "customName": action.text() if hasattr(action, "text") else str(action),
                "fontColor": None,
                "backgroundColor": None,
                "fontSize": None,
            }
        except Exception:
            return {
                "customName": action.text() if hasattr(action, "text") else str(action),
                "fontColor": None,
                "backgroundColor": None,
                "fontSize": None,
            }

    def setup_popup_shortcut(self):
        """Setup shortcut for popup functionality"""
        try:
            main_window = None
            app = Krita.instance()
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()

            parent = main_window if main_window else self.parent_docker

            shortcut_key = self.popup_loader.get_actions_popup_shortcut()
            self.popup_shortcut = QShortcut(shortcut_key, parent)
            self.popup_shortcut.activated.connect(self.show_popup_at_cursor)
            self.popup_shortcut.setContext(Qt.ApplicationShortcut)

        except Exception as e:
            print(f"Error setting up actions popup shortcut: {e}")

    def show_popup_at_cursor(self):
        """Show popup window at cursor position"""
        try:
            if self.popup_window and self.popup_window.isVisible():
                if not self.is_pinned:
                    self.popup_window.hide()
                return

            self.shortcut_grid_data = self.load_shortcut_grid_data()
            self.create_popup_window()

            popup_width = self.popup_window.width()
            popup_height = self.popup_window.height()

            cursor_pos = QCursor.pos()
            self.popup_window.move(
                cursor_pos.x() - popup_width // 2, cursor_pos.y() - popup_height // 3
            )
            self.popup_window.show()
            self.popup_window.raise_()

        except Exception as e:
            print(f"Error showing actions popup: {e}")
            import traceback
            traceback.print_exc()

    def create_popup_window(self):
        """Create the popup window with action shortcuts content"""
        self.popup_window = QFrame()
        self.popup_window.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )

        self.popup_window.mousePressEvent = self.popup_mouse_press
        self.popup_window.mouseMoveEvent = self.popup_mouse_move
        self.popup_window.mouseReleaseEvent = self.popup_mouse_release

        popup_layout = QVBoxLayout()
        popup_layout.setContentsMargins(5, 5, 5, 5)
        popup_layout.setSpacing(2)

        self.create_toolbar(popup_layout)
        self.create_popup_content(popup_layout)
        self.popup_window.setLayout(popup_layout)
        self.popup_window.adjustSize()

    def create_toolbar(self, popup_layout):
        """Create toolbar with pin and close buttons"""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 5)
        toolbar_layout.setSpacing(5)

        close_icon = os.path.join(
            get_plugin_dir(), "config", "system_icon", "circle-xmark.png"
        )

        self.pin_button = QPushButton()
        self.pin_button.setFixedSize(16, 16)
        self.pin_button.setToolTip("Pin window")
        self.pin_button.clicked.connect(self.toggle_pin)
        self.update_pin_icon()
        self.pin_button.setStyleSheet(
            """
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #6a6a6a;
            }
        """
        )

        close_button = QPushButton()
        close_button.setFixedSize(16, 16)
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.close_popup)
        if os.path.exists(close_icon):
            close_button.setIcon(QIcon(close_icon))
            close_button.setIconSize(close_button.size())
        else:
            close_button.setText("X")
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
                color: #fff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #6a6a6a;
            }
        """
        )

        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.pin_button)
        toolbar_layout.addWidget(close_button)
        popup_layout.addLayout(toolbar_layout)

    def update_pin_icon(self):
        """Update pin button icon based on pin status"""
        system_icon_dir = os.path.join(get_plugin_dir(), "config", "system_icon")
        if self.is_pinned:
            pin_icon = os.path.join(system_icon_dir, "pin_pinned.png")
            tooltip = "Unpin window"
        else:
            pin_icon = os.path.join(system_icon_dir, "pin_unpinned.png")
            tooltip = "Pin window"
        if self.pin_button and os.path.exists(pin_icon):
            self.pin_button.setIcon(QIcon(pin_icon))
            self.pin_button.setIconSize(self.pin_button.size())
            self.pin_button.setToolTip(tooltip)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.update_pin_icon()

    def close_popup(self):
        self.is_pinned = False
        if self.popup_window:
            self.popup_window.hide()

    def popup_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPos() - self.popup_window.frameGeometry().topLeft()
            )
            event.accept()

    def popup_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.popup_window.move(event.globalPos() - self.drag_position)
            event.accept()

    def popup_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()

    # ------------------------------------------------------------------
    # Popup content — tab-aware
    # ------------------------------------------------------------------

    def create_popup_content(self, popup_layout):
        """Create action shortcuts content organised by tab."""
        tabs = self._get_tabs_from_data()
        if not tabs or not any(tab.get("grids") for tab in tabs):
            no_grids_label = QLabel("No action grids found in configuration")
            no_grids_label.setStyleSheet("color: #999; font-style: italic;")
            popup_layout.addWidget(no_grids_label)
            return

        tab_widget = QTabWidget()
        for tab_data in tabs:
            tab_page = self._build_tab_page(tab_data)
            tab_widget.addTab(tab_page, tab_data.get("name", "Tab"))
        popup_layout.addWidget(tab_widget)

    def _build_tab_page(self, tab_data):
        """Build the grid content widget for one popup tab."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        if not tab_data.get("grids"):
            empty = QLabel("No grids in this tab")
            empty.setStyleSheet("color: #999; font-style: italic;")
            layout.addWidget(empty)
            page.setLayout(layout)
            return page

        for grid_data in tab_data["grids"]:
            layout.addLayout(self._build_grid_row(grid_data))

        page.setLayout(layout)
        return page

    def _build_grid_row(self, grid_data):
        """Build the name-label + button-grid row for one shortcut grid."""
        grid_name = grid_data.get("name", "Unnamed Grid")
        grid_label = QLabel(grid_name)
        grid_label.setFixedWidth(self.popup_loader.get_grid_label_width())
        grid_label.setWordWrap(True)
        grid_label.setAlignment(Qt.AlignCenter)
        grid_label.setStyleSheet(
            "color: #000000; background-color: #919191; border-radius: 4px;"
            " font-weight: bold; font-size: 12px;"
        )

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        row_layout.addWidget(grid_label)

        if grid_data.get("shortcuts"):
            grid_widget_container = QWidget()
            grid_layout = QGridLayout()
            grid_layout.setSpacing(1)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

            columns = self._get_columns(grid_data)
            for index, shortcut_data in enumerate(grid_data["shortcuts"]):
                btn = self._build_action_button(shortcut_data, grid_data)
                grid_layout.addWidget(btn, index // columns, index % columns)

            grid_layout.setColumnStretch(columns, 1)
            grid_widget_container.setLayout(grid_layout)
            row_layout.addWidget(grid_widget_container)
        else:
            empty_label = QLabel("  (empty)")
            empty_label.setStyleSheet(
                "color: #666; font-style: italic; font-size: 10px; margin-left: 10px;"
            )
            row_layout.addWidget(empty_label)

        row_layout.addStretch()
        return row_layout

    def _get_columns(self, grid_data):
        grid_specific = grid_data.get("max_shortcut_per_row", "")
        if grid_specific and str(grid_specific).strip():
            try:
                return int(grid_specific)
            except ValueError:
                pass
        return self.load_common_config()

    def _build_action_button(self, shortcut_data, grid_data):
        """Build a single action button for the popup."""
        action_btn = QPushButton()

        has_icon = False
        icon_size = 0
        icon_name = shortcut_data.get("icon_name", "")
        icon_size_str = grid_data.get("icon_size", "")

        if icon_name and icon_name.strip() and icon_size_str and icon_size_str.strip():
            try:
                icon_size = int(icon_size_str)
                icon_path = os.path.join(get_config_dir(), "icon", icon_name)
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        action_btn.setIcon(QIcon(pixmap))
                        action_btn.setIconSize(QSize(icon_size, icon_size))
                        action_btn.setFixedSize(QSize(icon_size + 5, icon_size + 5))
                        has_icon = True
            except (ValueError, Exception):
                pass

        if not has_icon:
            action_btn.setMinimumSize(QSize(40, 28))
            action_btn.setMaximumWidth(120)

        action_name = shortcut_data.get("actionName", "")
        action_btn.clicked.connect(
            lambda _, name=action_name: self.execute_action_by_name_and_close(name)
        )

        action_text = shortcut_data.get("customName", action_name)
        if not has_icon:
            action_btn.setText(action_text)
        action_btn.setToolTip(action_text)

        font_color = shortcut_data.get("fontColor", "#fff")
        bg_color = shortcut_data.get("backgroundColor", "#3d3d3d")
        font_size = shortcut_data.get("fontSize", "16")

        action_btn.setStyleSheet(
            f"""
            QPushButton {{
                border: 1px solid #555;
                background-color: {bg_color};
                border-radius: 4px;
                padding: 5px;
                color: {font_color};
                font-size: {font_size}px;
                font-weight: bold;
                text-align: center;
            }}
            QPushButton:hover {{
                border: 2px solid #0078d4;
                background-color: {bg_color};
            }}
            QPushButton:pressed {{
                background-color: #0078d4;
            }}
            """
        )

        return action_btn

    def execute_action_by_name_and_close(self, action_name):
        """Execute action by name and close popup"""
        try:
            if ActionManager.run_action(action_name):
                pass
            else:
                app = Krita.instance()
                if app.activeWindow():
                    window = app.activeWindow()
                    action = window.action(action_name)
                    if action:
                        action.trigger()
                    elif hasattr(self.parent_docker, "run_krita_action"):
                        self.parent_docker.run_krita_action(action_name)
        except Exception as e:
            print(f"Error executing action {action_name}: {e}")
            import traceback
            traceback.print_exc()

        if self.popup_window and not self.is_pinned:
            self.popup_window.hide()
