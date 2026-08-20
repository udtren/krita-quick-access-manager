"""Minimal Quick Access Palette Docker for the remastered plugin."""

import os

from krita import (  # type: ignore
    DockWidgetFactory,
    DockWidgetFactoryBase,
    Krita,
    ManagedColor,
)

from ..compat import (
    QColor,
    QDockWidget,
    QEvent,
    QFrame,
    QHBoxLayout,
    QIcon,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QObject,
    QPixmap,
    QPushButton,
    QRect,
    QRubberBand,
    QScrollArea,
    QSize,
    Qt,
    QTabWidget,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from ..gesture import GestureConfigDialog, set_gesture_enabled
from ..infrastructure import (
    ActionManager,
    AliasRepository,
    DockerManager,
    get_default_icons_dir,
    get_system_icons_dir,
)
from ..shared import (
    ACTION_ITEM,
    BRUSH_ITEM,
    BRUSH_SIZE_ITEM,
    COLOR_ITEM,
    COLOR_SWATCH_BORDER_COLOR,
    COLOR_SWATCH_BORDER_WIDTH,
    DOCKER_TOGGLE_ITEM,
    LABEL_ITEM,
    SCRIPT_ITEM,
    SEPARATOR_ITEM,
    SEPARATOR_ORIENTATION_VERTICAL,
)
from .alias_config_dialog import AliasConfigDialog
from .controller import PaletteController
from .dialogs import (
    ActionItemConfigDialog,
    BrushSizeItemConfigDialog,
    ColorItemConfigDialog,
    DockerToggleItemConfigDialog,
    GridEditDialog,
    LabelItemConfigDialog,
    PaletteConfigDialog,
    ScriptItemConfigDialog,
)


# Gap between grid cells, in pixels. The drag filter maps mouse deltas back to
# cells with it, so it has to match the geometry create_grid_widget() lays out.
GRID_CELL_SPACING = 2


class GridItemDragFilter(QObject):
    """Ctrl + left-drag moves one placed item to another cell of its grid.

    Installed on every item widget the docker builds. A plain left-click still
    activates the item (run the action, pick the brush, ...); only a Ctrl-held
    press starts a drag, and that press is swallowed so the widget never fires
    its click. Everything else - the multi-select marquee, resizing, moving
    items between tabs - stays in the Grid Edit dialog.
    """

    def __init__(self, docker):
        super().__init__(docker)
        self.docker = docker
        self.item_id = None
        self.start_pos = None
        self.highlight = None

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QEvent.MouseButtonPress:
            return self._start_drag(watched, event)
        if self.item_id is None:
            return False
        if event_type == QEvent.MouseMove:
            self._update_highlight(watched, event)
            return True
        if event_type == QEvent.MouseButtonRelease:
            self._finish_drag(watched, event)
            return True
        return False

    # ------------------------------------------------------------------
    def _start_drag(self, watched, event):
        if event.button() != Qt.LeftButton:
            if self.item_id is not None:
                # Any other button during a drag cancels it (and is swallowed,
                # so a right-click aborts instead of opening the item menu).
                self._cancel_drag()
                return True
            return False
        if not (event.modifiers() & Qt.ControlModifier):
            return False
        item_id = watched.property("palette_item_id")
        if not item_id or self.docker.find_active_item(item_id) is None:
            return False
        self.item_id = item_id
        self.start_pos = self._global_pos(event)
        return True

    def _update_highlight(self, watched, event):
        target = self._target_position(watched, event)
        if target is None:
            self._hide_highlight()
            return
        item, row, col = target
        grid_widget = watched.parentWidget()
        if grid_widget is None:
            return
        if self.highlight is None or self.highlight.parentWidget() is not grid_widget:
            self._hide_highlight()
            self.highlight = QRubberBand(QRubberBand.Rectangle, grid_widget)
        self.highlight.setGeometry(
            QRect(*self.docker.cell_geometry(row, col, item.row_span, item.col_span))
        )
        self.highlight.show()

    def _finish_drag(self, watched, event):
        target = self._target_position(watched, event)
        self._cancel_drag()
        if target is None:
            return
        item, row, col = target
        if (row, col) == (item.row, item.col):
            return
        # Deferred: applying the move rebuilds the tab pages, which deletes the
        # very widget whose mouse release is still being delivered.
        QTimer.singleShot(0, lambda: self.docker.move_item(item.id, row, col))

    def _cancel_drag(self):
        self._hide_highlight()
        self.item_id = None
        self.start_pos = None

    def _target_position(self, watched, event):
        """The clamped (item, row, col) this drag currently points at."""
        item = self.docker.find_active_item(self.item_id)
        if item is None or self.start_pos is None:
            return None
        grid = self.docker.controller.active_grid()
        if grid is None:
            return None
        step = self.docker.item_cell_size() + GRID_CELL_SPACING
        delta = self._global_pos(event) - self.start_pos
        row = max(0, item.row + int(round(delta.y() / float(step))))
        col = item.col + int(round(delta.x() / float(step)))
        col = max(0, min(col, max(0, grid.columns - item.col_span)))
        return item, row, col

    def _hide_highlight(self):
        if self.highlight is not None:
            self.highlight.hide()
            self.highlight.setParent(None)
            self.highlight.deleteLater()
            self.highlight = None

    def _global_pos(self, event):
        try:
            return event.globalPos()  # PyQt5
        except AttributeError:
            return event.globalPosition().toPoint()  # PyQt6


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
        # Krita's action table is only needed when a button is actually pressed,
        # so it is discovered lazily instead of walking the widget tree at startup.
        self._action_map = None
        self._alias_data = AliasRepository().load()
        self.issue_map = {}
        # One filter shared by every item widget; item widgets are rebuilt on
        # each reload, so per-widget filter objects would just churn.
        self.drag_filter = GridItemDragFilter(self)
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
        self.grid_edit_btn = self.create_header_button("manage_grid.png", "Edit Grid")
        self.gesture_btn = self.create_header_button("gesture.png", "Gesture Settings")
        self.config_btn = self.create_header_button("setting.png", "Config")

        self.add_brush_btn.clicked.connect(self.add_current_brush)
        self.grid_edit_btn.clicked.connect(self.show_grid_edit_dialog)
        self.gesture_btn.clicked.connect(self.show_gesture_config_dialog)
        self.config_btn.clicked.connect(self.show_config_dialog)

        self.header_buttons = (
            self.menu_btn,
            self.add_brush_btn,
            self.grid_edit_btn,
            self.gesture_btn,
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
        menu.addAction("Add Script", self.add_script)
        menu.addSeparator()
        menu.addAction("Resources", self.show_alias_config_dialog)
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

    def item_icon_size(self):
        size = max(16, self.item_cell_size() - 4)
        return QSize(size, size)

    def tab_bar_stylesheet(self):
        style = self.controller.tab_bar_settings()
        return (
            "QTabBar::tab {"
            f" background: {style['inactive_background_color']};"
            f" color: {style['inactive_font_color']};"
            f" font-size: {style['inactive_font_size']}px;"
            " padding: 4px 10px;"
            " }"
            "QTabBar::tab:selected {"
            f" background: {style['active_background_color']};"
            f" color: {style['active_font_color']};"
            f" font-size: {style['active_font_size']}px;"
            " }"
        )

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
            label.setAlignment(Qt.AlignCenter)
            self.apply_label_style(label, item)
            self.apply_issue_style(label, item)
            return label

        if item.type == SEPARATOR_ITEM:
            vertical = item.payload.get("orientation") == SEPARATOR_ORIENTATION_VERTICAL
            container = QWidget()
            separator = QFrame()
            if vertical:
                layout = QHBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                separator.setFrameShape(QFrame.VLine)
                separator.setFixedWidth(12)
                layout.addWidget(separator, alignment=Qt.AlignHCenter)
            else:
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                separator.setFrameShape(QFrame.HLine)
                separator.setFixedHeight(12)
                layout.addWidget(separator, alignment=Qt.AlignVCenter)
            separator.setFrameShadow(QFrame.Sunken)
            self.apply_issue_style(container, item)
            return container

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
                f"QPushButton {{ background: {color}; border: {COLOR_SWATCH_BORDER_WIDTH}px solid {COLOR_SWATCH_BORDER_COLOR}; border-radius: 4px; }}"
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

        if item.type == BRUSH_SIZE_ITEM:
            button = QPushButton(item.payload.get("text", ""))
            button.setFixedSize(self.item_cell_size(), self.item_cell_size())
            button.setToolTip(f"Set brush size to {item.payload.get('text', '')}")
            self.apply_brush_size_style(button, item)
            size_text = item.payload.get("text", "")
            button.clicked.connect(
                lambda checked=False, size_text=size_text: self.activate_brush_size(
                    size_text
                )
            )
            self.apply_issue_style(button, item)
            return button

        fallback = QLabel(item.type)
        self.apply_issue_style(fallback, item)
        return fallback

    def attach_item_drag(self, widget, item):
        """Let Ctrl + left-drag move this item to another cell."""
        widget.setProperty("palette_item_id", item.id)
        widget.installEventFilter(self.drag_filter)

    def cell_geometry(self, row, col, row_span, col_span):
        """(x, y, width, height) of a cell block, matching create_grid_widget()."""
        cell_size = self.item_cell_size()
        step = cell_size + GRID_CELL_SPACING
        return (
            col * step,
            row * step,
            col_span * cell_size + max(0, col_span - 1) * GRID_CELL_SPACING,
            row_span * cell_size + max(0, row_span - 1) * GRID_CELL_SPACING,
        )

    def find_active_item(self, item_id):
        """The active grid's item with this id, or None if it is on another tab."""
        grid = self.controller.active_grid()
        if grid is None:
            return None
        return next((item for item in grid.items if item.id == item_id), None)

    def move_item(self, item_id, row, col):
        self.controller.move_item(item_id, row, col)
        self.reload_tabs()

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
            BRUSH_SIZE_ITEM,
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
            elif item.type == BRUSH_SIZE_ITEM:
                self.show_brush_size_property(item)

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

    def show_brush_size_property(self, item):
        dialog = BrushSizeItemConfigDialog(dict(item.payload), parent=self)
        if dialog.exec():
            self.controller.update_brush_size_item(item.id, dialog.get_config())
            self.reload_tabs()

    def action_map(self, refresh=False):
        """Krita's {objectName: QAction} table, discovered on first use.

        Deliberately not named `actions` - that would shadow QWidget.actions().
        """
        if refresh or self._action_map is None:
            self._action_map = ActionManager.get_actions_dict()
        return self._action_map

    def show_action_property(self, item):
        action_id = item.payload.get("action_id", "")
        dialog = ActionItemConfigDialog(
            self.action_map(refresh=True),
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
        return self._alias_data.get(category, {}).get(item_id, {})

    def save_alias_entry(self, category, item_id, updates):
        if not item_id:
            return
        repository = AliasRepository()
        data = repository.load()
        entry = dict(data.get(category, {}).get(item_id, {}))
        entry.update(updates)
        data.setdefault(category, {})[item_id] = entry
        repository.save(data)
        self._alias_data = data

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

    def apply_brush_size_style(self, button, item):
        bg = item.payload.get("backgroundColor", "#3a263f")
        fg = item.payload.get("fontColor", "#ffffff")
        size = item.payload.get("fontSize", "18")
        button.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {fg}; font-size: {size}px; font-weight: bold; border: 1px solid #6b4a73; border-radius: 4px; }}"
        )

    def apply_issue_style(self, widget, item):
        issues = self.issue_map.get(item.id)
        if not issues:
            return
        widget.setToolTip("; ".join(issue.message for issue in issues))
        # The existing sheet is a selector block ("QPushButton { ... }"), so the
        # override has to be a block too - a bare property would be discarded.
        class_name = widget.metaObject().className()
        widget.setStyleSheet(
            f"{widget.styleSheet()} {class_name} {{ border: 2px solid #ff4d4d; }}"
        )

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

    def add_label(self):
        text, ok = QInputDialog.getText(self, "Add Label", "Label text:")
        if ok and text:
            self.controller.add_label(text)
            self.reload_tabs()

    def add_separator(self):
        self.controller.add_separator()
        self.reload_tabs()

    def add_v_separator(self):
        self.controller.add_separator(orientation=SEPARATOR_ORIENTATION_VERTICAL)
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

    def add_brush_size(self):
        dialog = BrushSizeItemConfigDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            text = config.pop("text", "1")
            self.controller.add_brush_size(text, config=config)
            self.reload_tabs()

    def show_grid_edit_dialog(self):
        tabs = self.controller.document.tabs
        if not tabs:
            return
        dialog = GridEditDialog(
            tabs, active_tab_id=self.controller.active_tab_id, parent=self
        )
        if dialog.exec() and dialog.saved_tabs is not None:
            for tab_id, items in dialog.saved_tabs.items():
                self.controller.replace_tab_grid_items(tab_id, items, compact=False)
            self.reload_tabs()

    def show_gesture_config_dialog(self):
        dialog = GestureConfigDialog(parent=self)
        dialog.exec()

    def show_alias_config_dialog(self):
        # on_item_added repaints the grid immediately on every Add click, while
        # the (modal) dialog is still open - without it, added items only
        # became visible once the dialog was closed.
        dialog = AliasConfigDialog(
            parent=self, controller=self.controller, on_item_added=self.reload_tabs
        )
        dialog.exec()
        # Reload once more regardless of Save/Cancel, in case the alias
        # name/color/icon fields themselves (not the Add buttons) changed how
        # an already-placed item should render.
        self.reload_tabs()

    def show_config_dialog(self):
        grid = self.controller.active_grid()
        if not grid:
            return
        huesvc_settings = self.controller.huesvc_settings()
        dialog_width, dialog_height = self.controller.config_dialog_size()
        dialog = PaletteConfigDialog(
            grid.columns,
            docker_icon_size=self.controller.docker_icon_size(),
            popup_icon_size=self.controller.popup_icon_size(),
            huesvc_value_font_size=huesvc_settings["value_font_size"],
            huesvc_poll_interval=huesvc_settings["poll_interval"],
            huesvc_rgb_display_mode=huesvc_settings["rgb_display_mode"],
            huesvc_popup_width=huesvc_settings.get("popup_width", 350),
            huesvc_popup_height=huesvc_settings.get("popup_height", 550),
            huesvc_controls_panel_font_size=huesvc_settings.get(
                "controls_panel_font_size", 12
            ),
            quick_adjust_settings=self.controller.quick_adjust_settings(),
            config_dialog_width=dialog_width,
            config_dialog_height=dialog_height,
            huesvc_enabled=self.controller.is_huesvc_enabled(),
            quick_adjust_enabled=self.controller.is_quick_adjust_enabled(),
            header_button_color=self.controller.header_button_color(),
            **{
                f"tab_{key}": value
                for key, value in self.controller.tab_bar_settings().items()
            },
            parent=self,
        )
        if dialog.exec():
            self.controller.set_columns(dialog.get_columns())
            self.controller.update_settings(
                docker_icon_size=dialog.get_docker_icon_size(),
                popup_icon_size=dialog.get_popup_icon_size(),
                config_dialog_width=dialog.get_config_dialog_width(),
                config_dialog_height=dialog.get_config_dialog_height(),
                huesvc_enabled=dialog.get_huesvc_enabled(),
                quick_adjust_enabled=dialog.get_quick_adjust_enabled(),
                header_button_color=dialog.get_header_button_color(),
                tab_active_font_size=dialog.get_tab_active_font_size(),
                tab_active_font_color=dialog.get_tab_active_font_color(),
                tab_active_background_color=dialog.get_tab_active_background_color(),
                tab_inactive_font_size=dialog.get_tab_inactive_font_size(),
                tab_inactive_font_color=dialog.get_tab_inactive_font_color(),
                tab_inactive_background_color=dialog.get_tab_inactive_background_color(),
            )
            self.controller.update_huesvc_settings(
                value_font_size=dialog.get_huesvc_value_font_size(),
                poll_interval=dialog.get_huesvc_poll_interval(),
                rgb_display_mode=dialog.get_huesvc_rgb_display_mode(),
                popup_width=dialog.get_huesvc_popup_width(),
                popup_height=dialog.get_huesvc_popup_height(),
                controls_panel_font_size=dialog.get_huesvc_controls_panel_font_size(),
            )
            self.controller.update_quick_adjust_settings(
                **dialog.get_quick_adjust_settings()
            )
            set_gesture_enabled(dialog.get_gesture_enabled())
            self.apply_header_button_color()
            self.reload_tabs()

    def activate_brush(self, brush_name):
        if not brush_name:
            return
        preset = Krita.instance().resources("preset").get(brush_name)
        view = self.active_view()
        if preset and view:
            view.setCurrentBrushPreset(preset)

    def trigger_action(self, action_id):
        action = self.action_map().get(action_id)
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

    def activate_brush_size(self, size_text):
        view = self.active_view()
        if not view or not size_text:
            return
        try:
            size = float(size_text)
        except ValueError:
            return
        view.setBrushSize(size)

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
