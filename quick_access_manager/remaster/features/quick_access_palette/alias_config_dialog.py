"""Alias Config dialog: a single shared place to set custom name/color/icon
for Krita Actions and Dockers, independent of any palette item or gesture."""

import os

from ...compat import (
    QColor,
    QColorDialog,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QIcon,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
)
from ...infrastructure import (
    ActionManager,
    AliasRepository,
    DockerManager,
    get_default_icons_dir,
)

COLUMN_LABELS = [
    "ID",
    "Custom Name",
    "Background Color",
    "Font Color",
    "Font Size",
    "Icon",
]


class AliasConfigDialog(QDialog):
    """Shared Action/Docker alias (custom name, colors, font size, icon) editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alias Config")
        self.resize(760, 480)
        self.repository = AliasRepository()
        self.data = self.repository.load()
        self.action_rows = {}
        self.docker_rows = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(
            self.build_tab(
                self.action_rows, self.data.get("actions", {}), self.action_entries()
            ),
            "Actions",
        )
        self.tabs.addTab(
            self.build_tab(
                self.docker_rows, self.data.get("dockers", {}), self.docker_entries()
            ),
            "Dockers",
        )
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

    def docker_entries(self):
        dockers = DockerManager.get_dockers_dict() if DockerManager else {}
        return sorted(dockers.items())

    # ------------------------------------------------------------------
    # Table construction
    # ------------------------------------------------------------------
    def build_tab(self, rows_store, saved_entries, id_label_pairs):
        table = QTableWidget()
        table.setColumnCount(len(COLUMN_LABELS))
        table.setHorizontalHeaderLabels(COLUMN_LABELS)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setRowCount(len(id_label_pairs))

        for row, (item_id, label) in enumerate(id_label_pairs):
            saved = saved_entries.get(item_id, {})
            id_item = QTableWidgetItem(f"{label} ({item_id})")
            table.setItem(row, 0, id_item)

            name_edit = QLineEdit(saved.get("custom_name", ""))
            table.setCellWidget(row, 1, name_edit)

            bg_color = QColor(saved.get("background_color") or "#3a263f")
            bg_button = self.create_color_button(
                bg_color, bool(saved.get("background_color"))
            )
            table.setCellWidget(row, 2, bg_button)

            font_color = QColor(saved.get("font_color") or "#ffffff")
            font_button = self.create_color_button(
                font_color, bool(saved.get("font_color"))
            )
            table.setCellWidget(row, 3, font_button)

            size_edit = QLineEdit(str(saved.get("font_size", "")))
            size_edit.setPlaceholderText("18")
            table.setCellWidget(row, 4, size_edit)

            icon_button = QPushButton("Icon")
            icon_button.setProperty("icon_path", saved.get("icon_name", ""))
            self.update_icon_button(icon_button)
            icon_button.clicked.connect(
                lambda checked=False, btn=icon_button: self.pick_icon(btn)
            )
            table.setCellWidget(row, 5, icon_button)

            rows_store[item_id] = {
                "name_edit": name_edit,
                "bg_button": bg_button,
                "font_button": font_button,
                "size_edit": size_edit,
                "icon_button": icon_button,
            }

        return table

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
