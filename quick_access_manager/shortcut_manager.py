import os
from .compat import (
    Qt, QSize,
    QIcon,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDockWidget, QScrollArea,
    QTabWidget, QMenu, QInputDialog,
)
from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita  # type: ignore
from .utils.data_manager import load_shortcut_tabs_data, save_shortcut_tabs_data
from .widgets.shortcut_popup import ShortcutPopup
from .widgets.shortcut_grid_widget import SingleShortcutGridWidget
from .utils.config_utils import (
    get_config_dir,
    get_plugin_dir,
    get_spacing_between_grids,
)
from .utils.action_manager import ActionManager
from .popup import ActionsPopup


class ShortcutAccessDockerWidget(QDockWidget):
    """Main docker widget for shortcut access management"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Actions")
        self.tabs = []
        self.tab_widget = None
        self.active_grid_idx = 0

        self.setup_paths()

        self.actions_popup = ActionsPopup(self)
        self.actions_popup.setup_popup_shortcut()

        application = Krita.instance()
        appNotifier = application.notifier()
        appNotifier.windowCreated.connect(self.restore_grids_from_file)

        self.init_ui()

    @property
    def grids(self):
        """Flat list of all SingleShortcutGridWidget across all tabs."""
        result = []
        for tab in self.tabs:
            result.extend(tab["grids"])
        return result

    def setup_paths(self):
        self.config_dir = get_config_dir()
        self.data_file = os.path.join(self.config_dir, "shortcut_grid_data.json")

    def _current_tab(self):
        idx = self.tab_widget.currentIndex() if self.tab_widget else 0
        if 0 <= idx < len(self.tabs):
            return self.tabs[idx]
        return None

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_button_row(main_layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(
            self._tab_context_menu
        )
        main_layout.addWidget(self.tab_widget)

        central_widget.setLayout(main_layout)
        self.setWidget(central_widget)

        self.setup_connections()

        if not self.tabs:
            self._add_tab_internal({"name": "Tab 1", "grids": [], "layout": None})
        else:
            for tab_info in self.tabs:
                self._add_tab_ui(tab_info)

    def _create_button_row(self, main_layout):
        button_layout = QHBoxLayout()

        icon_size = QSize(18, 18)
        button_style = """
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

        icon_dir = os.path.join(get_plugin_dir(), "config", "system_icon")

        self.show_all_btn = QPushButton()
        self.show_all_btn.setIcon(QIcon(os.path.join(icon_dir, "actions.png")))
        self.show_all_btn.setIconSize(icon_size)
        self.show_all_btn.setStyleSheet(button_style)
        self.show_all_btn.setFixedSize(22, 22)
        self.show_all_btn.setToolTip("Show All Actions")

        self.add_grid_btn = QPushButton()
        self.add_grid_btn.setIcon(QIcon(os.path.join(icon_dir, "add_grid.png")))
        self.add_grid_btn.setIconSize(icon_size)
        self.add_grid_btn.setStyleSheet(button_style)
        self.add_grid_btn.setFixedSize(22, 22)
        self.add_grid_btn.setToolTip("Add New Grid")

        self.add_tab_btn = QPushButton()
        self.add_tab_btn.setIcon(QIcon(os.path.join(icon_dir, "add_tab.png")))
        self.add_tab_btn.setIconSize(icon_size)
        self.add_tab_btn.setStyleSheet(button_style)
        self.add_tab_btn.setFixedSize(22, 22)
        self.add_tab_btn.setToolTip("Add New Tab")

        button_layout.addWidget(self.show_all_btn)
        button_layout.addWidget(self.add_grid_btn)
        button_layout.addWidget(self.add_tab_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def setup_connections(self):
        self.show_all_btn.clicked.connect(self.show_all_shortcut_popup)
        self.add_grid_btn.clicked.connect(self.add_grid)
        self.add_tab_btn.clicked.connect(self.add_new_tab)

    # ------------------------------------------------------------------
    # Tab operations
    # ------------------------------------------------------------------

    def _add_tab_ui(self, tab_info):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(get_spacing_between_grids())
        layout.setContentsMargins(0, 0, 0, 0)
        page.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        tab_info["layout"] = layout
        self.tab_widget.addTab(scroll, tab_info["name"])

        for grid_widget in tab_info["grids"]:
            layout.addWidget(grid_widget)

    def _add_tab_internal(self, tab_info):
        self.tabs.append(tab_info)
        self._add_tab_ui(tab_info)

    def _tab_context_menu(self, pos):
        idx = self.tab_widget.tabBar().tabAt(pos)
        if idx < 0 or idx >= len(self.tabs):
            return
        tab_info = self.tabs[idx]
        menu = QMenu(self)
        rename_act = menu.addAction("Rename Tab")
        rename_act.triggered.connect(lambda: self.rename_tab(tab_info, idx))
        if len(self.tabs) > 1:
            delete_act = menu.addAction("Delete Tab")
            delete_act.triggered.connect(lambda: self.remove_tab(tab_info))
        menu.exec(self.tab_widget.tabBar().mapToGlobal(pos))

    def add_new_tab(self):
        tab_info = {"name": f"Tab {len(self.tabs) + 1}", "grids": [], "layout": None}
        self._add_tab_internal(tab_info)
        self.tab_widget.setCurrentIndex(len(self.tabs) - 1)
        self.save_grids_data()

    def rename_tab(self, tab_info, idx):
        new_name, ok = QInputDialog.getText(
            self, "Rename Tab", "Enter tab name:", text=tab_info["name"]
        )
        if ok and new_name.strip():
            tab_info["name"] = new_name.strip()
            self.tab_widget.setTabText(idx, tab_info["name"])
            self.save_grids_data()

    def remove_tab(self, tab_info):
        if len(self.tabs) <= 1:
            return
        idx = self.tabs.index(tab_info)
        self.tabs.remove(tab_info)
        self.tab_widget.removeTab(idx)
        all_grids = self.grids
        self.active_grid_idx = min(self.active_grid_idx, max(0, len(all_grids) - 1))
        if all_grids:
            self.set_active_grid(self.active_grid_idx)
        self.save_grids_data()

    # ------------------------------------------------------------------
    # Grid operations
    # ------------------------------------------------------------------

    def _find_tab_for_grid(self, grid_widget):
        for tab_info in self.tabs:
            if grid_widget in tab_info["grids"]:
                return tab_info
        return None

    def _show_grid_context_menu(self, global_pos, grid_widget):
        tab_info = self._find_tab_for_grid(grid_widget)
        if tab_info is None:
            return
        menu = QMenu(self)
        menu.addAction("Rename").triggered.connect(
            lambda: self._rename_grid(grid_widget)
        )
        menu.addAction("Move Up").triggered.connect(
            lambda: self.move_grid(grid_widget, -1)
        )
        menu.addAction("Move Down").triggered.connect(
            lambda: self.move_grid(grid_widget, 1)
        )
        if len(self.tabs) > 1:
            move_menu = menu.addMenu("Move to Tab")
            for target_tab in self.tabs:
                if target_tab is not tab_info:
                    act = move_menu.addAction(target_tab["name"])
                    act.triggered.connect(
                        lambda _, t=target_tab: self.move_grid_to_tab(
                            grid_widget, tab_info, t
                        )
                    )
        menu.addSeparator()
        menu.addAction("Delete").triggered.connect(
            lambda: self._remove_grid(grid_widget, tab_info)
        )
        menu.exec(global_pos)

    def add_grid(self):
        tab_info = self._current_tab()
        if tab_info is None:
            return
        grid_name = f"Shortcut Grid {len(self.grids) + 1}"
        self.add_shortcut_grid(grid_name, tab_info=tab_info, save=True)

    def add_shortcut_grid(
        self,
        grid_name,
        tab_info=None,
        actions=None,
        max_shortcut_per_row="",
        icon_size="24",
        save=True,
    ):
        if tab_info is None:
            tab_info = self._current_tab()
        if tab_info is None:
            return None

        if actions is None:
            actions = []
        elif all(isinstance(a, str) for a in actions):
            krita_instance = Krita.instance()
            actions = [
                krita_instance.action(aid)
                for aid in actions
                if krita_instance.action(aid)
            ]

        grid_info = {
            "name": grid_name,
            "max_shortcut_per_row": max_shortcut_per_row,
            "icon_size": icon_size,
            "actions": actions,
        }

        grid_widget = SingleShortcutGridWidget(grid_info, self)
        tab_info["grids"].append(grid_widget)
        if tab_info["layout"] is not None:
            tab_info["layout"].addWidget(grid_widget)

        flat_idx = self.grids.index(grid_widget)
        self.set_active_grid(flat_idx)

        if save:
            self.save_grids_data()

        return grid_widget

    def _rename_grid(self, grid_widget):
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Grid",
            "Enter new grid name:",
            text=grid_widget.grid_info["name"],
        )
        if ok and new_name.strip():
            grid_widget.grid_info["name"] = new_name.strip()
            grid_widget.grid_name_label.setText(grid_widget.grid_info["name"])
            self.save_grids_data()

    def _remove_grid(self, grid_widget, tab_info):
        if tab_info["layout"] is not None:
            tab_info["layout"].removeWidget(grid_widget)
        grid_widget.setParent(None)
        grid_widget.deleteLater()
        if grid_widget in tab_info["grids"]:
            tab_info["grids"].remove(grid_widget)
        all_grids = self.grids
        if all_grids:
            self.set_active_grid(0)
        else:
            self.active_grid_idx = 0
        self.save_grids_data()

    def add_shortcut_to_grid(self, action):
        all_grids = self.grids
        if all_grids and self.active_grid_idx < len(all_grids):
            all_grids[self.active_grid_idx].add_shortcut_button(action)
            self.save_grids_data()

    def set_active_grid(self, idx):
        all_grids = self.grids
        for i, grid_widget in enumerate(all_grids):
            grid_widget.set_active(i == idx)
        self.active_grid_idx = idx

    def move_grid(self, grid_widget, direction):
        tab_info = self._find_tab_for_grid(grid_widget)
        if tab_info is None:
            return
        grids = tab_info["grids"]
        idx = grids.index(grid_widget)
        new_idx = idx + direction
        if 0 <= new_idx < len(grids):
            grids.pop(idx)
            grids.insert(new_idx, grid_widget)
            self._rebuild_tab_layout(tab_info)
            flat_idx = self.grids.index(grid_widget)
            self.set_active_grid(flat_idx)
            self.save_grids_data()

    def move_grid_to_tab(self, grid_widget, from_tab, to_tab):
        if from_tab["layout"] is not None:
            from_tab["layout"].removeWidget(grid_widget)
        if grid_widget in from_tab["grids"]:
            from_tab["grids"].remove(grid_widget)

        to_tab["grids"].append(grid_widget)
        if to_tab["layout"] is not None:
            to_tab["layout"].addWidget(grid_widget)

        self.tab_widget.setCurrentIndex(self.tabs.index(to_tab))
        self.save_grids_data()

    def _rebuild_tab_layout(self, tab_info):
        layout = tab_info["layout"]
        if layout is None:
            return
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget():
                layout.removeWidget(item.widget())
        for grid_widget in tab_info["grids"]:
            layout.addWidget(grid_widget)

    def rebuild_layout(self):
        """Legacy entry point — rebuilds current tab layout."""
        tab_info = self._current_tab()
        if tab_info:
            self._rebuild_tab_layout(tab_info)

    def run_krita_action(self, action_id):
        if not ActionManager.run_action(action_id):
            from .compat import QMessageBox
            QMessageBox.warning(self, "Action Error", f"Action '{action_id}' not found.")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_grids_data(self):
        tabs_data = []
        for tab_info in self.tabs:
            grids_data = []
            for grid_widget in tab_info["grids"]:
                shortcuts = grid_widget.grid_info.get("shortcut_configs", [])
                grids_data.append({
                    "name": grid_widget.grid_info["name"],
                    "max_shortcut_per_row": grid_widget.grid_info.get(
                        "max_shortcut_per_row", ""
                    ),
                    "icon_size": grid_widget.grid_info.get("icon_size", ""),
                    "shortcuts": shortcuts,
                })
            tabs_data.append({"name": tab_info["name"], "grids": grids_data})

        try:
            save_shortcut_tabs_data(self.data_file, tabs_data)
        except Exception as e:
            # print(f"Error saving shortcut tabs data: {e}")

    def restore_grids_from_file(self):
        self.clear_all_grids()

        all_actions = ActionManager.get_actions_dict()
        tabs_data = load_shortcut_tabs_data(self.data_file)

        for tab_data in tabs_data:
            tab_info = {"name": tab_data["name"], "grids": [], "layout": None}
            self._add_tab_internal(tab_info)

            for grid_data in tab_data["grids"]:
                grid_widget = self.add_shortcut_grid(
                    grid_data["name"],
                    tab_info=tab_info,
                    actions=[],
                    max_shortcut_per_row=grid_data.get("max_shortcut_per_row", ""),
                    icon_size=grid_data.get("icon_size", "24"),
                    save=False,
                )
                shortcut_configs = grid_data.get("shortcuts", [])
                grid_widget.grid_info["shortcut_configs"] = shortcut_configs

                actions = []
                for config in shortcut_configs:
                    action_id = config.get("actionName")
                    action = all_actions.get(action_id)
                    if action:
                        actions.append(action)
                grid_widget.grid_info["actions"] = actions
                grid_widget.update_grid()

        if self.grids:
            self.set_active_grid(0)
        if not self.tabs:
            self._add_tab_internal({"name": "Tab 1", "grids": [], "layout": None})

    def clear_all_grids(self):
        if self.tab_widget:
            while self.tab_widget.count() > 0:
                self.tab_widget.removeTab(0)
        for tab_info in self.tabs:
            for grid_widget in tab_info["grids"]:
                grid_widget.deleteLater()
        self.tabs = []
        self.active_grid_idx = 0

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def show_all_shortcut_popup(self):
        self.shortcut_popup = ShortcutPopup(self)
        if self.shortcut_popup.exec():
            self.reload_ui()

    def reload_ui(self):
        old_widget = self.widget()
        self.tabs = []
        self.tab_widget = None
        self.active_grid_idx = 0
        self.init_ui()
        self.restore_grids_from_file()
        if old_widget:
            old_widget.deleteLater()


class ShortcutAccessDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        try:
            dock_pos = DockWidgetFactory.DockRight
        except AttributeError:
            dock_pos = DockWidgetFactory.DockPosition.DockRight  # Krita 6
        super().__init__("shortcut_access_docker", dock_pos)

    def createDockWidget(self):
        return ShortcutAccessDockerWidget()
