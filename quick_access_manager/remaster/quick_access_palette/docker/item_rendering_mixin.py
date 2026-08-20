"""Item widget construction, drag/context-menu attachment, and the
right-click Property dialogs that edit an already-placed item."""

from ...compat import (
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QMenu,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
)
from ...shared import (
    ACTION_ITEM,
    BRUSH_ITEM,
    BRUSH_BLEND_MODE_ITEM,
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
from ..dialogs import (
    ActionItemConfigDialog,
    BrushBlendModeItemConfigDialog,
    BrushSizeItemConfigDialog,
    ColorItemConfigDialog,
    DockerToggleItemConfigDialog,
    LabelItemConfigDialog,
    ScriptItemConfigDialog,
)
from .drag_filter import GRID_CELL_SPACING


class ItemRenderingMixin:
    """Requires `self.controller`, `self.issue_map`, `self.drag_filter`,
    `self.action_map()`, `self.docker_alias_dialog_config()`,
    `self.save_docker_alias()`, `self.action_alias_dialog_config()`,
    `self.save_action_alias()` and `self.reload_tabs()` from the composed
    docker widget (plus alias_entry/resolve_icon_path/apply_*_style/
    apply_brush_icon from ItemStyleMixin/AliasBridgeMixin)."""

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

        if item.type == BRUSH_BLEND_MODE_ITEM:
            button = QPushButton(item.payload.get("text", ""))
            button.setMinimumHeight(36)
            button.setToolTip(f"Set brush blend mode to {item.payload.get('text', '')}")
            self.apply_brush_blend_mode_style(button, item)
            blend_mode_text = item.payload.get("text", "")
            button.clicked.connect(
                lambda checked=False, blend_mode_text=blend_mode_text: self.activate_brush_blend_mode(
                    blend_mode_text
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
            BRUSH_BLEND_MODE_ITEM,
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
            elif item.type == BRUSH_BLEND_MODE_ITEM:
                self.show_brush_blend_mode_property(item)

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

    def show_brush_blend_mode_property(self, item):
        dialog = BrushBlendModeItemConfigDialog(dict(item.payload), parent=self)
        if dialog.exec():
            self.controller.update_brush_blend_mode_item(item.id, dialog.get_config())
            self.reload_tabs()

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
