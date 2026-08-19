"""Minimal Quick Access Palette Docker for the remastered plugin."""

import os

from krita import (  # type: ignore
    DockWidgetFactory,
    DockWidgetFactoryBase,
    Krita,
    ManagedColor,
)

from ...compat import (
    QColor,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QIcon,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPixmap,
    QPushButton,
    QScrollArea,
    QSize,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from ...gesture import GestureConfigDialog, set_gesture_enabled
from ...infrastructure import (
    ActionManager,
    AliasRepository,
    DockerManager,
    get_default_icons_dir,
    get_system_icons_dir,
)
from ...shared import (
    ACTION_ITEM,
    BRUSH_ITEM,
    COLOR_ITEM,
    DOCKER_TOGGLE_ITEM,
    LABEL_ITEM,
    SCRIPT_ITEM,
    SEPARATOR_ITEM,
)
from .alias_config_dialog import AliasConfigDialog
from .controller import PaletteController
from .dialogs import (
    ActionItemConfigDialog,
    ActionSelectorDialog,
    ColorItemConfigDialog,
    DockerToggleItemConfigDialog,
    GridEditDialog,
    LabelItemConfigDialog,
    PaletteConfigDialog,
    ScriptItemConfigDialog,
)


class QuickAccessPaletteDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        try:
            dock_pos = DockWidgetFactory.DockRight
        except AttributeError:
            dock_pos = DockWidgetFactory.DockPosition.DockRight
        super().__init__("quick_access_palette_docker", dock_pos)

    def createDockWidget(self):
        return QuickAccessPaletteDockerWidget()


class QuickAccessPaletteDockerWidget(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Access Palette")
        self.setObjectName("quick_access_palette_docker")
        self.controller = PaletteController()
        self.actions = ActionManager.get_actions_dict()
        self.issue_map = {}
        self.root_widget = QWidget()
        self.setWidget(self.root_widget)
        self.setMinimumWidth(160)
        self.setMinimumHeight(120)
        self.build_ui()

    def build_ui(self):
        self.root_layout = QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.root_layout.setSpacing(4)
        self.build_header()
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self.show_tab_menu)
        self.root_layout.addWidget(self.tab_widget)
        self.reload_tabs()

    def build_header(self):
        header = QHBoxLayout()
        self.add_brush_btn = self.create_header_button("add_brush.png", "Add Brush")
        self.add_action_btn = self.create_header_button("actions.png", "Add Action")
        self.add_tab_btn = self.create_header_button("add_tab.png", "Add Tab")
        self.add_label_btn = self.create_header_button("label.png", "Add Label")
        self.add_separator_btn = self.create_header_button(
            "separator.png", "Add Separator"
        )
        self.add_docker_toggle_btn = self.create_header_button(
            "add_docker.png", "Add Docker Toggle"
        )
        self.add_color_btn = self.create_header_button(
            "add_color.png", "Add Color Swatch"
        )
        self.add_script_btn = self.create_header_button("add_script.png", "Add Script")
        self.grid_edit_btn = self.create_header_button("manage_grid.png", "Edit Grid")
        self.gesture_btn = self.create_header_button("gesture.png", "Gesture Settings")
        self.alias_config_btn = self.create_header_button(
            "alias_config.png", "Alias Config"
        )
        self.config_btn = self.create_header_button("setting.png", "Config")

        self.add_tab_btn.clicked.connect(self.add_tab)
        self.add_brush_btn.clicked.connect(self.add_current_brush)
        self.add_action_btn.clicked.connect(self.add_action)
        self.add_label_btn.clicked.connect(self.add_label)
        self.add_separator_btn.clicked.connect(self.add_separator)
        self.add_docker_toggle_btn.clicked.connect(self.add_docker_toggle)
        self.add_color_btn.clicked.connect(self.add_color)
        self.add_script_btn.clicked.connect(self.add_script)
        self.grid_edit_btn.clicked.connect(self.show_grid_edit_dialog)
        self.gesture_btn.clicked.connect(self.show_gesture_config_dialog)
        self.alias_config_btn.clicked.connect(self.show_alias_config_dialog)
        self.config_btn.clicked.connect(self.show_config_dialog)

        for button in (
            self.add_tab_btn,
            self.add_brush_btn,
            self.add_action_btn,
            self.add_label_btn,
            self.add_separator_btn,
            self.add_docker_toggle_btn,
            self.add_color_btn,
            self.add_script_btn,
            self.grid_edit_btn,
            self.gesture_btn,
            self.alias_config_btn,
            self.config_btn,
        ):
            if not button.icon().isNull():
                button.setFixedSize(24, 24)
                button.setIconSize(QSize(18, 18))
            else:
                button.setFixedHeight(24)
            header.addWidget(button)
        header.addStretch(1)
        self.root_layout.addLayout(header)

    def create_header_button(self, icon_name, tooltip, fallback_text=""):
        button = QPushButton()
        icon_path = os.path.join(get_system_icons_dir(), icon_name) if icon_name else ""
        if icon_path and os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        elif fallback_text:
            button.setText(fallback_text)
        button.setToolTip(tooltip)
        button.setStyleSheet(
            "QPushButton { background-color: #828282; border: none; border-radius: 2px; }"
            "QPushButton:hover { background-color: #9a9a9a; }"
            "QPushButton:pressed { background-color: #6a6a6a; }"
        )
        return button

    def item_cell_size(self):
        return self.controller.docker_icon_size()

    def item_icon_size(self):
        size = max(16, self.item_cell_size() - 4)
        return QSize(size, size)

    def reload_tabs(self):
        self.issue_map = self.controller.validate_active_grid().issues_by_item()
        self.tab_widget.blockSignals(True)
        while self.tab_widget.count():
            self.tab_widget.removeTab(0)

        for tab in self.controller.document.tabs:
            page = self.create_tab_page(tab)
            self.tab_widget.addTab(page, tab.name)
            if tab.id == self.controller.active_tab_id:
                self.tab_widget.setCurrentWidget(page)

        self.tab_widget.blockSignals(False)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def show_tab_menu(self, pos):
        index = self.tab_widget.tabBar().tabAt(pos)
        if index < 0 or index >= len(self.controller.document.tabs):
            return
        tab = self.controller.document.tabs[index]
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        remove_action = menu.addAction("Remove")
        remove_action.setEnabled(len(self.controller.document.tabs) > 1)
        selected = menu.exec(self.tab_widget.tabBar().mapToGlobal(pos))
        if selected == rename_action:
            self.rename_tab(tab, index)
        elif selected == remove_action:
            self.controller.remove_tab(tab.id)
            self.reload_tabs()

    def rename_tab(self, tab, index):
        name, ok = QInputDialog.getText(self, "Rename Tab", "Tab name:", text=tab.name)
        if ok and name.strip():
            self.controller.rename_tab(tab.id, name.strip())
            self.tab_widget.setTabText(index, name.strip())

    def create_tab_page(self, tab):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for grid in tab.grids:
            layout.addWidget(self.create_grid_widget(grid))
        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    def create_grid_widget(self, grid):
        widget = QWidget()
        cell_size = self.item_cell_size()
        spacing = 2
        max_bottom = max([item.bottom for item in grid.items], default=1)
        width = max(1, grid.columns) * cell_size + max(0, grid.columns - 1) * spacing
        height = max_bottom * cell_size + max(0, max_bottom - 1) * spacing
        widget.setMinimumSize(width, height)

        for item in sorted(
            grid.items, key=lambda entry: (entry.row, entry.col, entry.id)
        ):
            child = self.create_item_widget(item)
            self.attach_item_context_menu(child, item)
            child.setParent(widget)
            x = item.col * (cell_size + spacing)
            y = item.row * (cell_size + spacing)
            child_width = (
                item.col_span * cell_size + max(0, item.col_span - 1) * spacing
            )
            child_height = (
                item.row_span * cell_size + max(0, item.row_span - 1) * spacing
            )
            child.setGeometry(x, y, child_width, child_height)
            child.show()
        return widget

    def create_item_widget(self, item):
        if item.type == BRUSH_ITEM:
            button = QPushButton()
            button.setFixedSize(self.item_cell_size(), self.item_cell_size())
            brush_name = item.payload.get("brush_name", "")
            button.setToolTip(brush_name)
            self.apply_brush_icon(button, brush_name)
            button.clicked.connect(
                lambda checked=False, name=brush_name: self.activate_brush(name)
            )
            self.apply_issue_style(button, item)
            return button

        if item.type == ACTION_ITEM:
            action_id = item.payload.get("action_id", "")
            alias = self.alias_entry("actions", action_id)
            button = QPushButton(alias.get("custom_name") or action_id)
            button.setMinimumHeight(36)
            button.clicked.connect(
                lambda checked=False, action_id=action_id: self.trigger_action(
                    action_id
                )
            )
            icon_name = alias.get("icon_name")
            has_icon = False
            if icon_name:
                icon_path = self.resolve_icon_path(icon_name)
                if icon_path:
                    button.setIcon(QIcon(icon_path))
                    button.setIconSize(self.item_icon_size())
                    button.setText("")
                    button.setFixedSize(self.item_cell_size(), self.item_cell_size())
                    has_icon = True
            self.apply_action_style(button, alias, has_icon=has_icon)
            self.apply_issue_style(button, item)
            return button

        if item.type == LABEL_ITEM:
            label = QLabel(item.payload.get("text", "Label"))
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.apply_label_style(label, item)
            self.apply_issue_style(label, item)
            return label

        if item.type == SEPARATOR_ITEM:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setMinimumHeight(12)
            self.apply_issue_style(separator, item)
            return separator

        if item.type == DOCKER_TOGGLE_ITEM:
            docker_id = item.payload.get("docker_id", "")
            alias = self.alias_entry("dockers", docker_id)
            icon_path = self.resolve_icon_path(alias.get("icon_name"))
            has_icon = bool(icon_path)
            if has_icon:
                button = QPushButton()
                button.setFixedSize(self.item_cell_size(), self.item_cell_size())
                button.setIcon(QIcon(icon_path))
                button.setIconSize(self.item_icon_size())
            else:
                button = QPushButton(alias.get("custom_name") or docker_id)
                button.setMinimumHeight(36)
            button.setToolTip(alias.get("custom_name") or docker_id)
            button.clicked.connect(
                lambda checked=False, docker_id=docker_id: self.activate_docker_toggle(
                    docker_id
                )
            )
            self.apply_action_style(
                button,
                alias,
                has_icon=has_icon,
                default_bg="#263a2f",
                default_fg="#ffffff",
            )
            self.apply_issue_style(button, item)
            return button

        if item.type == COLOR_ITEM:
            button = QPushButton()
            button.setFixedSize(self.item_cell_size(), self.item_cell_size())
            color = item.payload.get("color", "#ffffff")
            button.setToolTip(color)
            button.setStyleSheet(
                f"QPushButton {{ background: {color}; border: 1px solid #555; border-radius: 4px; }}"
            )
            button.clicked.connect(
                lambda checked=False, color=color: self.activate_color(color)
            )
            self.apply_issue_style(button, item)
            return button

        if item.type == SCRIPT_ITEM:
            button = QPushButton()
            button.setFixedSize(self.item_cell_size(), self.item_cell_size())
            script_path = item.payload.get("script_path", "")
            button.setToolTip(item.payload.get("customName") or script_path)
            icon_path = self.resolve_icon_path(item.payload.get("icon_name"))
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(self.item_icon_size())
            else:
                button.setText((item.payload.get("customName") or "Sc")[:2])
            button.clicked.connect(
                lambda checked=False, script_path=script_path: self.run_script(
                    script_path
                )
            )
            self.apply_issue_style(button, item)
            return button

        fallback = QLabel(item.type)
        self.apply_issue_style(fallback, item)
        return fallback

    def attach_item_context_menu(self, widget, item):
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, target=widget, palette_item=item: self.show_item_menu(
                target, palette_item, pos
            )
        )

    def show_item_menu(self, widget, item, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        property_action = None
        if item.type in (
            ACTION_ITEM,
            LABEL_ITEM,
            DOCKER_TOGGLE_ITEM,
            COLOR_ITEM,
            SCRIPT_ITEM,
        ):
            property_action = menu.addAction("Property")
        selected = menu.exec(widget.mapToGlobal(pos))
        if selected == remove_action:
            self.controller.remove_item(item.id)
            self.reload_tabs()
        elif property_action is not None and selected == property_action:
            if item.type == ACTION_ITEM:
                self.show_action_property(item)
            elif item.type == LABEL_ITEM:
                self.show_label_property(item)
            elif item.type == DOCKER_TOGGLE_ITEM:
                self.show_docker_toggle_property(item)
            elif item.type == COLOR_ITEM:
                self.show_color_property(item)
            elif item.type == SCRIPT_ITEM:
                self.show_script_property(item)

    def show_label_property(self, item):
        dialog = LabelItemConfigDialog(dict(item.payload), parent=self)
        if dialog.exec():
            self.controller.update_label_item(item.id, dialog.get_config())
            self.reload_tabs()

    def show_docker_toggle_property(self, item):
        docker_id = item.payload.get("docker_id", "")
        dialog = DockerToggleItemConfigDialog(
            self.docker_alias_dialog_config(docker_id), parent=self
        )
        if dialog.exec():
            config = dialog.get_config()
            new_docker_id = config.pop("docker_id", docker_id)
            self.save_docker_alias(new_docker_id, config)
            self.controller.update_docker_toggle_item(item.id, new_docker_id)
            self.reload_tabs()

    def show_color_property(self, item):
        dialog = ColorItemConfigDialog(dict(item.payload), parent=self)
        if dialog.exec():
            self.controller.update_color_item(item.id, dialog.get_config())
            self.reload_tabs()

    def show_script_property(self, item):
        dialog = ScriptItemConfigDialog(dict(item.payload), parent=self)
        if dialog.exec():
            self.controller.update_script_item(item.id, dialog.get_config())
            self.reload_tabs()

    def show_action_property(self, item):
        action_id = item.payload.get("action_id", "")
        self.actions = ActionManager.get_actions_dict()
        dialog = ActionItemConfigDialog(
            self.actions,
            parent=self,
            selected_action_id=action_id,
            config=self.action_alias_dialog_config(action_id),
        )
        if dialog.exec():
            config = dialog.get_config()
            config.pop("action_id", None)
            self.save_action_alias(action_id, config)
            self.controller.update_action_item(item.id)
            self.reload_tabs()

    def resolve_icon_path(self, icon_name):
        if not icon_name:
            return None
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
        icon_path = os.path.join(get_default_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            return icon_path
        return None

    # ------------------------------------------------------------------
    # Shared Alias Config lookups (single reference for Action/Docker
    # custom name, colors, font size, and icon).
    # ------------------------------------------------------------------
    def alias_entry(self, category, item_id):
        return AliasRepository().load().get(category, {}).get(item_id, {})

    def save_alias_entry(self, category, item_id, updates):
        if not item_id:
            return
        repository = AliasRepository()
        data = repository.load()
        entry = dict(data.get(category, {}).get(item_id, {}))
        entry.update(updates)
        data.setdefault(category, {})[item_id] = entry
        repository.save(data)

    def action_alias_dialog_config(self, action_id):
        alias = self.alias_entry("actions", action_id)
        return {
            "customName": alias.get("custom_name") or action_id,
            "fontSize": alias.get("font_size") or "18",
            "backgroundColor": alias.get("background_color") or "#3a263f",
            "fontColor": alias.get("font_color") or "#ffffff",
            "icon_name": alias.get("icon_name", ""),
        }

    def save_action_alias(self, action_id, dialog_config):
        self.save_alias_entry(
            "actions",
            action_id,
            {
                "custom_name": dialog_config.get("customName", ""),
                "font_size": dialog_config.get("fontSize", ""),
                "background_color": dialog_config.get("backgroundColor", ""),
                "font_color": dialog_config.get("fontColor", ""),
                "icon_name": dialog_config.get("icon_name", ""),
            },
        )

    def docker_alias_dialog_config(self, docker_id):
        alias = self.alias_entry("dockers", docker_id)
        return {
            "docker_id": docker_id,
            "customName": alias.get("custom_name") or docker_id,
            "icon_name": alias.get("icon_name", ""),
        }

    def save_docker_alias(self, docker_id, dialog_config):
        self.save_alias_entry(
            "dockers",
            docker_id,
            {
                "custom_name": dialog_config.get("customName", ""),
                "icon_name": dialog_config.get("icon_name", ""),
            },
        )

    def apply_brush_icon(self, button, brush_name):
        if not brush_name:
            return
        try:
            preset = Krita.instance().resources("preset").get(brush_name)
            if not preset:
                button.setText("?")
                return
            image = preset.image()
            if image:
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull():
                    button.setIcon(QIcon(pixmap))
                    button.setIconSize(self.item_icon_size())
                    button.setText("")
                    button.setStyleSheet(
                        "QPushButton { padding: 0px; border: 1px solid #555; background: #2f2f2f; }"
                    )
                    return
        except Exception as exc:
            print(f"Quick Access Palette brush icon error: {exc}")
        button.setText(brush_name[:1] if brush_name else "?")

    def apply_action_style(
        self, button, alias, has_icon=False, default_bg="#3a263f", default_fg="#ffffff"
    ):
        bg = alias.get("background_color") or default_bg
        fg = alias.get("font_color") or default_fg
        size = alias.get("font_size") or "18"
        padding = "0px" if has_icon else "2px 6px"
        button.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {fg}; font-size: {size}px; border: 1px solid #6b4a73; border-radius: 4px; padding: {padding}; }}"
        )

    def apply_label_style(self, label, item):
        bg = item.payload.get("backgroundColor", "transparent")
        fg = item.payload.get("fontColor", "#4FC3F7")
        size = item.payload.get("fontSize", "18")
        background_rule = (
            f"background: {bg};" if bg != "transparent" else "background: transparent;"
        )
        label.setStyleSheet(
            f"QLabel {{ {background_rule} color: {fg}; font-size: {size}px; font-weight: bold; padding: 0px 4px; }}"
        )

    def apply_issue_style(self, widget, item):
        if item.id in self.issue_map:
            widget.setToolTip(
                "; ".join(issue.message for issue in self.issue_map[item.id])
            )
            widget.setStyleSheet(widget.styleSheet() + " border: 2px solid #ff4d4d;")

    def on_tab_changed(self, index):
        if index < 0 or index >= len(self.controller.document.tabs):
            return
        self.controller.set_active_tab(self.controller.document.tabs[index].id)

    def add_tab(self):
        name, ok = QInputDialog.getText(
            self,
            "Add Tab",
            "Tab name:",
            text=f"Tab {len(self.controller.document.tabs) + 1}",
        )
        if ok and name.strip():
            self.controller.add_tab(name.strip())
            self.reload_tabs()

    def add_current_brush(self):
        view = self.active_view()
        if not view:
            return
        preset = view.currentBrushPreset()
        if not preset:
            return
        self.controller.add_brush(preset.name())
        self.reload_tabs()

    def add_action(self):
        self.actions = ActionManager.get_actions_dict()
        if not self.actions:
            QMessageBox.warning(
                self, "No Actions", "No Krita actions are available yet."
            )
            return
        selector = ActionSelectorDialog(list(self.actions.values()), parent=self)
        if not selector.exec() or not selector.selected_action:
            return
        self.configure_and_add_action(selector.selected_action)

    def configure_and_add_action(self, action):
        action_id = action.objectName()
        dialog = ActionItemConfigDialog(
            self.actions,
            parent=self,
            selected_action_id=action_id,
            config=self.action_alias_dialog_config(action_id),
        )
        if dialog.exec():
            config = dialog.get_config()
            action_id = config.pop("action_id")
            self.save_action_alias(action_id, config)
            self.controller.add_action(action_id)
            self.reload_tabs()

    def add_label(self):
        text, ok = QInputDialog.getText(self, "Add Label", "Label text:")
        if ok and text:
            self.controller.add_label(text)
            self.reload_tabs()

    def add_separator(self):
        self.controller.add_separator()
        self.reload_tabs()

    def add_docker_toggle(self):
        dialog = DockerToggleItemConfigDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            docker_id = config.pop("docker_id", "")
            if not docker_id:
                QMessageBox.warning(
                    self, "No Docker Selected", "Please select a docker."
                )
                return
            self.save_docker_alias(docker_id, config)
            self.controller.add_docker_toggle(docker_id)
            self.reload_tabs()

    def add_color(self):
        dialog = ColorItemConfigDialog(
            config={"color": self.current_foreground_color()}, parent=self
        )
        if dialog.exec():
            self.controller.add_color(dialog.get_config().get("color", "#ffffff"))
            self.reload_tabs()

    def current_foreground_color(self):
        view = self.active_view()
        if not view:
            return "#ffffff"
        managed_color = view.foregroundColor()
        qcolor = managed_color.colorForCanvas(view.canvas()) if managed_color else None
        return qcolor.name() if qcolor and qcolor.isValid() else "#ffffff"

    def add_script(self):
        dialog = ScriptItemConfigDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            script_path = config.pop("script_path", "")
            self.controller.add_script(script_path, config=config)
            self.reload_tabs()

    def show_grid_edit_dialog(self):
        grid = self.controller.active_grid()
        if not grid:
            return
        dialog = GridEditDialog(grid, parent=self)
        if dialog.exec() and dialog.saved_items is not None:
            self.controller.replace_active_grid_items(dialog.saved_items, compact=False)
            self.reload_tabs()

    def show_gesture_config_dialog(self):
        dialog = GestureConfigDialog(parent=self)
        dialog.exec()

    def show_alias_config_dialog(self):
        dialog = AliasConfigDialog(parent=self)
        dialog.exec()

    def show_config_dialog(self):
        grid = self.controller.active_grid()
        if not grid:
            return
        huesvc_settings = self.controller.huesvc_settings()
        dialog = PaletteConfigDialog(
            grid.columns,
            docker_icon_size=self.controller.docker_icon_size(),
            popup_icon_size=self.controller.popup_icon_size(),
            huesvc_value_font_size=huesvc_settings["value_font_size"],
            huesvc_poll_interval=huesvc_settings["poll_interval"],
            huesvc_rgb_display_mode=huesvc_settings["rgb_display_mode"],
            quick_adjust_settings=self.controller.quick_adjust_settings(),
            parent=self,
        )
        if dialog.exec():
            self.controller.set_columns(dialog.get_columns())
            self.controller.update_settings(
                docker_icon_size=dialog.get_docker_icon_size(),
                popup_icon_size=dialog.get_popup_icon_size(),
            )
            self.controller.update_huesvc_settings(
                value_font_size=dialog.get_huesvc_value_font_size(),
                poll_interval=dialog.get_huesvc_poll_interval(),
                rgb_display_mode=dialog.get_huesvc_rgb_display_mode(),
            )
            self.controller.update_quick_adjust_settings(
                **dialog.get_quick_adjust_settings()
            )
            set_gesture_enabled(dialog.get_gesture_enabled())
            self.reload_tabs()

    def activate_brush(self, brush_name):
        if not brush_name:
            return
        preset = Krita.instance().resources("preset").get(brush_name)
        view = self.active_view()
        if preset and view:
            view.setCurrentBrushPreset(preset)

    def trigger_action(self, action_id):
        action = self.actions.get(action_id)
        if action:
            action.trigger()

    def activate_docker_toggle(self, docker_id):
        if DockerManager:
            DockerManager.toggle_docker(docker_id)

    def activate_color(self, color):
        view = self.active_view()
        if not view:
            return
        managed_color = ManagedColor("RGBA", "U8", "")
        qcolor = QColor(color)
        managed_color.setComponents(
            [qcolor.blueF(), qcolor.greenF(), qcolor.redF(), 1.0]
        )
        view.setForeGroundColor(managed_color)

    def run_script(self, script_path):
        if not script_path or not os.path.isfile(script_path):
            QMessageBox.warning(
                self,
                "Script Not Found",
                f"The script file could not be found:\n{script_path}",
            )
            return
        try:
            with open(script_path, "r", encoding="utf-8") as script_file:
                source = script_file.read()
            exec(
                compile(source, script_path, "exec"),
                {"__name__": "__main__", "Krita": Krita},
            )
        except Exception as exc:
            QMessageBox.warning(self, "Script Error", f"Failed to run script:\n{exc}")

    def active_view(self):
        window = Krita.instance().activeWindow()
        if window:
            return window.activeView()
        return None

    def reload_ui(self):
        self.controller = PaletteController()
        old_widget = self.widget()
        self.root_widget = QWidget()
        self.setWidget(self.root_widget)
        self.build_ui()
        if old_widget:
            old_widget.deleteLater()
