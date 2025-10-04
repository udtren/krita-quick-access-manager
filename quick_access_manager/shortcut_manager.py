import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDockWidget
from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita  # type: ignore
from .utils.data_manager import load_shortcut_grids_data, save_shortcut_grids_data
from .widgets.shortcut_popup import ShortcutPopup
from .widgets.shortcut_grid_widget import SingleShortcutGridWidget
from .utils.shortcut_utils import get_spacing_between_grids
from .utils.action_manager import ActionManager
from .utils.styles import docker_btn_style
from .popup import ActionsPopup


class ShortcutAccessDockerWidget(QDockWidget):
    """Main docker widget for shortcut access management"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Actions")
        self.grids = []
        self.active_grid_idx = 0

        # Setup paths
        self.setup_paths()

        # Initialize popup functionality
        self.actions_popup = ActionsPopup(self)
        self.actions_popup.setup_popup_shortcut()

        # Initialize UI
        self.init_ui()

    def setup_paths(self):
        """Setup configuration file paths"""
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        self.data_file = os.path.join(self.config_dir, "shortcut_grid_data.json")

    def init_ui(self):
        """Initialize the user interface"""
        # Create a central widget for the dock
        central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(get_spacing_between_grids())
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Create button row
        self.create_button_row()

        central_widget.setLayout(self.main_layout)
        self.setWidget(central_widget)

        # Setup connections
        self.setup_connections()

    def create_button_row(self):
        """Create the top button row"""
        button_layout = QHBoxLayout()

        button_layout.addStretch()

        # Actions button
        self.show_all_btn = QPushButton("Actions")
        self.show_all_btn.setFixedWidth(70)
        self.show_all_btn.setStyleSheet(docker_btn_style())

        # Add Grid button
        self.add_grid_btn = QPushButton("AddGrid")
        self.add_grid_btn.setFixedWidth(70)
        self.add_grid_btn.setStyleSheet(docker_btn_style())

        # Restore Actions button
        self.restore_grid_btn = QPushButton("RestoreActions")
        self.restore_grid_btn.setFixedWidth(100)
        self.restore_grid_btn.setStyleSheet(docker_btn_style())

        button_layout.addWidget(self.show_all_btn)
        button_layout.addWidget(self.add_grid_btn)
        button_layout.addWidget(self.restore_grid_btn)

        self.main_layout.addLayout(button_layout)

    def setup_connections(self):
        """Setup button connections"""
        self.show_all_btn.clicked.connect(self.show_all_shortcut_popup)
        self.add_grid_btn.clicked.connect(self.add_grid)
        self.restore_grid_btn.clicked.connect(self.restore_grids_from_file)

    def show_all_shortcut_popup(self):
        """Show the action selection popup"""
        self.shortcut_popup = ShortcutPopup(self)
        self.shortcut_popup.exec_()

    def add_grid(self):
        """Add a new shortcut grid"""
        grid_name = f"Shortcut Grid {len(self.grids) + 1}"
        self.add_shortcut_grid(grid_name, save=True)

    def add_shortcut_grid(self, grid_name, actions=None, save=True):
        """Add a shortcut grid with the given name and actions"""
        if actions is None:
            actions = []
        elif all(isinstance(a, str) for a in actions):
            # Convert action IDs to action objects
            krita_instance = Krita.instance()
            actions = [
                krita_instance.action(aid)
                for aid in actions
                if krita_instance.action(aid)
            ]

        grid_info = {
            "name": grid_name,
            "actions": actions,
        }

        grid_widget = SingleShortcutGridWidget(grid_info, self)
        self.grids.append(grid_widget)
        self.main_layout.addWidget(grid_widget)
        self.set_active_grid(len(self.grids) - 1)

        if save:
            self.save_grids_data()

        return grid_widget

    def add_shortcut_to_grid(self, action):
        """Add a shortcut to the active grid"""
        if self.grids:
            self.grids[self.active_grid_idx].add_shortcut_button(action)
            self.save_grids_data()

    def set_active_grid(self, idx):
        """Set the active grid by index"""
        for i, grid_widget in enumerate(self.grids):
            grid_widget.set_active(i == idx)
        self.active_grid_idx = idx

    def move_grid(self, grid_widget, direction):
        """Move a grid up or down"""
        try:
            idx = self.grids.index(grid_widget)
            new_idx = idx + direction

            if 0 <= new_idx < len(self.grids):
                # Reorder grids list
                self.grids.pop(idx)
                self.grids.insert(new_idx, grid_widget)

                # Rebuild layout
                self.rebuild_layout()
                self.set_active_grid(new_idx)
                self.save_grids_data()
        except ValueError:
            pass

    def rebuild_layout(self):
        """Rebuild the layout with current grid order"""
        # Remove all grid widgets from layout
        for grid_widget in self.grids:
            self.main_layout.removeWidget(grid_widget)

        # Re-add in new order
        for grid_widget in self.grids:
            self.main_layout.addWidget(grid_widget)

    def run_krita_action(self, action_id):
        """Execute a Krita action"""
        if not ActionManager.run_action(action_id):
            from PyQt5.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Action Error", f"Action '{action_id}' not found."
            )

    def save_grids_data(self):
        """Save grid data to file"""
        grids_data = []
        for grid_widget in self.grids:
            shortcuts = grid_widget.grid_info.get("shortcut_configs", [])
            grid_info = {"name": grid_widget.grid_info["name"], "shortcuts": shortcuts}
            grids_data.append(grid_info)

        try:
            save_shortcut_grids_data(self.data_file, grids_data)
        except Exception as e:
            print(f"Error saving shortcut grids data: {e}")

    def restore_grids_from_file(self):
        """Restore grids from saved file"""
        # Clear existing grids
        self.clear_all_grids()

        # Load data
        krita_instance = Krita.instance()
        all_actions = ActionManager.get_actions_dict()
        grids_data = load_shortcut_grids_data(self.data_file, krita_instance)

        # Create grids
        grid_name_to_widget = {}
        for grid_info in grids_data:
            grid_widget = self.add_shortcut_grid(grid_info["name"], [], save=False)
            grid_name_to_widget[grid_info["name"]] = grid_widget
            # Restore configs
            grid_widget.grid_info["shortcut_configs"] = grid_info.get(
                "shortcut_configs", grid_info.get("shortcuts", [])
            )

        # Add actions to grids
        for grid_info in grids_data:
            grid_widget = grid_name_to_widget.get(grid_info["name"])
            if not grid_widget:
                continue

            shortcut_configs = grid_info.get(
                "shortcut_configs", grid_info.get("shortcuts", [])
            )
            actions = []
            for config in shortcut_configs:
                action_id = config.get("actionName")
                action = all_actions.get(action_id)
                if action:
                    actions.append(action)

            grid_widget.grid_info["actions"] = actions
            grid_widget.update_grid()

        # Set first grid as active
        if self.grids:
            self.set_active_grid(0)

    def clear_all_grids(self):
        """Clear all existing grids"""
        for grid_widget in self.grids:
            self.main_layout.removeWidget(grid_widget)
            grid_widget.deleteLater()

        self.grids = []
        self.active_grid_idx = 0

    def refresh_layout(self):
        """Refresh layout spacing and styles"""
        self.main_layout.setSpacing(get_spacing_between_grids())
        for grid_widget in self.grids:
            grid_widget.refresh_spacing_and_update()


class ShortcutAccessDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        super().__init__("shortcut_access_docker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        return ShortcutAccessDockerWidget()
