from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QShortcut,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QCursor, QKeySequence, QIcon, QPixmap
from krita import Krita  # type: ignore
from ..utils.action_manager import ActionManager
from ..utils.logs import write_log
import json
import os

ActionsPopupShortcut = QKeySequence(Qt.Key_Tab)
GridLabelWidth = 60


class ActionsPopup:
    """Handles the popup functionality for action shortcuts"""

    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
        self.popup_window = None
        self.popup_shortcut = None
        self.shortcut_grid_data = self.load_shortcut_grid_data()

    def load_shortcut_grid_data(self):
        """Load shortcut grid data to check for custom names"""
        try:
            # Get the path to the config file
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(plugin_dir, "config", "shortcut_grid_data.json")

            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"Shortcut grid data file not found: {config_path}")
                return {}
        except Exception as e:
            print(f"Error loading shortcut grid data: {e}")
            return {}

    def load_common_config(self):
        """Load common configuration to get max_shortcut_per_row"""
        try:
            # Get the path to the common config file
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(plugin_dir, "config", "common.json")

            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    # Access the nested layout.max_shortcut_per_row value
                    layout_config = config_data.get("layout", {})
                    return layout_config.get(
                        "max_shortcut_per_row", 4
                    )  # Default to 4 if not found
            else:
                print(f"Common config file not found: {config_path}")
                return 4  # Default value
        except Exception as e:
            print(f"Error loading common config: {e}")
            return 4  # Default value

    def get_custom_name_for_action(self, action):
        """Get custom name for action if available"""
        try:
            # Get action ID
            action_id = None
            if hasattr(action, "objectName"):
                action_id = action.objectName()
            elif hasattr(action, "text"):
                action_id = action.text()
            else:
                action_id = str(action)

            # Search through shortcut grid data for custom name
            if "grids" in self.shortcut_grid_data:
                for grid in self.shortcut_grid_data["grids"]:
                    if "shortcuts" in grid:
                        for shortcut_data in grid["shortcuts"]:
                            # Check if this action matches and has a custom name
                            if (
                                shortcut_data.get("actionName") == action_id
                                and "customName" in shortcut_data
                            ):
                                return shortcut_data["customName"]

            # Return original name if no custom name found
            if hasattr(action, "text"):
                return action.text()
            else:
                return str(action)

        except Exception as e:
            print(f"Error getting custom name for action: {e}")
            # Fallback to original name
            if hasattr(action, "text"):
                return action.text()
            else:
                return str(action)

    def get_action_style_info(self, action):
        """Get custom styling information for action if available"""
        try:
            # Get action ID
            action_id = None
            if hasattr(action, "objectName"):
                action_id = action.objectName()
            elif hasattr(action, "text"):
                action_id = action.text()
            else:
                action_id = str(action)

            # Search through shortcut grid data for styling info
            if "grids" in self.shortcut_grid_data:
                for grid in self.shortcut_grid_data["grids"]:
                    if "shortcuts" in grid:
                        for shortcut_data in grid["shortcuts"]:
                            # Check if this action matches
                            if shortcut_data.get("actionName") == action_id:
                                return {
                                    "customName": shortcut_data.get("customName"),
                                    "fontColor": shortcut_data.get("fontColor"),
                                    "backgroundColor": shortcut_data.get(
                                        "backgroundColor"
                                    ),
                                    "fontSize": shortcut_data.get("fontSize"),
                                }

            # Return default values if no custom styling found
            return {
                "customName": action.text() if hasattr(action, "text") else str(action),
                "fontColor": None,
                "backgroundColor": None,
                "fontSize": None,
            }

        except Exception as e:
            print(f"Error getting action style info: {e}")
            # Fallback to defaults
            return {
                "customName": action.text() if hasattr(action, "text") else str(action),
                "fontColor": None,
                "backgroundColor": None,
                "fontSize": None,
            }

    def setup_popup_shortcut(self):
        """Setup shortcut for popup functionality"""
        try:
            # Try to register shortcut with the main window for global access
            main_window = None
            app = Krita.instance()
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()

            # If we can't get the main window, use parent docker as parent
            parent = main_window if main_window else self.parent_docker

            self.popup_shortcut = QShortcut(ActionsPopupShortcut, parent)
            self.popup_shortcut.activated.connect(self.show_popup_at_cursor)

            # Enable the shortcut for application-wide use
            self.popup_shortcut.setContext(Qt.ApplicationShortcut)

        except Exception as e:
            print(f"Error setting up actions popup shortcut: {e}")

    def show_popup_at_cursor(self):
        """Show popup window at cursor position"""
        print("Actions popup shortcut activated!")  # Debug message
        try:
            if self.popup_window and self.popup_window.isVisible():
                print("Hiding existing actions popup")
                self.popup_window.hide()
                return

            self.shortcut_grid_data = self.load_shortcut_grid_data()
            self.create_popup_window()

            # Get size after adjustSize()
            popup_width = self.popup_window.width()
            popup_height = self.popup_window.height()

            # Position at cursor (centered)
            cursor_pos = QCursor.pos()
            self.popup_window.move(
                cursor_pos.x() - popup_width // 2, cursor_pos.y() - popup_height // 3
            )
            self.popup_window.show()
            self.popup_window.raise_()

            # Auto-hide after 10 seconds (optional)
            # QTimer.singleShot(10000, self.popup_window.hide)

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

        popup_layout = QVBoxLayout()
        popup_layout.setContentsMargins(5, 5, 5, 5)
        popup_layout.setSpacing(2)

        # Add popup content - action shortcuts
        self.create_popup_content(popup_layout)
        self.popup_window.setLayout(popup_layout)
        # Auto-fit content size
        self.popup_window.adjustSize()

    def create_popup_content(self, popup_layout):
        """Create action shortcuts content for popup"""
        # Check if we have grid data from JSON file
        if not self.shortcut_grid_data or "grids" not in self.shortcut_grid_data:
            no_grids_label = QLabel("No action grids found in configuration")
            no_grids_label.setStyleSheet("color: #999; font-style: italic;")
            popup_layout.addWidget(no_grids_label)
            return

        # Create a main widget to hold all grids directly (no scroll area)
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Display all action grids from shortcut_grid_data.json ONLY
        for grid_data in self.shortcut_grid_data["grids"]:
            write_log(f"Processing action grid: {grid_data}")
            grid_name = grid_data.get("name", "Unnamed Grid")
            grid_label = QLabel(grid_name)
            grid_label.setFixedWidth(GridLabelWidth)
            grid_label.setWordWrap(True)
            grid_label.setAlignment(Qt.AlignCenter)
            grid_label.setStyleSheet(
                """
                color: #000000;
                background-color: #919191;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                """
            )

            grid_name_action_layout = QHBoxLayout()
            grid_name_action_layout.setContentsMargins(0, 0, 0, 0)
            grid_name_action_layout.setSpacing(5)
            grid_name_action_layout.addWidget(grid_label)
            if grid_data.get("shortcuts"):
                grid_widget_container = QWidget()
                grid_layout = QGridLayout()
                grid_layout.setSpacing(1)
                grid_layout.setContentsMargins(0, 0, 0, 0)

                # Set alignment to left
                grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

                # Get max_shortcut_per_row - use grid-specific if set, otherwise global config
                grid_specific_columns = grid_data.get("max_shortcut_per_row", "")
                if grid_specific_columns and grid_specific_columns.strip():
                    try:
                        columns = int(grid_specific_columns)
                    except ValueError:
                        columns = self.load_common_config()
                else:
                    columns = self.load_common_config()

                for index, shortcut_data in enumerate(grid_data["shortcuts"]):
                    row = index // columns
                    col = index % columns

                    # Create action button
                    action_btn = QPushButton()

                    # Check for icon
                    has_icon = False
                    icon_name = shortcut_data.get("icon_name", "")
                    icon_size_str = grid_data.get("icon_size", "")

                    if (
                        icon_name
                        and icon_name.strip()
                        and icon_size_str
                        and icon_size_str.strip()
                    ):
                        try:
                            icon_size = int(icon_size_str)
                            # Build icon path
                            plugin_dir = os.path.dirname(
                                os.path.dirname(os.path.abspath(__file__))
                            )
                            icon_path = os.path.join(
                                plugin_dir, "config", "icon", icon_name
                            )

                            if os.path.exists(icon_path):
                                pixmap = QPixmap(icon_path)
                                if not pixmap.isNull():
                                    icon = QIcon(pixmap)
                                    action_btn.setIcon(icon)
                                    action_btn.setIconSize(QSize(icon_size, icon_size))
                                    has_icon = True
                        except (ValueError, Exception):
                            pass

                    # Set button size based on whether it has an icon
                    if not has_icon:
                        action_btn.setMinimumSize(QSize(40, 28))
                        action_btn.setMaximumWidth(120)
                    else:
                        action_btn.setFixedSize(QSize(icon_size + 5, icon_size + 5))

                    # Store action name for execution
                    action_name = shortcut_data.get("actionName", "")
                    action_btn.clicked.connect(
                        lambda checked, name=action_name: self.execute_action_by_name_and_close(
                            name
                        )
                    )

                    # Set action text and styling from JSON data
                    try:
                        # Get custom name and styling from JSON
                        action_text = shortcut_data.get("customName", action_name)

                        # Only set text if no icon
                        if not has_icon:
                            display_text = action_text
                            action_btn.setText(display_text)

                        # Set full name as tooltip
                        action_btn.setToolTip(action_text)

                        # Apply custom styling from JSON
                        font_color = shortcut_data.get("fontColor", "#fff")
                        bg_color = shortcut_data.get("backgroundColor", "#3d3d3d")
                        font_size = shortcut_data.get("fontSize", "16")

                        custom_style = f"""
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
                            filter: brightness(1.2);
                        }}
                        QPushButton:pressed {{
                            background-color: #0078d4;
                        }}
                        """
                        action_btn.setStyleSheet(custom_style)

                    except Exception as e:
                        print(f"Error setting up action button: {e}")
                        action_btn.setText("Action")
                        # Apply default styling on error
                        action_btn.setStyleSheet(
                            """
                            QPushButton {
                                border: 1px solid #555;
                                background-color: #3d3d3d;
                                border-radius: 3px;
                                padding: 2px;
                                color: #fff;
                                font-size: 16px;
                                font-weight: bold;
                                text-align: center;
                            }
                            QPushButton:hover {
                                border: 2px solid #0078d4;
                                background-color: #4d4d4d;
                            }
                            QPushButton:pressed {
                                background-color: #0078d4;
                            }
                        """
                        )

                    grid_layout.addWidget(action_btn, row, col)

                # Add column stretch
                grid_layout.setColumnStretch(columns, 1)

                grid_widget_container.setLayout(grid_layout)
            else:
                # Empty grid message
                empty_label = QLabel(f"  {grid_data.get('name', 'Grid')} (empty)")
                empty_label.setStyleSheet(
                    "color: #666; font-style: italic; font-size: 10px; margin-left: 10px;"
                )
                main_layout.addWidget(empty_label)
            grid_name_action_layout.addWidget(grid_widget_container)
            grid_name_action_layout.addStretch()
            main_layout.addLayout(grid_name_action_layout)

        main_widget.setLayout(main_layout)
        popup_layout.addWidget(main_widget)

    def execute_action_by_name_and_close(self, action_name):
        """Execute action by name and close popup"""
        try:
            print(f"Attempting to execute action: '{action_name}'")  # Debug

            # Use the same ActionManager that works in shortcut_manager.py
            if ActionManager.run_action(action_name):
                print(
                    f"✅ Successfully executed action via ActionManager: {action_name}"
                )
            else:
                print(f"❌ ActionManager could not execute action: '{action_name}'")

                # Fallback: Try the old method
                app = Krita.instance()
                if app.activeWindow():
                    window = app.activeWindow()
                    action = window.action(action_name)
                    if action:
                        action.trigger()
                        print(
                            f"✅ Successfully executed action via window.action: {action_name}"
                        )
                    else:
                        print(
                            f"❌ Action '{action_name}' not found in Krita's action collection"
                        )

                        # Final fallback: try parent docker
                        if hasattr(self.parent_docker, "run_krita_action"):
                            self.parent_docker.run_krita_action(action_name)
                            print(f"✅ Executed via parent docker: {action_name}")
                        else:
                            print(f"❌ All methods failed for action: '{action_name}'")
                else:
                    print("❌ No active window found")

        except Exception as e:
            print(f"❌ Error executing action {action_name}: {e}")
            import traceback

            traceback.print_exc()

        if self.popup_window:
            self.popup_window.hide()
