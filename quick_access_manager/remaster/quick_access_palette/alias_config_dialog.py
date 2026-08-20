"""Resources dialog: a single shared place to set custom name/color/icon
for Krita Actions and Dockers, independent of any palette item or gesture."""

import os

from krita import Krita  # type: ignore

from ..compat import (
    QAbstractItemView,
    QColor,
    QColorDialog,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QIcon,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPixmap,
    QPushButton,
    Qt,
    QSize,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from ..infrastructure import (
    ActionManager,
    AliasRepository,
    DockerManager,
    get_default_icons_dir,
)

COLUMN_LABELS = [
    "ID",
    "Shortcut",
    "Custom Name",
    "Background Color",
    "Font Color",
    "Font Size",
    "Icon",
    "Reset",
    "Add",
]

# Fixed pixel width for every column except ID (column 0), which stretches to
# take up the remaining space - the ID text is the only thing here that
# varies enough in length to need it.
FIXED_COLUMN_WIDTHS = {
    "Shortcut": 140,
    "Custom Name": 150,
    "Background Color": 110,
    "Font Color": 110,
    "Font Size": 70,
    "Icon": 70,
    "Reset": 70,
    "Add": 70,
}


class AliasConfigDialog(QDialog):
    """Shared Action/Docker alias (custom name, colors, font size, icon) editor.

    Each row also has an "Add" button that adds that Action/Docker Toggle
    straight to the Quick Access Palette's active grid - no separate item
    dialog, since this dialog's own fields are already the item's styling.
    """

    def __init__(self, parent=None, controller=None, on_item_added=None):
        """`on_item_added`, if given, is called after every Add click (Actions,
        Dockers, or Brushes) so the docker's own grid can repaint immediately
        while this dialog is still open, instead of only once it closes."""
        super().__init__(parent)
        self.setWindowTitle("Resources")
        self.resize(760, 480)
        self.repository = AliasRepository()
        self.data = self.repository.load()
        self.controller = controller
        self.on_item_added = on_item_added
        self.action_rows = {}
        self.docker_rows = {}
        # Items added from this dialog fill the grid's last empty row from its
        # left column onward (wrapping to the next row when full) instead of
        # each Add starting a new row. The cursor lives for as long as this
        # window is open; done() releases it.
        if self.controller is not None:
            self.controller.begin_sequential_placement()
        self.setup_ui()

    def done(self, result):
        # Covers Save, Cancel, Esc, and the window's close button alike.
        if self.controller is not None:
            self.controller.end_sequential_placement()
        super().done(result)

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        actions_table = self.build_tab(
            self.action_rows,
            self.data.get("actions", {}),
            self.action_entries(),
            self._add_action_item,
            shortcut_lookup=self.action_shortcut_text,
        )
        self.tabs.addTab(self._wrap_with_id_filter(actions_table), "Actions")
        dockers_table = self.build_tab(
            self.docker_rows,
            self.data.get("dockers", {}),
            self.docker_entries(),
            self._add_docker_toggle_item,
        )
        self.tabs.addTab(dockers_table, "Dockers")
        self.tabs.addTab(self.build_brushes_tab(), "Brushes")
        layout.addWidget(self.tabs)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def action_entries(self):
        actions = ActionManager.get_actions_dict() if ActionManager else {}
        entries = []
        for action_id, action in sorted(actions.items()):
            label = action.text() if hasattr(action, "text") else action_id
            entries.append((action_id, label))
        return entries

    def action_shortcut_text(self, action_id):
        action = ActionManager.get_action_by_id(action_id) if ActionManager else None
        if action is None or not hasattr(action, "shortcuts"):
            return ""
        return ", ".join(
            shortcut.toString() for shortcut in action.shortcuts() if not shortcut.isEmpty()
        )

    def docker_entries(self):
        dockers = DockerManager.get_dockers_dict() if DockerManager else {}
        return sorted(dockers.items())

    def brush_entries(self):
        try:
            presets = Krita.instance().resources("preset")
        except Exception:
            presets = {}
        return sorted(presets.items(), key=lambda pair: pair[0])

    # ------------------------------------------------------------------
    # Brushes tab: icon grid, name filter, multi-select "Add"
    # ------------------------------------------------------------------
    def build_brushes_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        top_row = QHBoxLayout()
        self.brush_add_btn = QPushButton("Add")
        self.brush_add_btn.setToolTip(
            "Add every selected brush to the active grid, in list order."
        )
        self.brush_add_btn.clicked.connect(self._add_selected_brushes)
        top_row.addWidget(self.brush_add_btn)

        self.brush_filter_edit = QLineEdit()
        self.brush_filter_edit.setPlaceholderText("Filter by name...")
        self.brush_filter_edit.textChanged.connect(self._apply_brush_filter)
        top_row.addWidget(self.brush_filter_edit, 1)
        layout.addLayout(top_row)

        self.brush_list = QListWidget()
        self.brush_list.setViewMode(QListWidget.IconMode)
        self.brush_list.setResizeMode(QListWidget.Adjust)
        self.brush_list.setMovement(QListWidget.Static)
        # Click selects one; Ctrl+click adds/removes from the selection.
        self.brush_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.brush_list.setIconSize(QSize(56, 56))
        self.brush_list.setGridSize(QSize(76, 90))
        self.brush_list.setWordWrap(True)
        self.brush_list.setUniformItemSizes(True)
        self.brush_list.setSpacing(2)
        layout.addWidget(self.brush_list)

        for brush_name, preset in self.brush_entries():
            item = QListWidgetItem(brush_name)
            item.setToolTip(brush_name)
            item.setData(Qt.UserRole, brush_name)
            icon = self._brush_icon(preset)
            if icon is not None:
                item.setIcon(icon)
            self.brush_list.addItem(item)

        return container

    def _brush_icon(self, preset):
        try:
            image = preset.image()
            if image:
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull():
                    return QIcon(pixmap)
        except Exception:
            pass
        return None

    def _apply_brush_filter(self, text):
        needle = text.lower()
        for row in range(self.brush_list.count()):
            item = self.brush_list.item(row)
            name = item.data(Qt.UserRole) or ""
            item.setHidden(bool(needle and needle not in name.lower()))

    def _add_selected_brushes(self):
        if self.controller is None:
            return
        # Row order (alphabetical, matching the grid's own layout) rather than
        # click order - deterministic and matches what the user sees on screen.
        names = [
            self.brush_list.item(row).data(Qt.UserRole)
            for row in range(self.brush_list.count())
            if self.brush_list.item(row).isSelected()
        ]
        if not names:
            return
        for name in names:
            self.controller.add_brush(name)
        if self.on_item_added is not None:
            self.on_item_added()

        self.brush_list.clearSelection()
        self.brush_add_btn.setText(f"Added {len(names)}")
        self.brush_add_btn.setEnabled(False)
        QTimer.singleShot(700, self._reset_brush_add_button)

    def _reset_brush_add_button(self):
        try:
            self.brush_add_btn.setText("Add")
            self.brush_add_btn.setEnabled(True)
        except RuntimeError:
            pass  # dialog was closed before the timer fired; button is gone

    # ------------------------------------------------------------------
    # Table construction
    # ------------------------------------------------------------------
    def build_tab(
        self, rows_store, saved_entries, id_label_pairs, add_callback, shortcut_lookup=None
    ):
        table = QTableWidget()
        table.setColumnCount(len(COLUMN_LABELS))
        table.setHorizontalHeaderLabels(COLUMN_LABELS)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for column, label in enumerate(COLUMN_LABELS):
            width = FIXED_COLUMN_WIDTHS.get(label)
            if width is not None:
                header.setSectionResizeMode(column, QHeaderView.Fixed)
                table.setColumnWidth(column, width)
        table.setRowCount(len(id_label_pairs))

        for row, (item_id, label) in enumerate(id_label_pairs):
            saved = saved_entries.get(item_id, {})
            id_item = QTableWidgetItem(f"{label} ({item_id})")
            id_item.setData(Qt.UserRole, item_id)
            table.setItem(row, 0, id_item)

            shortcut_text = shortcut_lookup(item_id) if shortcut_lookup else ""
            shortcut_item = QTableWidgetItem(shortcut_text)
            table.setItem(row, 1, shortcut_item)

            name_edit = QLineEdit(saved.get("custom_name", ""))
            table.setCellWidget(row, 2, name_edit)

            bg_color = QColor(saved.get("background_color") or "#3a263f")
            bg_button = self.create_color_button(
                bg_color, bool(saved.get("background_color"))
            )
            table.setCellWidget(row, 3, bg_button)

            font_color = QColor(saved.get("font_color") or "#ffffff")
            font_button = self.create_color_button(
                font_color, bool(saved.get("font_color"))
            )
            table.setCellWidget(row, 4, font_button)

            size_edit = QLineEdit(str(saved.get("font_size", "")))
            size_edit.setPlaceholderText("18")
            table.setCellWidget(row, 5, size_edit)

            icon_button = QPushButton("Icon")
            icon_button.setProperty("icon_path", saved.get("icon_name", ""))
            self.update_icon_button(icon_button)
            icon_button.clicked.connect(
                lambda checked=False, btn=icon_button: self.pick_icon(btn)
            )
            table.setCellWidget(row, 6, icon_button)

            reset_button = QPushButton("Reset")
            reset_button.setToolTip(
                "Clear background/font color, font size, and icon (keeps Custom Name)"
            )
            reset_button.clicked.connect(
                lambda checked=False, iid=item_id, store=rows_store: self._reset_row(
                    store, iid
                )
            )
            table.setCellWidget(row, 7, reset_button)

            add_button = QPushButton("Add")
            add_button.setToolTip(f"Add to the active grid: {label} ({item_id})")
            add_button.clicked.connect(
                lambda checked=False, iid=item_id, btn=add_button: self._on_add_clicked(
                    add_callback, iid, btn
                )
            )
            table.setCellWidget(row, 8, add_button)

            rows_store[item_id] = {
                "name_edit": name_edit,
                "bg_button": bg_button,
                "font_button": font_button,
                "size_edit": size_edit,
                "icon_button": icon_button,
            }

        return table

    # ------------------------------------------------------------------
    # Add-to-grid (per-row "Add" button)
    # ------------------------------------------------------------------
    def _on_add_clicked(self, add_callback, item_id, button):
        add_callback(item_id)
        # Brief inline feedback instead of a dialog - the item is already
        # fully styled from this row's own fields, so there's nothing left
        # to configure before it lands on the grid.
        button.setText("Added")
        button.setEnabled(False)
        QTimer.singleShot(700, lambda: self._reset_add_button(button))

    def _reset_add_button(self, button):
        try:
            button.setText("Add")
            button.setEnabled(True)
        except RuntimeError:
            pass  # dialog was closed before the timer fired; button is gone

    def _reset_row(self, rows_store, item_id):
        widgets = rows_store[item_id]
        widgets["bg_button"].setProperty("color", "")
        self.update_color_button(widgets["bg_button"])
        widgets["font_button"].setProperty("color", "")
        self.update_color_button(widgets["font_button"])
        widgets["size_edit"].clear()
        widgets["icon_button"].setProperty("icon_path", "")
        self.update_icon_button(widgets["icon_button"])

    def _add_action_item(self, action_id):
        if self.controller is not None:
            self.controller.add_action(action_id)
            if self.on_item_added is not None:
                self.on_item_added()

    def _add_docker_toggle_item(self, docker_id):
        if self.controller is not None:
            self.controller.add_docker_toggle(docker_id)
            if self.on_item_added is not None:
                self.on_item_added()

    def _wrap_with_id_filter(self, table):
        """Add an ID filter box above `table` - same "Filter by internal ID..."
        behavior as the rest of the plugin's ID filter fields."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        filter_edit = QLineEdit()
        filter_edit.setPlaceholderText("Filter by internal ID...")
        filter_edit.textChanged.connect(
            lambda text, t=table: self._apply_id_filter(t, text)
        )
        container_layout.addWidget(filter_edit)
        container_layout.addWidget(table)
        return container

    def _apply_id_filter(self, table, text):
        needle = text.lower()
        for row in range(table.rowCount()):
            id_item = table.item(row, 0)
            item_id = id_item.data(Qt.UserRole) or "" if id_item else ""
            table.setRowHidden(row, bool(needle and needle not in item_id.lower()))

    def create_color_button(self, color, is_set):
        button = QPushButton(color.name() if is_set else "Default")
        button.setProperty("color", color.name() if is_set else "")
        self.update_color_button(button)
        button.clicked.connect(lambda checked=False, btn=button: self.pick_color(btn))
        return button

    def update_color_button(self, button):
        color = button.property("color") or ""
        if color:
            button.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
            button.setText(color)
        else:
            button.setStyleSheet("")
            button.setText("Default")

    def pick_color(self, button):
        current = QColor(button.property("color") or "#ffffff")
        color = QColorDialog.getColor(current, self, "Select Color")
        if color.isValid():
            button.setProperty("color", color.name())
            self.update_color_button(button)

    def update_icon_button(self, button):
        icon_path = button.property("icon_path") or ""
        if icon_path:
            resolved = self.resolve_icon_path(icon_path)
            if resolved:
                button.setIcon(QIcon(resolved))
            button.setToolTip(icon_path)
        else:
            button.setIcon(QIcon())
            button.setToolTip("No icon selected")

    def resolve_icon_path(self, icon_name):
        if not icon_name:
            return None
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
        icon_path = os.path.join(get_default_icons_dir(), icon_name)
        return icon_path if os.path.exists(icon_path) else None

    def pick_icon(self, button):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            get_default_icons_dir(),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if selected:
            button.setProperty("icon_path", self._stored_icon_path(selected))
            self.update_icon_button(button)

    def _stored_icon_path(self, selected_path):
        default_dir = os.path.normcase(os.path.abspath(get_default_icons_dir()))
        selected_abs = os.path.abspath(selected_path)
        selected_dir = os.path.normcase(os.path.dirname(selected_abs))
        if selected_dir == default_dir:
            return os.path.basename(selected_abs)
        return selected_abs

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def collect_entries(self, rows_store):
        entries = {}
        for item_id, widgets in rows_store.items():
            entry = {
                "custom_name": widgets["name_edit"].text().strip(),
                "background_color": widgets["bg_button"].property("color") or "",
                "font_color": widgets["font_button"].property("color") or "",
                "font_size": widgets["size_edit"].text().strip(),
                "icon_name": widgets["icon_button"].property("icon_path") or "",
            }
            if any(entry.values()):
                entries[item_id] = entry
        return entries

    def save_and_close(self):
        self.data = {
            "actions": self.collect_entries(self.action_rows),
            "dockers": self.collect_entries(self.docker_rows),
        }
        self.repository.save(self.data)
        self.accept()
