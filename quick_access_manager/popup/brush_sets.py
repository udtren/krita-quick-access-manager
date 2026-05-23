from ..compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QShortcut, QFrame, QTabWidget,
    Qt,
    QCursor, QIcon,
)
from krita import Krita  # type: ignore
from ..config.popup_loader import PopupConfigLoader
from ..utils.config_utils import get_plugin_dir 


class BrushSetsPopup:
    """Handles the popup functionality for brush sets"""

    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
        self.popup_window = None
        self.popup_shortcut = None
        self.popup_loader = PopupConfigLoader()
        self.is_pinned = False
        self.drag_position = None
        self.pin_button = None

    def setup_popup_shortcut(self):
        """Setup shortcut for popup functionality"""
        try:
            # Try to register shortcut with the main window for global access
            main_window = None
            app = Krita.instance()
            if app.activeWindow():
                main_window = app.activeWindow().qwindow()

            # If we can't get the main window, use parent docker as parent
            parent = main_window if main_window else self.parent_docker

            # Get shortcut from config
            shortcut_key = self.popup_loader.get_brush_sets_popup_shortcut()
            self.popup_shortcut = QShortcut(shortcut_key, parent)
            self.popup_shortcut.activated.connect(self.show_popup_at_cursor)

            # Enable the shortcut for application-wide use
            self.popup_shortcut.setContext(Qt.ApplicationShortcut)

        except Exception as e:
            # print(f"Error setting up popup shortcut: {e}")

    def show_popup_at_cursor(self):
        """Show popup window at cursor position"""
        try:
            if self.popup_window and self.popup_window.isVisible():
                if not self.is_pinned:
                    self.popup_window.hide()
                return

            self.create_popup_window()

            # Get size after adjustSize()
            popup_width = self.popup_window.width()
            popup_height = self.popup_window.height()

            # Position at cursor (centered)
            cursor_pos = QCursor.pos()
            self.popup_window.move(
                cursor_pos.x() - popup_width // 2, cursor_pos.y() - popup_height // 3
            )
            self.popup_window.show()
            self.popup_window.raise_()

        except Exception:
            import traceback

            traceback.print_exc()

    def create_popup_window(self):
        """Create the popup window with brush grid content"""
        self.popup_window = QFrame()
        self.popup_window.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        # Override mouse events for dragging
        self.popup_window.mousePressEvent = self.popup_mouse_press
        self.popup_window.mouseMoveEvent = self.popup_mouse_move
        self.popup_window.mouseReleaseEvent = self.popup_mouse_release

        popup_layout = QVBoxLayout()
        popup_layout.setContentsMargins(5, 5, 5, 5)
        popup_layout.setSpacing(2)

        # Add toolbar at the top
        self.create_toolbar(popup_layout)

        # Add popup content - simplified brush grids
        self.create_popup_content(popup_layout)

        self.popup_window.setLayout(popup_layout)
        # Auto-fit content size
        self.popup_window.adjustSize()

    def create_toolbar(self, popup_layout):
        """Create toolbar with pin and close buttons"""
        import os

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 5)
        toolbar_layout.setSpacing(5)

        # Get the base path for icons
        close_icon = os.path.join(
            get_plugin_dir(), "config", "system_icon", "circle-xmark.png"
        )

        # Pin button
        self.pin_button = QPushButton()
        self.pin_button.setFixedSize(16, 16)
        self.pin_button.setToolTip("Pin window")
        self.pin_button.clicked.connect(self.toggle_pin)
        self.update_pin_icon()
        self.pin_button.setStyleSheet(
            """
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #6a6a6a;
            }
        """
        )

        # Close button
        close_button = QPushButton()
        close_button.setFixedSize(16, 16)
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.close_popup)
        if os.path.exists(close_icon):
            close_button.setIcon(QIcon(close_icon))
            close_button.setIconSize(close_button.size())
        else:
            close_button.setText("X")
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #828282;
                border: none;
                border-radius: 2px;
                color: #fff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9a9a9a;
            }
            QPushButton:pressed {
                background-color: #6a6a6a;
            }
        """
        )

        # Add buttons to toolbar (align right)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.pin_button)
        toolbar_layout.addWidget(close_button)

        popup_layout.addLayout(toolbar_layout)

    def update_pin_icon(self):
        """Update pin button icon based on pin status"""
        import os

        system_icon_dir = os.path.join(get_plugin_dir(), "config", "system_icon")

        if self.is_pinned:
            pin_icon = os.path.join(system_icon_dir, "pin_pinned.png")
            tooltip = "Unpin window"
        else:
            pin_icon = os.path.join(system_icon_dir, "pin_unpinned.png")
            tooltip = "Pin window"

        if self.pin_button and os.path.exists(pin_icon):
            self.pin_button.setIcon(QIcon(pin_icon))
            self.pin_button.setIconSize(self.pin_button.size())
            self.pin_button.setToolTip(tooltip)

    def toggle_pin(self):
        """Toggle pin status"""
        self.is_pinned = not self.is_pinned
        self.update_pin_icon()

    def close_popup(self):
        """Close popup and reset pin status"""
        self.is_pinned = False
        if self.popup_window:
            self.popup_window.hide()

    def popup_mouse_press(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPos() - self.popup_window.frameGeometry().topLeft()
            )
            event.accept()

    def popup_mouse_move(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.popup_window.move(event.globalPos() - self.drag_position)
            event.accept()

    def popup_mouse_release(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            event.accept()

    def create_popup_content(self, popup_layout):
        """Create brush grid content organised by tab."""
        tabs = self.parent_docker.tabs
        if not tabs or not any(tab["grids"] for tab in tabs):
            no_grids_label = QLabel("No brush grids available")
            no_grids_label.setStyleSheet("color: #999; font-style: italic;")
            popup_layout.addWidget(no_grids_label)
            return

        tab_widget = QTabWidget()
        for tab_info in tabs:
            tab_page = self._build_tab_page(tab_info)
            tab_widget.addTab(tab_page, tab_info["name"])

        popup_layout.addWidget(tab_widget)

    def _build_tab_page(self, tab_info):
        """Build the grid content widget for one popup tab."""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        if not tab_info["grids"]:
            empty = QLabel("No grids in this tab")
            empty.setStyleSheet("color: #999; font-style: italic;")
            layout.addWidget(empty)
            page.setLayout(layout)
            return page

        for grid_info in tab_info["grids"]:
            grid_name = grid_info.get("name", "Unnamed Grid")
            grid_label = QLabel(grid_name)
            grid_label.setFixedWidth(self.popup_loader.get_grid_label_width())
            grid_label.setWordWrap(True)
            grid_label.setAlignment(Qt.AlignCenter)
            grid_label.setStyleSheet(
                "color: #000000; background-color: #919191; border-radius: 4px;"
                " font-weight: bold; font-size: 12px;"
            )

            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            row_layout.addWidget(grid_label)

            if grid_info.get("brush_presets"):
                grid_widget = QWidget()
                grid_layout = QGridLayout()
                grid_layout.setSpacing(1)
                grid_layout.setContentsMargins(0, 0, 0, 0)
                grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                columns = self.parent_docker.get_dynamic_columns()

                for index, preset in enumerate(grid_info["brush_presets"]):
                    brush_btn = self._build_brush_button(preset)
                    grid_layout.addWidget(brush_btn, index // columns, index % columns)

                grid_widget.setLayout(grid_layout)
                row_layout.addWidget(grid_widget)
            else:
                empty_label = QLabel("  (empty)")
                empty_label.setStyleSheet(
                    "color: #666; font-style: italic; font-size: 10px; margin-left: 10px;"
                )
                row_layout.addWidget(empty_label)

            row_layout.addStretch()
            layout.addLayout(row_layout)

        page.setLayout(layout)
        return page

    def _build_brush_button(self, preset):
        """Build a single brush icon button for the popup."""
        from ..compat import QPixmap
        icon_size = self.popup_loader.get_brush_icon_size()
        btn = QPushButton()
        btn.setFixedSize(icon_size, icon_size)
        btn.setToolTip(preset.name())
        btn.clicked.connect(lambda _, p=preset: self.select_brush_preset_and_close(p))

        try:
            img = preset.image()
            if not img or img.isNull():
                raise ValueError
            pixmap = QPixmap.fromImage(img)
            if pixmap.isNull():
                raise ValueError
            scaled = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            btn.setIcon(QIcon(scaled))
            btn.setIconSize(scaled.size())
            btn.setStyleSheet(
                "QPushButton { border: 1px solid #555; background-color: #3d3d3d;"
                " border-radius: 8px; padding: 2px; }"
                " QPushButton:hover { border: 2px solid #0078d4; background-color: #4d4d4d; }"
                " QPushButton:pressed { background-color: #0078d4; }"
            )
        except Exception:
            btn.setText(preset.name()[:2].upper())
            btn.setStyleSheet(
                "QPushButton { border: 1px solid #555; background-color: #3d3d3d;"
                " border-radius: 3px; color: #fff; font-weight: bold; font-size: 10px; }"
                " QPushButton:hover { border: 2px solid #0078d4; background-color: #4d4d4d; }"
            )
        return btn

    def select_brush_preset_and_close(self, preset):
        """Select brush preset and close popup"""
        self.parent_docker.select_brush_preset(preset)
        if self.popup_window and not self.is_pinned:
            self.popup_window.hide()
