from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QInputDialog,
    QApplication,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from .shortcut_button import ShortcutDraggableButton
from ..utils.shortcut_utils import (
    get_spacing_between_buttons,
    get_max_shortcut_per_row,
    get_shortcut_button_config,
)
from ..utils.styles import shortcut_btn_style


class SingleShortcutGridWidget(QWidget):
    """Widget representing a single shortcut grid"""

    def __init__(self, grid_info, parent_section):
        super().__init__()
        self.grid_info = grid_info
        self.parent_section = parent_section
        self.is_active = False
        self.shortcut_buttons = []

        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        """Setup the UI elements"""
        self.setAcceptDrops(True)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(get_spacing_between_buttons())
        main_layout.setContentsMargins(1, 1, 1, 1)

        # Header with grid name
        header_layout = QHBoxLayout()
        self.grid_name_label = QLabel(self.grid_info["name"])
        self.grid_name_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; background: none;"
        )
        header_layout.addWidget(self.grid_name_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Grid area for shortcut buttons
        self.shortcut_grid_layout = QGridLayout()
        self.shortcut_grid_layout.setSpacing(get_spacing_between_buttons())
        self.shortcut_grid_layout.setContentsMargins(1, 1, 1, 1)

        grid_area = QWidget()
        grid_area.setLayout(self.shortcut_grid_layout)
        grid_area.setStyleSheet("background: none;")
        main_layout.addWidget(grid_area)

        self.setLayout(main_layout)

    def setup_events(self):
        """Setup event handlers"""

        def grid_name_label_mousePressEvent(event):
            modifiers = QApplication.keyboardModifiers()

            # Shift + Left click: Move grid up
            if event.button() == Qt.LeftButton and modifiers == Qt.ShiftModifier:
                self.parent_section.move_grid(self, -1)

            # Shift + Right click: Move grid down
            elif event.button() == Qt.RightButton and modifiers == Qt.ShiftModifier:
                self.parent_section.move_grid(self, 1)

            # Normal left click: Activate grid
            elif event.button() == Qt.LeftButton:
                self.activate_grid()

            # Alt + Right click: Rename grid
            elif event.button() == Qt.RightButton and modifiers == Qt.AltModifier:
                self.rename_grid()

            # Ctrl+Alt+Shift+Right click: Delete grid
            elif event.button() == Qt.RightButton and (
                modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)
            ) == (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier):
                self.remove_grid()

        self.grid_name_label.mousePressEvent = grid_name_label_mousePressEvent

    def add_shortcut_button(self, action):
        """Add a new shortcut button to this grid"""
        self.grid_info["actions"].append(action)

        # Add default config
        default_config = get_shortcut_button_config()
        if "shortcut_configs" not in self.grid_info:
            self.grid_info["shortcut_configs"] = []

        self.grid_info["shortcut_configs"].append(
            {
                "actionName": action.objectName(),
                "customName": action.objectName(),
                "fontSize": str(default_config["font_size"]).replace("px", ""),
                "fontColor": default_config["font_color"],
                "backgroundColor": default_config["background_color"],
            }
        )

        self.update_grid()

        # Save data
        if hasattr(self.parent_section, "save_grids_data"):
            self.parent_section.save_grids_data()

    def update_grid(self):
        """Update the grid layout and buttons"""
        # Clear existing buttons
        self.clear_grid()

        # Update spacing
        self.shortcut_grid_layout.setSpacing(get_spacing_between_buttons())

        # Get layout parameters
        max_columns = get_max_shortcut_per_row()
        default_config = get_shortcut_button_config()

        # Create buttons
        for idx, action in enumerate(self.grid_info["actions"]):
            # Get or create config
            config = self.get_button_config(idx, action, default_config)

            # Create button
            shortcut_btn = ShortcutDraggableButton(
                action, self.grid_info, self.parent_section, config
            )
            shortcut_btn.setMinimumSize(QSize(40, 28))

            # Apply styling
            self.apply_button_styling(shortcut_btn, config, default_config)

            # Add to grid
            row = idx // max_columns
            col = idx % max_columns
            self.shortcut_grid_layout.addWidget(shortcut_btn, row, col)
            self.shortcut_buttons.append(shortcut_btn)

    def get_button_config(self, idx, action, default_config):
        """Get configuration for a button at the given index"""
        configs = self.grid_info.get("shortcut_configs", [])

        if idx < len(configs):
            return configs[idx]
        else:
            # Create default config
            return {
                "actionName": action.objectName(),
                "customName": action.objectName(),
                "fontSize": str(default_config["font_size"]).replace("px", ""),
                "fontColor": default_config["font_color"],
                "backgroundColor": default_config["background_color"],
            }

    def apply_button_styling(self, button, config, default_config):
        """Apply styling to a button based on its configuration"""
        font_color = config.get("fontColor", default_config["font_color"])
        bg_color = config.get("backgroundColor", default_config["background_color"])
        font_size = config.get("fontSize", default_config["font_size"])

        # Check if using custom styling
        is_custom = (
            font_color != default_config["font_color"]
            or bg_color != default_config["background_color"]
            or f"{str(font_size)}px" != default_config["font_size"]
        )

        if is_custom:
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {bg_color}; 
                    color: {font_color}; 
                    font-size: {font_size}px;
                    border-radius: 6px;
                    border: 1px solid #555;
                    padding: 3px 6px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {button.lighten_color(bg_color, 15)};
                    border: 1px solid #777;
                }}
                QPushButton:pressed {{
                    background-color: {button.darken_color(bg_color, 15)};
                    border: 1px solid #333;
                }}
            """
            )
        else:
            button.setStyleSheet(shortcut_btn_style())

    def clear_grid(self):
        """Clear all buttons from the grid"""
        while self.shortcut_grid_layout.count():
            item = self.shortcut_grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self.shortcut_buttons = []

    def refresh_spacing_and_update(self):
        """Refresh spacing and update the grid"""
        layout = self.layout()
        if layout:
            layout.setSpacing(get_spacing_between_buttons())

        # Update header layout spacing
        if layout and layout.count() > 0:
            header_layout = layout.itemAt(0).layout()
            if header_layout:
                header_layout.setSpacing(1)

        # Update grid layout spacing
        if hasattr(self, "shortcut_grid_layout"):
            self.shortcut_grid_layout.setSpacing(get_spacing_between_buttons())

        self.update_grid()

    def set_active(self, active):
        """Set the active state of this grid"""
        self.is_active = active
        self.update_grid_style()

    def activate_grid(self):
        """Activate this grid"""
        try:
            idx = self.parent_section.grids.index(self)
            self.parent_section.set_active_grid(idx)
        except ValueError:
            pass

    def update_grid_style(self):
        """Update visual style based on active state"""
        if self.is_active:
            self.setStyleSheet("QWidget { border: none; background: none; }")
            self.grid_name_label.setStyleSheet(
                """
                font-weight: bold;
                font-size: 13px;
                color: #4FC3F7;
                background: none;
            """
            )
        else:
            self.setStyleSheet("QWidget { border: none; background: none; }")
            self.grid_name_label.setStyleSheet(
                """
                font-weight: bold;
                font-size: 13px;
                color: #ffffff;
                background: none;
            """
            )

    def rename_grid(self):
        """Rename this grid"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Shortcut Grid",
            "Enter new grid name:",
            text=self.grid_info["name"],
        )

        if ok and new_name.strip():
            self.grid_info["name"] = new_name.strip()
            self.grid_name_label.setText(self.grid_info["name"])
            self.parent_section.save_grids_data()

    def remove_grid(self):
        """Remove this grid"""
        if self in self.parent_section.grids:
            # Remove from layout
            self.parent_section.main_layout.removeWidget(self)
            self.setParent(None)
            self.deleteLater()

            # Remove from grids list
            self.parent_section.grids.remove(self)

            # Update active grid
            if self.parent_section.grids:
                self.parent_section.set_active_grid(0)
            else:
                self.parent_section.active_grid_idx = 0

            self.parent_section.save_grids_data()

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("shortcut_action:"):
                event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop events"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("shortcut_action:"):
                self.handle_action_drop(event, text)

    def handle_action_drop(self, event, text):
        """Handle dropping an action onto this grid"""
        action_id = text.split(":", 1)[1]

        # Find source action and grid
        source_action, source_grid, source_index = self.find_source_action(action_id)

        if source_action and source_grid:
            drop_pos = event.pos()
            target_index = self.calculate_drop_position(drop_pos)

            # Move configuration along with action
            config_to_move = self.extract_config(source_grid, source_index)

            # Handle movement
            if self.grid_info == source_grid:
                self.handle_same_grid_move(source_index, target_index, config_to_move)
            else:
                self.handle_cross_grid_move(
                    source_action,
                    source_grid,
                    source_index,
                    target_index,
                    config_to_move,
                )

            self.parent_section.save_grids_data()
            event.acceptProposedAction()

    def find_source_action(self, action_id):
        """Find the source action in all grids"""
        for grid_widget in self.parent_section.grids:
            for i, action in enumerate(grid_widget.grid_info["actions"]):
                if action.objectName() == action_id:
                    return action, grid_widget.grid_info, i
        return None, None, -1

    def calculate_drop_position(self, drop_pos):
        """Calculate the target position for a drop"""
        max_columns = get_max_shortcut_per_row()
        col = min(drop_pos.x() // 90, max_columns - 1)
        row = drop_pos.y() // 36
        return row * max_columns + col

    def extract_config(self, source_grid, source_index):
        """Extract configuration from source grid"""
        source_configs = source_grid.get("shortcut_configs", [])
        if source_configs and source_index < len(source_configs):
            return source_configs.pop(source_index)
        return None

    def handle_same_grid_move(self, source_index, target_index, config):
        """Handle movement within the same grid"""
        if target_index > source_index:
            target_index -= 1

        # Move action
        action = self.grid_info["actions"].pop(source_index)
        self.grid_info["actions"].insert(target_index, action)

        # Move config
        if config:
            configs = self.grid_info.get("shortcut_configs", [])
            configs.insert(target_index, config)

        self.update_grid()

    def handle_cross_grid_move(
        self, source_action, source_grid, source_index, target_index, config
    ):
        """Handle movement between different grids"""
        # Remove from source
        source_grid["actions"].pop(source_index)

        # Add to target
        target_index = max(0, min(target_index, len(self.grid_info["actions"])))
        self.grid_info["actions"].insert(target_index, source_action)

        # Move config
        if config:
            target_configs = self.grid_info.setdefault("shortcut_configs", [])
            target_configs.insert(target_index, config)

        # Update both grids
        self.update_grid()
        for grid_widget in self.parent_section.grids:
            if grid_widget.grid_info == source_grid:
                grid_widget.update_grid()
                break
