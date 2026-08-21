"""Docker UI scaffolding: header buttons/menu, tab widget, and the per-tab/
per-grid widget trees. Item widget construction itself lives in
item_rendering_mixin.py."""

import os

from ...compat import (
    QColor,
    QHBoxLayout,
    QIcon,
    QInputDialog,
    QMenu,
    QPushButton,
    QScrollArea,
    QSize,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from ...infrastructure import AliasRepository, get_system_icons_dir
from .drag_filter import GRID_CELL_SPACING


class UIBuilderMixin:
    """Requires `self.controller`, `self.root_widget`, `self.root_layout`,
    `self.create_item_widget()`, `self.attach_item_context_menu()`,
    `self.attach_item_drag()` and the various `add_*`/`show_*` handlers from
    the composed docker widget."""

    def build_ui(self):
        self.root_layout = QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.root_layout.setSpacing(4)
        self.build_header()
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self.show_tab_menu)
        # Connected once here, never inside reload_tabs() - reconnecting on every
        # reload would fire on_tab_changed (and a config save) once per reload.
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.root_layout.addWidget(self.tab_widget)
        self.reload_tabs()

    def build_header(self):
        header = QHBoxLayout()
        self.menu_btn = QPushButton("Menu")
        self.menu_btn.setFixedHeight(24)
        self.menu_btn.setMenu(self.build_menu())
        self.add_brush_btn = self.create_header_button("add_brush.png", "Add Brush")
        self.grid_edit_btn = self.create_header_button("grid_edit.png", "Edit Grid")
        self.gesture_btn = self.create_header_button("gesture.png", "Gesture Settings")
        self.config_btn = self.create_header_button("setting.png", "Config")
        self.resources_btn = self.create_header_button("resources.png", "Resources")

        self.add_brush_btn.clicked.connect(self.add_current_brush)
        self.grid_edit_btn.clicked.connect(self.show_grid_edit_dialog)
        self.gesture_btn.clicked.connect(self.show_gesture_config_dialog)
        self.config_btn.clicked.connect(self.show_config_dialog)
        self.resources_btn.clicked.connect(self.show_alias_config_dialog)

        self.header_buttons = (
            self.menu_btn,
            self.add_brush_btn,
            self.resources_btn,
            self.gesture_btn,
            self.grid_edit_btn,
            self.config_btn,
        )
        header.addWidget(self.menu_btn)
        for button in self.header_buttons[1:]:
            if not button.icon().isNull():
                button.setFixedSize(24, 24)
                button.setIconSize(QSize(18, 18))
            else:
                button.setFixedHeight(24)
            header.addWidget(button)
        header.addStretch(1)
        self.root_layout.addLayout(header)
        self.apply_header_button_color()

    def build_menu(self):
        menu = QMenu(self)
        menu.addAction("Add Tab", self.add_tab)
        menu.addAction("Add Label", self.add_label)
        menu.addAction("Add H Separator", self.add_separator)
        menu.addAction("Add V Separator", self.add_v_separator)
        menu.addAction("Add Color Swatch", self.add_color)
        menu.addAction("Add Brush Size", self.add_brush_size)
        menu.addAction("Add Brush Blend Mode", self.add_brush_blend_mode)
        menu.addAction("Add Script", self.add_script)
        return menu

    def create_header_button(self, icon_name, tooltip, fallback_text=""):
        button = QPushButton()
        icon_path = os.path.join(get_system_icons_dir(), icon_name) if icon_name else ""
        if icon_path and os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        elif fallback_text:
            button.setText(fallback_text)
        button.setToolTip(tooltip)
        return button

    def header_button_stylesheet(self):
        base = QColor(self.controller.header_button_color())
        hover = base.lighter(115).name()
        pressed = base.darker(115).name()
        return (
            f"QPushButton {{ background-color: {base.name()}; color: #000000; border: none; border-radius: 2px; }}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
            f"QPushButton:pressed {{ background-color: {pressed}; }}"
        )

    def apply_header_button_color(self):
        stylesheet = self.header_button_stylesheet()
        for button in self.header_buttons:
            button.setStyleSheet(stylesheet)

    def item_cell_size(self):
        return self.controller.docker_icon_size()

    def apply_tab_bar_style(self):
        self.tab_widget.setStyleSheet(self.tab_bar_stylesheet())

    def reload_tabs(self):
        self.apply_tab_bar_style()
        self.issue_map = self.controller.validate_active_grid().issues_by_item()
        # One alias read per rebuild instead of one per item.
        self._alias_data = AliasRepository().load()
        self.tab_widget.blockSignals(True)
        while self.tab_widget.count():
            page = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            if page is not None:
                page.setParent(None)
                page.deleteLater()

        for tab in self.controller.document.tabs:
            page = self.create_tab_page(tab)
            self.tab_widget.addTab(page, tab.name)
            if tab.id == self.controller.active_tab_id:
                self.tab_widget.setCurrentWidget(page)

        self.tab_widget.blockSignals(False)

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
        spacing = GRID_CELL_SPACING
        max_bottom = max([item.bottom for item in grid.items], default=1)
        width = max(1, grid.columns) * cell_size + max(0, grid.columns - 1) * spacing
        height = max_bottom * cell_size + max(0, max_bottom - 1) * spacing
        widget.setMinimumSize(width, height)

        for item in sorted(
            grid.items, key=lambda entry: (entry.row, entry.col, entry.id)
        ):
            child = self.create_item_widget(item)
            self.attach_item_context_menu(child, item)
            self.attach_item_drag(child, item)
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

    def on_tab_changed(self, index):
        if index < 0 or index >= len(self.controller.document.tabs):
            return
        self.controller.set_active_tab(self.controller.document.tabs[index].id)
