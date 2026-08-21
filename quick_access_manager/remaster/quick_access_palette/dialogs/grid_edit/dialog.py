"""GridEditDialog: edits every tab's grid without auto-compacting on save."""

import os
from uuid import uuid4

from krita import Krita  # type: ignore

from ....compat import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QIcon,
    QMenu,
    QPixmap,
    QPushButton,
    QRect,
    QScrollArea,
    QSize,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from ....infrastructure import AliasRepository, get_default_icons_dir, get_system_icons_dir
from ....shared import (
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
    PaletteItem,
)
from .canvas import GridEditCanvas
from .item_button import GridEditItemButton


class GridEditDialog(QDialog):
    """Edit every tab's grid in a separate dialog without auto-compacting on save."""

    def __init__(self, tabs, active_tab_id=None, parent=None):
        super().__init__(parent)
        self.cell_size = 42
        self.spacing = 4
        self.visible_rows = 10
        self.saved_tabs = None
        # Read once for the lifetime of the dialog: rebuild_grid() runs on every
        # drop and would otherwise re-read the alias config once per item.
        self._alias_data = AliasRepository().load()

        self.tab_order = [tab.id for tab in tabs]
        self.tab_names = {tab.id: tab.name for tab in tabs}
        self.tab_state = {}
        for tab in tabs:
            grid = tab.grids[0] if tab.grids else None
            items = [
                self.normalized_item(PaletteItem.from_dict(item.to_dict()))
                for item in (grid.items if grid else [])
            ]
            self.tab_state[tab.id] = {
                "columns": int(grid.columns) if grid else 8,
                "items": items,
                "selected_ids": set(),
                "history": [],
                "item_widgets": {},
                "drop_highlight": None,
                "canvas": None,
            }

        # Current-tab context, swapped by _load_tab_state/_save_current_tab_state.
        self.current_tab_id = None
        self.columns = 8
        self.items = []
        self.selected_ids = set()
        self.history = []
        self.item_widgets = {}
        self.drop_highlight = None
        self.grid_host = None

        self.setup_ui()

        initial_tab_id = (
            active_tab_id
            if active_tab_id in self.tab_state
            else (self.tab_order[0] if self.tab_order else None)
        )
        for tab_id in self.tab_order:
            self._load_tab_state(tab_id)
            self.rebuild_grid()
            self._save_current_tab_state()
        if initial_tab_id is not None:
            self._load_tab_state(initial_tab_id)
            self.tab_widget.setCurrentIndex(self.tab_order.index(initial_tab_id))
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def alias_entry(self, category, item_id):
        return self._alias_data.get(category, {}).get(item_id, {})

    def normalized_item(self, item):
        if item.type == ACTION_ITEM:
            alias = self.alias_entry("actions", item.payload.get("action_id", ""))
            if alias.get("icon_name"):
                return item.copy_with(col_span=1)
        if item.type == DOCKER_TOGGLE_ITEM:
            alias = self.alias_entry("dockers", item.payload.get("docker_id", ""))
            if alias.get("icon_name"):
                return item.copy_with(col_span=1)
        if item.type == SCRIPT_ITEM and item.payload.get("icon_name"):
            return item.copy_with(col_span=1)
        return item

    def setup_ui(self):
        self.setWindowTitle("Grid Edit")
        self.resize(720, 520)
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.undo_btn = QPushButton()
        undo_icon_path = os.path.join(get_system_icons_dir(), "undo.png")
        if os.path.exists(undo_icon_path):
            self.undo_btn.setIcon(QIcon(undo_icon_path))
            self.undo_btn.setIconSize(QSize(18, 18))
        else:
            self.undo_btn.setText("Undo")
        self.undo_btn.setToolTip("Undo last move/resize")
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(24)
        self.undo_btn.clicked.connect(self.undo)
        control_layout.addWidget(self.undo_btn)
        control_layout.addStretch(1)
        layout.addLayout(control_layout)

        self.tab_widget = QTabWidget()
        for tab_id in self.tab_order:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            canvas = GridEditCanvas(self)
            scroll.setWidget(canvas)
            self.tab_state[tab_id]["canvas"] = canvas
            self.tab_widget.addTab(scroll, self.tab_names[tab_id])
        layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.accept_save)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _save_current_tab_state(self):
        if self.current_tab_id is None:
            return
        state = self.tab_state[self.current_tab_id]
        state["items"] = self.items
        state["selected_ids"] = self.selected_ids
        state["history"] = self.history
        state["item_widgets"] = self.item_widgets
        state["drop_highlight"] = self.drop_highlight

    def _load_tab_state(self, tab_id):
        self.current_tab_id = tab_id
        state = self.tab_state[tab_id]
        self.columns = state["columns"]
        self.items = state["items"]
        self.selected_ids = state["selected_ids"]
        self.history = state["history"]
        self.item_widgets = state["item_widgets"]
        self.drop_highlight = state["drop_highlight"]
        self.grid_host = state["canvas"]
        self.undo_btn.setEnabled(bool(self.history))
        self.update_selection_styles()

    def _on_tab_changed(self, index):
        if index < 0 or index >= len(self.tab_order):
            return
        tab_id = self.tab_order[index]
        if tab_id == self.current_tab_id:
            return
        self._save_current_tab_state()
        self._load_tab_state(tab_id)

    def _rebuild_tab(self, tab_id):
        """Rebuild a tab's canvas immediately, even if it isn't the one currently shown."""
        previous_tab_id = self.current_tab_id
        if previous_tab_id != tab_id:
            self._save_current_tab_state()
        self._load_tab_state(tab_id)
        self.rebuild_grid()
        self._save_current_tab_state()
        if previous_tab_id is not None and previous_tab_id != tab_id:
            self._load_tab_state(previous_tab_id)

    def rebuild_grid(self):
        for child in self.grid_host.findChildren(QWidget):
            child.deleteLater()
        self.item_widgets = {}
        self.drop_highlight = None
        self.grid_host.rubber_band = None
        self.grid_host.origin = None
        spacing = self.spacing
        max_bottom = max([item.bottom for item in self.items], default=0)
        rows = max(self.visible_rows, max_bottom + 2)
        width = self.columns * self.cell_size + max(0, self.columns - 1) * spacing + 8
        height = rows * self.cell_size + max(0, rows - 1) * spacing + 8
        self.grid_host.setMinimumSize(width, height)
        self.grid_host.grid_rows = rows
        self.grid_host.grid_columns = self.columns
        self.grid_host.update()
        for item in sorted(
            self.items, key=lambda entry: (entry.row, entry.col, entry.id)
        ):
            widget = self.create_item_widget(item)
            self.item_widgets[item.id] = widget
            widget.setParent(self.grid_host)
            x, y, item_width, item_height = self.item_geometry(item, spacing)
            widget.setGeometry(x, y, item_width, item_height)
            widget.raise_()
            widget.show()
        self.update_selection_styles()

    def item_geometry(self, item, spacing):
        x = 4 + item.col * (self.cell_size + spacing)
        y = 4 + item.row * (self.cell_size + spacing)
        width = item.col_span * self.cell_size + max(0, item.col_span - 1) * spacing
        height = item.row_span * self.cell_size + max(0, item.row_span - 1) * spacing
        return x, y, width, height

    def show_drop_highlight(self, item, row_delta, col_delta):
        """Outline the cell(s) the dragged item would land on."""
        target_row = max(0, item.row + row_delta)
        target_col = max(0, min(item.col + col_delta, self.columns - item.col_span))
        target = item.copy_with(row=target_row, col=target_col)
        x, y, width, height = self.item_geometry(target, self.spacing)
        if self.drop_highlight is None:
            self.drop_highlight = QFrame(self.grid_host)
            self.drop_highlight.setStyleSheet(
                "QFrame { border: 2px solid #4FC3F7; background-color: rgba(79, 195, 247, 60); border-radius: 3px; }"
            )
        self.drop_highlight.setGeometry(x, y, width, height)
        self.drop_highlight.raise_()
        self.drop_highlight.show()

    def show_resize_highlight(self, item, row_delta=0, col_delta=0):
        """Outline the size a Label/Separator's edge drag would apply -
        col_delta for the right-edge (width) handle, row_delta for the
        bottom-edge (height) handle a vertical Separator uses instead."""
        target_row_span = max(1, item.row_span + row_delta)
        target_col_span = max(
            1, min(self.columns - item.col, item.col_span + col_delta)
        )
        target = item.copy_with(row_span=target_row_span, col_span=target_col_span)
        x, y, width, height = self.item_geometry(target, self.spacing)
        if self.drop_highlight is None:
            self.drop_highlight = QFrame(self.grid_host)
            self.drop_highlight.setStyleSheet(
                "QFrame { border: 2px solid #4FC3F7; background-color: rgba(79, 195, 247, 60); border-radius: 3px; }"
            )
        self.drop_highlight.setGeometry(x, y, width, height)
        self.drop_highlight.raise_()
        self.drop_highlight.show()

    def hide_drop_highlight(self):
        if self.drop_highlight is not None:
            self.drop_highlight.hide()

    def create_item_widget(self, item):
        button = GridEditItemButton(item, self)
        button.setMinimumSize(self.cell_size, 36)
        if (
            item.type
            in (
                BRUSH_ITEM,
                ACTION_ITEM,
                DOCKER_TOGGLE_ITEM,
                COLOR_ITEM,
                SCRIPT_ITEM,
                BRUSH_SIZE_ITEM,
            )
            and item.col_span == 1
        ):
            button.setFixedSize(self.cell_size, self.cell_size)
        self.apply_item_icon(button, item)
        button.clicked.connect(
            lambda checked=False, item_id=item.id: self.toggle_selection(item_id)
        )
        return button

    def apply_item_icon(self, button, item):
        if item.type == BRUSH_ITEM:
            brush_name = item.payload.get("brush_name", "")
            try:
                preset = Krita.instance().resources("preset").get(brush_name)
                image = preset.image() if preset else None
                if image:
                    pixmap = QPixmap.fromImage(image)
                    if not pixmap.isNull():
                        button.setIcon(QIcon(pixmap))
                        button.setIconSize(QSize(34, 34))
                        button.setText("")
                        return
            except Exception:
                pass
        elif item.type == ACTION_ITEM:
            icon_name = self.alias_entry(
                "actions", item.payload.get("action_id", "")
            ).get("icon_name")
            icon_path = self.resolve_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setText("")
        elif item.type == DOCKER_TOGGLE_ITEM:
            icon_name = self.alias_entry(
                "dockers", item.payload.get("docker_id", "")
            ).get("icon_name")
            icon_path = self.resolve_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setText("")
        elif item.type == SCRIPT_ITEM:
            icon_name = item.payload.get("icon_name")
            icon_path = self.resolve_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setText("")
        elif item.type == COLOR_ITEM:
            button.setText("")

    def resolve_icon_path(self, icon_name):
        if not icon_name:
            return None
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
        icon_path = os.path.join(get_default_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            return icon_path
        return None

    def item_label(self, item):
        if item.type == BRUSH_ITEM:
            return "Brush"
        if item.type == ACTION_ITEM:
            action_id = item.payload.get("action_id", "Action")
            return self.alias_entry("actions", action_id).get("custom_name") or action_id
        if item.type == LABEL_ITEM:
            return item.payload.get("text", "Label")
        if item.type == SEPARATOR_ITEM:
            vertical = item.payload.get("orientation") == SEPARATOR_ORIENTATION_VERTICAL
            return "|" if vertical else "---"
        if item.type == DOCKER_TOGGLE_ITEM:
            docker_id = item.payload.get("docker_id", "Docker")
            return self.alias_entry("dockers", docker_id).get("custom_name") or docker_id
        if item.type == COLOR_ITEM:
            return ""
        if item.type == SCRIPT_ITEM:
            return item.payload.get("customName") or "Script"
        if item.type == BRUSH_SIZE_ITEM:
            return item.payload.get("text", "")
        if item.type == BRUSH_BLEND_MODE_ITEM:
            return item.payload.get("text", "")
        return item.type

    def ensure_selected_for_drag(self, item_id):
        if item_id not in self.selected_ids:
            self.selected_ids = {item_id}
            self.update_selection_styles()

    def select_items_in_rect(self, rect, additive=False):
        """Select every item whose cell footprint intersects the marquee rect."""
        hit_ids = set()
        for item in self.items:
            x, y, width, height = self.item_geometry(item, self.spacing)
            if rect.intersects(QRect(x, y, width, height)):
                hit_ids.add(item.id)
        if additive:
            self.selected_ids |= hit_ids
        else:
            self.selected_ids = hit_ids
        self.update_selection_styles()

    def toggle_selection(self, item_id):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if item_id in self.selected_ids:
                self.selected_ids.remove(item_id)
            else:
                self.selected_ids.add(item_id)
        else:
            self.selected_ids = {item_id}
        self.update_selection_styles()

    def update_selection_styles(self):
        for item in self.items:
            widget = self.item_widgets.get(item.id)
            if not widget:
                continue
            widget.setStyleSheet(self.item_style(item, item.id in self.selected_ids))

    def item_style(self, item, selected):
        colors = {
            BRUSH_ITEM: ("#2f2f2f", "#555555"),
            ACTION_ITEM: ("#3a263f", "#6b4a73"),
            LABEL_ITEM: (
                item.payload.get("backgroundColor", "#263746"),
                item.payload.get("fontColor", "#4FC3F7"),
            ),
            SEPARATOR_ITEM: ("#303030", "#777777"),
            DOCKER_TOGGLE_ITEM: ("#263a2f", "#4a8b6b"),
            COLOR_ITEM: (
                item.payload.get("color", "#ffffff"),
                COLOR_SWATCH_BORDER_COLOR,
            ),
            SCRIPT_ITEM: ("#2f2a1f", "#8b7a4a"),
            BRUSH_SIZE_ITEM: (
                item.payload.get("backgroundColor", "#3a263f"),
                "#6b4a73",
            ),
            BRUSH_BLEND_MODE_ITEM: (
                item.payload.get("backgroundColor", "#263a3a"),
                "#4a8b8b",
            ),
        }
        background, border = colors.get(item.type, ("#333333", "#555555"))
        if item.type == COLOR_ITEM and not selected:
            border_width = COLOR_SWATCH_BORDER_WIDTH
        else:
            border_width = 2 if selected else 1
        border_color = "#4FC3F7" if selected else border
        custom_text_color_types = (LABEL_ITEM, BRUSH_SIZE_ITEM, BRUSH_BLEND_MODE_ITEM)
        text_color = (
            item.payload.get("fontColor", "#ffffff")
            if item.type in custom_text_color_types
            else "#ffffff"
        )
        font_size = (
            item.payload.get("fontSize", "18")
            if item.type in custom_text_color_types
            else "18"
        )
        return (
            f"QPushButton {{ background: {background}; color: {text_color}; font-size: {font_size}px; border: {border_width}px solid {border_color}; "
            "border-radius: 3px; padding: 0px 4px; }"
        )

    def resize_axis(self, item):
        """"row" for a vertical Separator (it grows/shrinks by row_span);
        "col" for everything else resizable (Label, horizontal Separator,
        Action)."""
        if (
            item.type == SEPARATOR_ITEM
            and item.payload.get("orientation") == SEPARATOR_ORIENTATION_VERTICAL
        ):
            return "row"
        return "col"

    def is_resizable(self, item):
        """Label/Separator resize freely; text-mode Action/Docker/Script items
        resize by width, while icon-mode variants are pinned to col_span=1 by
        the controller on load/update."""
        if item.type in (LABEL_ITEM, SEPARATOR_ITEM):
            return True
        if item.type == ACTION_ITEM:
            action_id = item.payload.get("action_id", "")
            return not self.alias_entry("actions", action_id).get("icon_name")
        if item.type == DOCKER_TOGGLE_ITEM:
            docker_id = item.payload.get("docker_id", "")
            return not self.alias_entry("dockers", docker_id).get("icon_name")
        if item.type == SCRIPT_ITEM:
            return not item.payload.get("icon_name")
        return False

    def selected_items(self):
        return [item for item in self.items if item.id in self.selected_ids]

    def show_item_context_menu(self, item, global_pos):
        if item.id not in self.selected_ids:
            self.selected_ids = {item.id}
            self.update_selection_styles()
        if not self.selected_items():
            return
        other_tab_ids = [tid for tid in self.tab_order if tid != self.current_tab_id]
        menu = QMenu(self)
        copy_menu = menu.addMenu("Copy to Tab")
        move_menu = menu.addMenu("Move to Tab")
        copy_menu.setEnabled(bool(other_tab_ids))
        move_menu.setEnabled(bool(other_tab_ids))
        for tab_id in other_tab_ids:
            name = self.tab_names.get(tab_id, tab_id)
            copy_action = copy_menu.addAction(name)
            copy_action.triggered.connect(
                lambda checked=False, tid=tab_id: self.copy_selected_to_tab(tid)
            )
            move_action = move_menu.addAction(name)
            move_action.triggered.connect(
                lambda checked=False, tid=tab_id: self.move_selected_to_tab(tid)
            )
        menu.exec(global_pos)

    def _new_item_id(self, item_type):
        return f"{item_type}-{uuid4().hex[:12]}"

    def copy_selected_to_tab(self, target_tab_id):
        selected = self.selected_items()
        if not selected or target_tab_id == self.current_tab_id:
            return
        self._push_history()
        clones = [item.copy_with(id=self._new_item_id(item.type)) for item in selected]
        self._append_items_to_tab(target_tab_id, clones)

    def move_selected_to_tab(self, target_tab_id):
        selected = self.selected_items()
        if not selected or target_tab_id == self.current_tab_id:
            return
        self._push_history()
        moved_ids = {item.id for item in selected}
        clones = [item.copy_with(id=self._new_item_id(item.type)) for item in selected]
        self.items = [item for item in self.items if item.id not in moved_ids]
        self.selected_ids -= moved_ids
        self.rebuild_grid()
        self._append_items_to_tab(target_tab_id, clones)

    def _append_items_to_tab(self, target_tab_id, new_items):
        """Place copied/moved items below the target tab's last existing row, same as a new item add."""
        if not new_items:
            return
        target_state = self.tab_state[target_tab_id]
        target_items = target_state["items"]
        target_columns = target_state["columns"]
        base_row = max((it.bottom for it in target_items), default=0)
        min_row = min(it.row for it in new_items)
        min_col = min(it.col for it in new_items)
        placed = []
        for it in new_items:
            new_col = min(
                max(0, it.col - min_col), max(0, target_columns - it.col_span)
            )
            placed.append(it.copy_with(row=base_row + (it.row - min_row), col=new_col))
        target_state["items"] = target_items + placed
        target_state["selected_ids"] = {it.id for it in placed}
        self._rebuild_tab(target_tab_id)

    MAX_HISTORY = 20

    def _push_history(self):
        snapshot = [item.copy_with() for item in self.items]
        self.history.append(snapshot)
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)
        self.undo_btn.setEnabled(True)

    def undo(self):
        if not self.history:
            return
        self.items = self.history.pop()
        self.selected_ids &= {item.id for item in self.items}
        self.undo_btn.setEnabled(bool(self.history))
        self.rebuild_grid()

    def move_selected(self, row_delta, col_delta):
        if not self.selected_ids:
            return
        selected = self.selected_items()
        min_row = min(item.row for item in selected)
        min_col = min(item.col for item in selected)
        row_delta = max(row_delta, -min_row)
        col_delta = max(col_delta, -min_col)
        if row_delta == 0 and col_delta == 0:
            return
        self._push_history()
        moved_selected = []
        for item in selected:
            moved_selected.append(
                item.copy_with(row=item.row + row_delta, col=item.col + col_delta)
            )
        self.items = self.place_group_with_push(moved_selected)
        self.rebuild_grid()

    def place_group_with_push(self, active_items):
        active_ids = {item.id for item in active_items}
        placed = sorted(active_items, key=lambda item: (item.row, item.col, item.id))
        for item in self.sorted_items(
            [item for item in self.items if item.id not in active_ids]
        ):
            candidate = item.copy_with(row=max(0, item.row), col=max(0, item.col))
            if candidate.col_span > self.columns:
                placed.append(candidate)
                continue
            if self.needs_reposition(candidate, placed):
                candidate = self.first_free_position(candidate, placed)
            placed.append(candidate)
        return placed

    def first_free_position(self, item, placed):
        # An item wider than the grid can never satisfy the column check below,
        # so leave it where it is instead of scanning forever.
        if item.col_span > self.columns:
            return item.copy_with(row=max(0, item.row), col=0)
        cursor = self.linear_index(item.row, item.col)
        while True:
            row = cursor // self.columns
            col = cursor % self.columns
            if col + item.col_span <= self.columns:
                candidate = item.copy_with(row=row, col=col)
                if not self.needs_reposition(candidate, placed):
                    return candidate
            cursor += 1

    def needs_reposition(self, item, placed):
        if item.col + item.col_span > self.columns:
            return True
        return any(self.items_overlap(item, other) for other in placed)

    def items_overlap(self, item, other):
        return not (
            item.right <= other.col
            or other.right <= item.col
            or item.bottom <= other.row
            or other.bottom <= item.row
        )

    def sorted_items(self, items):
        return sorted(
            items, key=lambda item: (self.linear_index(item.row, item.col), item.id)
        )

    def linear_index(self, row, col):
        return max(0, int(row)) * self.columns + max(0, int(col))

    def resize_selected(self, row_delta, col_delta):
        selected = self.selected_items()
        if not selected or any(not self.is_resizable(item) for item in selected):
            return
        self._push_history()
        resized = []
        for item in selected:
            resized.append(
                item.copy_with(
                    row_span=max(1, item.row_span + row_delta),
                    # Never let an item grow past the grid width - a wider item
                    # can never be placed and would stall the layout pass.
                    col_span=max(1, min(self.columns, item.col_span + col_delta)),
                )
            )
        self.items = self.place_group_with_push(resized)
        self.rebuild_grid()

    def accept_save(self):
        self._save_current_tab_state()
        self.saved_tabs = {
            tab_id: [PaletteItem.from_dict(item.to_dict()) for item in state["items"]]
            for tab_id, state in self.tab_state.items()
        }
        self.accept()
