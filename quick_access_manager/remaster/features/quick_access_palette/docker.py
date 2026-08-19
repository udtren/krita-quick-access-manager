"""Minimal Quick Access Palette Docker for the remastered plugin."""

import os

from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita  # type: ignore

from ...infrastructure import get_default_icons_dir, get_system_icons_dir
from ...compat import (
    QDockWidget,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QIcon,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPixmap,
    QSize,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    Qt,
)
from ...infrastructure import ActionManager
from ...shared import ACTION_ITEM, BRUSH_ITEM, LABEL_ITEM, SEPARATOR_ITEM
from .controller import PaletteController
from .dialogs import ActionItemConfigDialog, ActionSelectorDialog, GridEditDialog, LabelItemConfigDialog, PaletteConfigDialog


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
        self.root_layout.addWidget(self.tab_widget)
        self.reload_tabs()

    def build_header(self):
        header = QHBoxLayout()
        self.add_brush_btn = self.create_header_button("add_brush.png", "Add Brush")
        self.add_action_btn = self.create_header_button("actions.png", "Add Action")
        self.add_label_btn = self.create_header_button("label.png", "Add Label")
        self.add_separator_btn = self.create_header_button("seperator.png", "Add Separator")
        self.grid_edit_btn = self.create_header_button("manage_grid.png", "Edit Grid")
        self.config_btn = self.create_header_button("setting.png", "Config")

        self.add_brush_btn.clicked.connect(self.add_current_brush)
        self.add_action_btn.clicked.connect(self.add_action)
        self.add_label_btn.clicked.connect(self.add_label)
        self.add_separator_btn.clicked.connect(self.add_separator)
        self.grid_edit_btn.clicked.connect(self.show_grid_edit_dialog)
        self.config_btn.clicked.connect(self.show_config_dialog)

        for button in (
            self.add_brush_btn,
            self.add_action_btn,
            self.add_label_btn,
            self.add_separator_btn,
            self.grid_edit_btn,
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

    def create_header_button(self, icon_name, tooltip):
        button = QPushButton()
        icon_path = os.path.join(get_system_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        button.setToolTip(tooltip)
        button.setStyleSheet(
            "QPushButton { background-color: #828282; border: none; border-radius: 2px; }"
            "QPushButton:hover { background-color: #9a9a9a; }"
            "QPushButton:pressed { background-color: #6a6a6a; }"
        )
        return button
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
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        for col in range(grid.columns):
            layout.setColumnMinimumWidth(col, 36)
        for item in sorted(grid.items, key=lambda entry: (entry.row, entry.col, entry.id)):
            child = self.create_item_widget(item)
            self.attach_item_context_menu(child, item)
            layout.addWidget(child, item.row, item.col, item.row_span, item.col_span)
        return widget

    def create_item_widget(self, item):
        if item.type == BRUSH_ITEM:
            button = QPushButton()
            button.setFixedSize(42, 42)
            brush_name = item.payload.get("brush_name", "")
            button.setToolTip(brush_name)
            self.apply_brush_icon(button, brush_name)
            button.clicked.connect(lambda checked=False, name=brush_name: self.activate_brush(name))
            self.apply_issue_style(button, item)
            return button

        if item.type == ACTION_ITEM:
            label = item.payload.get("customName") or item.payload.get("action_id", "Action")
            button = QPushButton(label)
            button.setMinimumHeight(36)
            button.clicked.connect(lambda checked=False, action_id=item.payload.get("action_id", ""): self.trigger_action(action_id))
            icon_name = item.payload.get("icon_name")
            has_icon = False
            if icon_name:
                icon_path = self.resolve_icon_path(icon_name)
                if icon_path:
                    button.setIcon(QIcon(icon_path))
                    button.setIconSize(QSize(32, 32))
                    button.setText("")
                    button.setFixedSize(42, 42)
                    has_icon = True
            self.apply_action_style(button, item, has_icon=has_icon)
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

        fallback = QLabel(item.type)
        self.apply_issue_style(fallback, item)
        return fallback

    def attach_item_context_menu(self, widget, item):
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, target=widget, palette_item=item: self.show_item_menu(target, palette_item, pos)
        )

    def show_item_menu(self, widget, item, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        property_action = None
        if item.type in (ACTION_ITEM, LABEL_ITEM):
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

    def show_label_property(self, item):
        dialog = LabelItemConfigDialog(dict(item.payload), parent=self)
        if dialog.exec():
            self.controller.update_label_item(item.id, dialog.get_config())
            self.reload_tabs()
    def show_action_property(self, item):
        action_id = item.payload.get("action_id", "")
        self.actions = ActionManager.get_actions_dict()
        dialog = ActionItemConfigDialog(
            self.actions,
            parent=self,
            selected_action_id=action_id,
            config=dict(item.payload),
        )
        if dialog.exec():
            config = dialog.get_config()
            self.controller.update_action_item(item.id, config)
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
                    button.setIconSize(QSize(38, 38))
                    button.setText("")
                    button.setStyleSheet(
                        "QPushButton { padding: 0px; border: 1px solid #555; background: #2f2f2f; }"
                    )
                    return
        except Exception as exc:
            print("Quick Access Palette brush icon error: {0}".format(exc))
        button.setText(brush_name[:1] if brush_name else "?")
    def apply_action_style(self, button, item, has_icon=False):
        bg = item.payload.get("backgroundColor", "#3a263f")
        fg = item.payload.get("fontColor", "#ffffff")
        size = item.payload.get("fontSize", "18")
        padding = "0px" if has_icon else "2px 6px"
        button.setStyleSheet(
            "QPushButton {{ background: {0}; color: {1}; font-size: {2}px; border: 1px solid #6b4a73; border-radius: 4px; padding: {3}; }}".format(
                bg, fg, size, padding
            )
        )

    def apply_label_style(self, label, item):
        bg = item.payload.get("backgroundColor", "transparent")
        fg = item.payload.get("fontColor", "#4FC3F7")
        size = item.payload.get("fontSize", "18")
        background_rule = "background: {0};".format(bg) if bg != "transparent" else "background: transparent;"
        label.setStyleSheet(
            "QLabel {{ {0} color: {1}; font-size: {2}px; font-weight: bold; padding: 0px 4px; }}".format(
                background_rule, fg, size
            )
        )
    def apply_issue_style(self, widget, item):
        if item.id in self.issue_map:
            widget.setToolTip("; ".join(issue.message for issue in self.issue_map[item.id]))
            widget.setStyleSheet(widget.styleSheet() + " border: 2px solid #ff4d4d;")

    def on_tab_changed(self, index):
        if index < 0 or index >= len(self.controller.document.tabs):
            return
        self.controller.set_active_tab(self.controller.document.tabs[index].id)

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
            QMessageBox.warning(self, "No Actions", "No Krita actions are available yet.")
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
            config={"customName": action_id},
        )
        if dialog.exec():
            config = dialog.get_config()
            action_id = config.pop("action_id")
            self.controller.add_action(action_id, config=config)
            self.reload_tabs()

    def add_label(self):
        text, ok = QInputDialog.getText(self, "Add Label", "Label text:")
        if ok and text:
            self.controller.add_label(text)
            self.reload_tabs()

    def add_separator(self):
        self.controller.add_separator()
        self.reload_tabs()

    def show_grid_edit_dialog(self):
        grid = self.controller.active_grid()
        if not grid:
            return
        dialog = GridEditDialog(grid, parent=self)
        if dialog.exec() and dialog.saved_items is not None:
            self.controller.replace_active_grid_items(dialog.saved_items, compact=False)
            self.reload_tabs()
    def show_config_dialog(self):
        grid = self.controller.active_grid()
        if not grid:
            return
        dialog = PaletteConfigDialog(grid.columns, parent=self)
        if dialog.exec():
            self.controller.set_columns(dialog.get_columns())
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
