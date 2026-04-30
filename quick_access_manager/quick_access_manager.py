import os
import json
from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita  # type: ignore
from .compat import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QScrollArea,
    QTabWidget,
    QMenu,
    Qt,
    QSize,
    QIcon,
)
from .utils.data_manager import load_tabs_data, save_tabs_data, check_common_config
from .dialogs.settings_dialog import CommonConfigDialog
from .gesture.gesture_config_dialog import GestureConfigDialog
from .utils.config_utils import (
    get_config_dir,
    get_plugin_dir,
    get_spacing_between_grids,
    get_spacing_between_buttons,
    get_brush_icon_size,
)
from .widgets.draggable_button import DraggableBrushButton
from .widgets.grid_container import ClickableGridWidget, DraggableGridContainer
from .popup import BrushSetsPopup, PresetSwitchManager

GRID_NAME_COLOR = "#979797"


class QuickAccessDockerWidget(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Brush Sets")
        self.tabs = []
        self.tab_widget = None
        self.active_grid = None
        self.grid_counter = 0
        config_dir = get_config_dir()
        self.data_file = os.path.join(config_dir, "grids_data.json")
        self.common_config_path = os.path.join(config_dir, "common.json")
        self.preset_dict = Krita.instance().resources("preset")
        self.tabs, self.grid_counter = load_tabs_data(self.data_file, self.preset_dict)

        self.brush_popup = BrushSetsPopup(self)
        self.brush_popup.setup_popup_shortcut()

        self.preset_switch = PresetSwitchManager(self)
        self.preset_switch.setup_shortcut()

        self.init_ui()

    @property
    def grids(self):
        """Flat list of all grids across all tabs — used by widgets/grid_container.py."""
        result = []
        for tab in self.tabs:
            result.extend(tab["grids"])
        return result

    def save_grids_data(self):
        save_tabs_data(self.data_file, self.tabs)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(1)

        icon_size = QSize(18, 18)
        button_style = """
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
                color: white;
            }
            QPushButton:hover { background-color: #9a9a9a; }
            QPushButton:pressed { background-color: #6a6a6a; }
        """
        icon_dir = os.path.join(get_plugin_dir(), "config", "system_icon")

        add_brush_btn = QPushButton()
        add_brush_btn.setIcon(QIcon(os.path.join(icon_dir, "add_brush.png")))
        add_brush_btn.setIconSize(icon_size)
        add_brush_btn.setStyleSheet(button_style)
        add_brush_btn.setFixedSize(22, 22)
        add_brush_btn.setToolTip("Add Current Brush")
        add_brush_btn.clicked.connect(self.add_current_brush)
        button_layout.addWidget(add_brush_btn)

        add_grid_btn = QPushButton()
        add_grid_btn.setIcon(QIcon(os.path.join(icon_dir, "add_grid.png")))
        add_grid_btn.setIconSize(icon_size)
        add_grid_btn.setStyleSheet(button_style)
        add_grid_btn.setFixedSize(22, 22)
        add_grid_btn.setToolTip("Add New Grid")
        add_grid_btn.clicked.connect(self.add_new_grid)
        button_layout.addWidget(add_grid_btn)

        add_tab_btn = QPushButton()
        add_tab_btn.setIcon(QIcon(os.path.join(icon_dir, "add_tab.png")))
        add_tab_btn.setIconSize(icon_size)
        add_tab_btn.setStyleSheet(button_style)
        add_tab_btn.setFixedSize(22, 22)
        add_tab_btn.setToolTip("Add New Tab")
        add_tab_btn.clicked.connect(self.add_new_tab)
        button_layout.addWidget(add_tab_btn)

        gesture_btn = QPushButton()
        gesture_btn.setIcon(QIcon(os.path.join(icon_dir, "gesture.png")))
        gesture_btn.setIconSize(icon_size)
        gesture_btn.setStyleSheet(button_style)
        gesture_btn.setFixedSize(22, 22)
        gesture_btn.setToolTip("Gesture Configuration")
        gesture_btn.clicked.connect(self.open_gesture_config)
        button_layout.addWidget(gesture_btn)

        setting_btn = QPushButton()
        setting_btn.setIcon(QIcon(os.path.join(icon_dir, "setting.png")))
        setting_btn.setIconSize(icon_size)
        setting_btn.setStyleSheet(button_style)
        setting_btn.setFixedSize(22, 22)
        setting_btn.setToolTip("Settings")
        setting_btn.clicked.connect(self.show_settings_dialog)
        button_layout.addWidget(setting_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(
            self._tab_context_menu
        )
        main_layout.addWidget(self.tab_widget)

        central_widget.setLayout(main_layout)
        self.setWidget(central_widget)

        if not self.tabs or not any(True for _ in self.tabs):
            self.add_new_tab()
        else:
            for tab_info in self.tabs:
                self._add_tab_ui(tab_info)
            all_grids = self.grids
            if all_grids:
                self.set_active_grid(all_grids[0])

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

        tab_info["layout"] = layout
        self.tab_widget.addTab(scroll, tab_info["name"])

        for grid_info in tab_info["grids"]:
            self._add_grid_ui(grid_info, tab_info)

    def _add_grid_ui(self, grid_info, tab_info):
        grid_container = DraggableGridContainer(grid_info, self)
        container_layout = QVBoxLayout()
        container_layout.setAlignment(Qt.AlignTop)
        container_layout.setSpacing(1)
        container_layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(1)
        header_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(grid_info["name"])
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(name_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)
        grid_info["container"] = grid_container
        grid_info["name_label"] = name_label

        def name_label_mousePressEvent(event, _g=grid_info, _t=tab_info):
            if event.button() == Qt.LeftButton:
                self.set_active_grid(_g)
            elif event.button() == Qt.RightButton:
                self._show_grid_context_menu(event.globalPos(), _g, _t)

        name_label.mousePressEvent = name_label_mousePressEvent

        grid_widget = ClickableGridWidget(grid_info, self)
        grid_widget.setFixedHeight(get_brush_icon_size() + 4)
        grid_widget.setMinimumHeight(get_brush_icon_size() + 4)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        grid_layout.setSpacing(get_spacing_between_buttons())
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_widget.setLayout(grid_layout)
        container_layout.addWidget(grid_widget)

        grid_container.setLayout(container_layout)
        grid_info["widget"] = grid_widget
        grid_info["layout"] = grid_layout
        tab_info["layout"].addWidget(grid_container)
        self.update_grid(grid_info)

    # ------------------------------------------------------------------
    # Tab operations
    # ------------------------------------------------------------------

    def _current_tab(self):
        idx = self.tab_widget.currentIndex()
        if 0 <= idx < len(self.tabs):
            return self.tabs[idx]
        return None

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
        self.tabs.append(tab_info)
        self._add_tab_ui(tab_info)
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
        if self.active_grid in tab_info["grids"]:
            self.active_grid = None
        self.tabs.remove(tab_info)
        self.tab_widget.removeTab(idx)
        if self.active_grid is None:
            for tab in self.tabs:
                if tab["grids"]:
                    self.set_active_grid(tab["grids"][0])
                    break
        self.save_grids_data()

    # ------------------------------------------------------------------
    # Grid operations
    # ------------------------------------------------------------------

    def _show_grid_context_menu(self, global_pos, grid_info, tab_info):
        menu = QMenu(self)
        menu.addAction("Rename").triggered.connect(lambda: self.rename_grid(grid_info))
        menu.addAction("Move Up").triggered.connect(
            lambda: self.move_grid(grid_info, tab_info, -1)
        )
        menu.addAction("Move Down").triggered.connect(
            lambda: self.move_grid(grid_info, tab_info, 1)
        )
        if len(self.tabs) > 1:
            move_menu = menu.addMenu("Move to Tab")
            for target_tab in self.tabs:
                if target_tab is not tab_info:
                    act = move_menu.addAction(target_tab["name"])
                    act.triggered.connect(
                        lambda _, t=target_tab: self.move_grid_to_tab(
                            grid_info, tab_info, t
                        )
                    )
        menu.addSeparator()
        menu.addAction("Delete").triggered.connect(
            lambda: self.remove_grid(grid_info, tab_info)
        )
        menu.exec(global_pos)

    def add_new_grid(self):
        tab_info = self._current_tab()
        if tab_info is None:
            return
        self.grid_counter += 1
        grid_info = {
            "container": None,
            "widget": None,
            "layout": None,
            "name_label": None,
            "name": f"Grid {self.grid_counter}",
            "brush_presets": [],
            "is_active": False,
        }
        tab_info["grids"].append(grid_info)
        self._add_grid_ui(grid_info, tab_info)
        if self.active_grid is None:
            self.set_active_grid(grid_info)
        self.save_grids_data()

    def rename_grid(self, grid_info):
        new_name, ok = QInputDialog.getText(
            self, "Rename Grid", "Enter new grid name:", text=grid_info["name"]
        )
        if ok and new_name.strip():
            grid_info["name"] = new_name.strip()
            grid_info["name_label"].setText(grid_info["name"])
            self.save_grids_data()

    def remove_grid(self, grid_info, tab_info):
        container = grid_info.get("container")
        if container:
            tab_info["layout"].removeWidget(container)
            container.setParent(None)
            container.deleteLater()
        tab_info["grids"].remove(grid_info)
        if self.active_grid is grid_info:
            self.active_grid = None
            all_grids = self.grids
            if all_grids:
                self.set_active_grid(all_grids[0])
        self.save_grids_data()

    def move_grid(self, grid_info, tab_info, direction):
        grids = tab_info["grids"]
        idx = grids.index(grid_info)
        new_idx = idx + direction
        if 0 <= new_idx < len(grids):
            grids.pop(idx)
            grids.insert(new_idx, grid_info)
            self._rebuild_tab_layout(tab_info)
            self.save_grids_data()

    def move_grid_to_tab(self, grid_info, from_tab, to_tab):
        container = grid_info.get("container")
        if container:
            from_tab["layout"].removeWidget(container)
            container.setParent(None)
            container.deleteLater()
        from_tab["grids"].remove(grid_info)

        grid_info["container"] = None
        grid_info["widget"] = None
        grid_info["layout"] = None
        grid_info["name_label"] = None

        to_tab["grids"].append(grid_info)
        self._add_grid_ui(grid_info, to_tab)
        self.tab_widget.setCurrentIndex(self.tabs.index(to_tab))
        self.save_grids_data()

    def _rebuild_tab_layout(self, tab_info):
        layout = tab_info["layout"]
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget():
                layout.removeWidget(item.widget())
        for grid_info in tab_info["grids"]:
            layout.addWidget(grid_info["container"])
        for grid_info in tab_info["grids"]:
            self.update_grid_style(grid_info)

    # ------------------------------------------------------------------
    # Grid display
    # ------------------------------------------------------------------

    def get_dynamic_columns(self):
        max_brush = check_common_config().get("layout", {}).get("max_brush_per_row", 8)
        return int(max_brush)

    def add_current_brush(self):
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            current_preset = app.activeWindow().activeView().currentBrushPreset()
            if current_preset and self.active_grid:
                all_preset_names = []
                for tab in self.tabs:
                    for grid in tab["grids"]:
                        all_preset_names.extend(p.name() for p in grid["brush_presets"])
                if current_preset.name() not in all_preset_names:
                    self.active_grid["brush_presets"].append(current_preset)
                    self.update_grid(self.active_grid)
                    self.save_grids_data()

    def update_grid(self, grid_info):
        layout = grid_info["layout"]
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        columns = self.get_dynamic_columns()
        preset_count = len(grid_info["brush_presets"])
        required_rows = (
            (preset_count + columns - 1) // columns if preset_count > 0 else 1
        )
        new_height = required_rows * get_brush_icon_size() + (required_rows - 1) * 2 + 4
        grid_info["widget"].setFixedHeight(new_height)
        for index, preset in enumerate(grid_info["brush_presets"]):
            row = index // columns
            col = index % columns
            brush_button = DraggableBrushButton(preset, grid_info, self)
            layout.addWidget(brush_button, row, col)

    def set_active_grid(self, grid_info):
        for tab in self.tabs:
            for grid in tab["grids"]:
                grid["is_active"] = False
                self.update_grid_style(grid)
        grid_info["is_active"] = True
        self.active_grid = grid_info
        self.update_grid_style(grid_info)

    def update_grid_style(self, grid_info):
        if grid_info["widget"] is None or grid_info["name_label"] is None:
            return
        if grid_info["is_active"]:
            grid_info["widget"].setStyleSheet(
                "QWidget { border: 2px solid #0078d4; background-color: #f0f8ff; }"
            )
            grid_info["name_label"].setStyleSheet(
                "font-weight: bold; font-size: 12px; color: #4FC3F7;"
            )
        else:
            grid_info["widget"].setStyleSheet(
                "QWidget { border: 1px solid #cccccc; background-color: #ffffff; }"
            )
            grid_info["name_label"].setStyleSheet(
                f"font-weight: bold; font-size: 12px; color: {GRID_NAME_COLOR};"
            )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def select_brush_preset(self, preset):
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            app.activeWindow().activeView().setCurrentBrushPreset(preset)

    def open_gesture_config(self):
        dialog = GestureConfigDialog()
        dialog.show()
        dialog.setAttribute(Qt.WA_DeleteOnClose, False)

    def reload_ui(self):
        old_widget = self.widget()
        self.tabs, self.grid_counter = load_tabs_data(self.data_file, self.preset_dict)
        self.active_grid = None
        self.tab_widget = None
        self.init_ui()
        if old_widget:
            old_widget.deleteLater()
        window = Krita.instance().activeWindow()
        if window:
            for docker in window.dockers():
                if docker.objectName() in (
                    "shortcut_access_docker",
                    "brush_adjust_docker",
                ):
                    if hasattr(docker, "reload_ui"):
                        docker.reload_ui()

    def show_settings_dialog(self):
        dlg = CommonConfigDialog(self.common_config_path, self)
        if dlg.exec():
            global COMMON_CONFIG
            with open(self.common_config_path, "r", encoding="utf-8") as f:
                COMMON_CONFIG = json.load(f)
            self.reload_ui()

    def rebuild_grid_layout(self):
        """Legacy entry point called by drag-drop widgets — rebuilds the current tab."""
        tab_info = self._current_tab()
        if tab_info:
            self._rebuild_tab_layout(tab_info)
            self.save_grids_data()


class QuickAccessDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        try:
            dock_pos = DockWidgetFactory.DockRight
        except AttributeError:
            dock_pos = DockWidgetFactory.DockPosition.DockRight  # Krita 6
        super().__init__("quick_access_manager_docker", dock_pos)

    def createDockWidget(self):
        return QuickAccessDockerWidget()
