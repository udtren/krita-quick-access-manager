"""Execution-only popup for the remastered Quick Access Palette."""

import os

from krita import Krita, ManagedColor  # type: ignore

from ..compat import (
    QColor,
    QCursor,
    QDialog,
    QFrame,
    QHBoxLayout,
    QIcon,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QShortcut,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from ..infrastructure import (
    ActionManager,
    AliasRepository,
    DockerManager,
    get_system_icons_dir,
)
from ..shared import (
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
from .controller import PaletteController
from .item_style_mixin import ItemStyleMixin


class QuickAccessPalettePopup(QDialog, ItemStyleMixin):
    """Read-only popup that executes palette items."""

    def __init__(self, parent=None, close_shortcuts=None):
        super().__init__(parent)
        self.close_shortcuts = list(close_shortcuts or [])
        self.shortcut_handlers = []
        self.controller = PaletteController()
        self._alias_data = AliasRepository().load()
        self.cell_size = self.controller.popup_icon_size()
        self.spacing = 2
        self.is_pinned = False
        self.drag_position = None
        self.pin_button = None
        self.setWindowTitle("Quick Access Palette")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.resize(420, 360)
        self.build_ui()
        self.register_close_shortcuts()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        self.create_toolbar(layout)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        self.reload_tabs()

    def create_toolbar(self, layout):
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 4)
        toolbar.setSpacing(4)
        toolbar.addStretch(1)

        self.pin_button = self.create_toolbar_button("pin_unpinned.png", "Pin window")
        self.pin_button.clicked.connect(self.toggle_pin)
        close_button = self.create_toolbar_button("circle-xmark.png", "Close")
        close_button.clicked.connect(self.close_popup)
        toolbar.addWidget(self.pin_button)
        toolbar.addWidget(close_button)
        layout.addLayout(toolbar)
        self.update_pin_icon()

    def create_toolbar_button(self, icon_name, tooltip):
        button = QPushButton()
        button.setFixedSize(16, 16)
        icon_path = os.path.join(get_system_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(button.size())
        elif icon_name == "circle-xmark.png":
            button.setText("X")
        button.setToolTip(tooltip)
        button.setStyleSheet(
            "QPushButton { background-color: #828282; border: none; border-radius: 2px; color: #fff; font-weight: bold; }"
            "QPushButton:hover { background-color: #9a9a9a; }"
            "QPushButton:pressed { background-color: #6a6a6a; }"
        )
        return button

    def update_pin_icon(self):
        if not self.pin_button:
            return
        icon_name = "pin_pinned.png" if self.is_pinned else "pin_unpinned.png"
        tooltip = "Unpin window" if self.is_pinned else "Pin window"
        icon_path = os.path.join(get_system_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            self.pin_button.setIcon(QIcon(icon_path))
            self.pin_button.setIconSize(self.pin_button.size())
        self.pin_button.setToolTip(tooltip)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.update_pin_icon()

    def close_popup(self):
        self.is_pinned = False
        self.close()

    def register_close_shortcuts(self):
        for key_sequence in self.close_shortcuts:
            try:
                if key_sequence.isEmpty():
                    continue
            except AttributeError:
                pass
            shortcut = QShortcut(key_sequence, self)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.activated.connect(self.close_popup)
            self.shortcut_handlers.append(shortcut)

    def show_at_cursor(self):
        self.adjustSize()
        cursor_pos = QCursor.pos()
        self.move(
            cursor_pos.x() - self.width() // 2, cursor_pos.y() - self.height() // 3
        )
        self.show()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def item_cell_size(self):
        return self.cell_size

    def reload_tabs(self):
        self.tab_widget.setStyleSheet(self.tab_bar_stylesheet())
        while self.tab_widget.count():
            self.tab_widget.removeTab(0)
        for tab in self.controller.document.tabs:
            page = self.create_tab_page(tab)
            self.tab_widget.addTab(page, tab.name)
            if tab.id == self.controller.active_tab_id:
                self.tab_widget.setCurrentWidget(page)

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
        max_bottom = max([item.bottom for item in grid.items], default=1)
        width = (
            max(1, grid.columns) * self.cell_size
            + max(0, grid.columns - 1) * self.spacing
        )
        height = max_bottom * self.cell_size + max(0, max_bottom - 1) * self.spacing
        widget.setMinimumSize(width, height)

        for item in sorted(
            grid.items, key=lambda entry: (entry.row, entry.col, entry.id)
        ):
            child = self.create_item_widget(item)
            child.setParent(widget)
            x = item.col * (self.cell_size + self.spacing)
            y = item.row * (self.cell_size + self.spacing)
            child_width = (
                item.col_span * self.cell_size
                + max(0, item.col_span - 1) * self.spacing
            )
            child_height = (
                item.row_span * self.cell_size
                + max(0, item.row_span - 1) * self.spacing
            )
            child.setGeometry(x, y, child_width, child_height)
            child.show()
        return widget

    def create_item_widget(self, item):
        if item.type == BRUSH_ITEM:
            button = QPushButton()
            button.setFixedSize(self.cell_size, self.cell_size)
            brush_name = item.payload.get("brush_name", "")
            button.setToolTip(brush_name)
            self.apply_brush_icon(button, brush_name)
            button.clicked.connect(
                lambda checked=False, name=brush_name: self.activate_brush(name)
            )
            return button

        if item.type == ACTION_ITEM:
            action_id = item.payload.get("action_id", "")
            alias = self.alias_entry("actions", action_id)
            button = QPushButton(alias.get("custom_name") or action_id)
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
                    button.setFixedSize(self.cell_size, self.cell_size)
                    has_icon = True
            self.apply_action_style(button, alias, has_icon)
            return button

        if item.type == LABEL_ITEM:
            label = QLabel(item.payload.get("text", "Label"))
            label.setAlignment(Qt.AlignCenter)
            self.apply_label_style(label, item)
            return label

        if item.type == SEPARATOR_ITEM:
            vertical = item.payload.get("orientation") == SEPARATOR_ORIENTATION_VERTICAL
            container = QWidget()
            separator = QFrame()
            separator.setFrameShape(QFrame.NoFrame)
            thickness = max(1, int(item.payload.get("thickness", 2)))
            color = item.payload.get("color", "#5a5a5a")
            separator.setStyleSheet(f"background-color: {color};")
            if vertical:
                layout = QHBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                separator.setFixedWidth(thickness)
                layout.addWidget(separator, alignment=Qt.AlignHCenter)
            else:
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                separator.setFixedHeight(thickness)
                layout.addWidget(separator, alignment=Qt.AlignVCenter)
            return container

        if item.type == DOCKER_TOGGLE_ITEM:
            docker_id = item.payload.get("docker_id", "")
            alias = self.alias_entry("dockers", docker_id)
            icon_path = self.resolve_icon_path(alias.get("icon_name"))
            has_icon = bool(icon_path)
            if has_icon:
                button = QPushButton()
                button.setFixedSize(self.cell_size, self.cell_size)
                button.setIcon(QIcon(icon_path))
                button.setIconSize(self.item_icon_size())
            else:
                button = QPushButton(alias.get("custom_name") or docker_id)
            button.setToolTip(alias.get("custom_name") or docker_id)
            button.clicked.connect(
                lambda checked=False, docker_id=docker_id: self.activate_docker_toggle(
                    docker_id
                )
            )
            self.apply_action_style(
                button, alias, has_icon, default_bg="#263a2f", default_fg="#ffffff"
            )
            return button

        if item.type == COLOR_ITEM:
            button = QPushButton()
            button.setFixedSize(self.cell_size, self.cell_size)
            color = item.payload.get("color", "#ffffff")
            button.setToolTip(color)
            button.setStyleSheet(
                f"QPushButton {{ background: {color}; border: {COLOR_SWATCH_BORDER_WIDTH}px solid {COLOR_SWATCH_BORDER_COLOR}; border-radius: 4px; }}"
            )
            button.clicked.connect(
                lambda checked=False, color=color: self.activate_color(color)
            )
            return button

        if item.type == SCRIPT_ITEM:
            button = QPushButton()
            button.setFixedSize(self.cell_size, self.cell_size)
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
            return button

        if item.type == BRUSH_SIZE_ITEM:
            button = QPushButton(item.payload.get("text", ""))
            button.setFixedSize(self.cell_size, self.cell_size)
            button.setToolTip(f"Set brush size to {item.payload.get('text', '')}")
            self.apply_brush_size_style(button, item)
            size_text = item.payload.get("text", "")
            button.clicked.connect(
                lambda checked=False, size_text=size_text: self.activate_brush_size(
                    size_text
                )
            )
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
            return button

        return QLabel(item.type)

    def apply_brush_icon(self, button, brush_name):
        try:
            preset = Krita.instance().resources("preset").get(brush_name)
            if self._set_brush_pixmap(button, preset):
                return
        except Exception as exc:
            print(f"Quick Access Palette popup brush icon error: {exc}")
        button.setText(brush_name[:1] if brush_name else "?")

    def activate_brush(self, brush_name):
        if not brush_name:
            return
        preset = Krita.instance().resources("preset").get(brush_name)
        window = Krita.instance().activeWindow()
        view = window.activeView() if window else None
        if preset and view:
            view.setCurrentBrushPreset(preset)
            self.close_after_execute()

    def trigger_action(self, action_id):
        if ActionManager.run_action(action_id):
            self.close_after_execute()

    def activate_docker_toggle(self, docker_id):
        if DockerManager and DockerManager.toggle_docker(docker_id):
            self.close_after_execute()

    def activate_color(self, color):
        window = Krita.instance().activeWindow()
        view = window.activeView() if window else None
        if not view:
            return
        managed_color = ManagedColor("RGBA", "U8", "")
        qcolor = QColor(color)
        managed_color.setComponents(
            [qcolor.blueF(), qcolor.greenF(), qcolor.redF(), 1.0]
        )
        view.setForeGroundColor(managed_color)
        self.close_after_execute()

    def activate_brush_size(self, size_text):
        window = Krita.instance().activeWindow()
        view = window.activeView() if window else None
        if not view or not size_text:
            return
        try:
            size = float(size_text)
        except ValueError:
            return
        view.setBrushSize(size)
        self.close_after_execute()

    def activate_brush_blend_mode(self, blend_mode):
        window = Krita.instance().activeWindow()
        view = window.activeView() if window else None
        if not view or not blend_mode:
            return
        try:
            view.setCurrentBlendingMode(blend_mode)
        except Exception:
            return
        self.close_after_execute()

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
            self.close_after_execute()
        except Exception as exc:
            QMessageBox.warning(self, "Script Error", f"Failed to run script:\n{exc}")

    def close_after_execute(self):
        if not self.is_pinned:
            self.close()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.is_pinned:
            self.close()
