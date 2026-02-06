from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor, QKeySequence, QIcon, QPixmap, QShortcut
from krita import Krita  # type: ignore
from ..utils.logs import write_log
from ..config.popup_loader import PopupConfigLoader


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
            self.popup_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)

        except Exception as e:
            print(f"Error setting up popup shortcut: {e}")

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

        except Exception as e:
            import traceback

            traceback.print_exc()

    def create_popup_window(self):
        """Create the popup window with brush grid content"""
        self.popup_window = QFrame()
        self.popup_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
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
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        close_icon = os.path.join(
            base_path, "config", "system_icon", "circle-xmark.png"
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

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if self.is_pinned:
            pin_icon = os.path.join(
                base_path, "config", "system_icon", "pin_pinned.png"
            )
            tooltip = "Unpin window"
        else:
            pin_icon = os.path.join(
                base_path, "config", "system_icon", "pin_unpinned.png"
            )
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
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.popup_window.frameGeometry().topLeft()
            )
            event.accept()

    def popup_mouse_move(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.popup_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def popup_mouse_release(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            event.accept()

    def create_popup_content(self, popup_layout):
        """Create simplified brush grid content for popup"""
        if not self.parent_docker.grids:
            no_grids_label = QLabel("No brush grids available")
            no_grids_label.setStyleSheet("color: #999; font-style: italic;")
            popup_layout.addWidget(no_grids_label)
            return

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Display all grids
        for grid_info in self.parent_docker.grids:
            grid_name = grid_info.get("name", "Unnamed Grid")
            grid_label = QLabel(grid_name)
            grid_label.setFixedWidth(self.popup_loader.get_grid_label_width())
            grid_label.setWordWrap(True)
            grid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_label.setStyleSheet(
                """
                color: #000000;
                background-color: #919191;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                """
            )

            grid_name_preset_layout = QHBoxLayout()
            grid_name_preset_layout.setContentsMargins(0, 0, 0, 0)
            grid_name_preset_layout.setSpacing(5)
            grid_name_preset_layout.addWidget(grid_label)

            if grid_info.get("brush_presets"):
                grid_widget = QWidget()
                grid_layout = QGridLayout()
                grid_layout.setSpacing(1)
                grid_layout.setContentsMargins(0, 0, 0, 0)

                # Set alignment to left
                grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

                columns = self.parent_docker.get_dynamic_columns()

                for index, preset in enumerate(grid_info["brush_presets"]):
                    row = index // columns
                    col = index % columns

                    # Create brush button with icon
                    brush_btn = QPushButton()
                    icon_size = self.popup_loader.get_brush_icon_size()
                    brush_btn.setFixedSize(icon_size, icon_size)
                    brush_btn.setToolTip(preset.name())
                    brush_btn.clicked.connect(
                        lambda checked, p=preset: self.select_brush_preset_and_close(p)
                    )

                    # Set brush icon
                    try:
                        # Try to get the brush icon/thumbnail
                        icon = preset.image()
                        if icon and not icon.isNull():
                            # Convert QImage to QPixmap and then to QIcon
                            from PyQt6.QtGui import QPixmap, QIcon

                            pixmap = QPixmap.fromImage(icon)
                            if not pixmap.isNull():
                                # Scale the pixmap to fit the button
                                scaled_pixmap = pixmap.scaled(
                                    icon_size,
                                    icon_size,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation,
                                )
                                brush_btn.setIcon(QIcon(scaled_pixmap))
                                brush_btn.setIconSize(scaled_pixmap.size())
                            else:
                                raise Exception("Null pixmap")
                        else:
                            raise Exception("No image")
                    except Exception as e:
                        # Fallback: use first 2 characters
                        brush_btn.setText(preset.name()[:2].upper())
                        brush_btn.setStyleSheet(
                            """
                            QPushButton {
                                border: 1px solid #555;
                                background-color: #3d3d3d;
                                border-radius: 3px;
                                color: #fff;
                                font-weight: bold;
                                font-size: 10px;
                            }
                            QPushButton:hover {
                                border: 2px solid #0078d4;
                                background-color: #4d4d4d;
                            }
                        """
                        )
                        grid_layout.addWidget(brush_btn, row, col)
                        continue

                    brush_btn.setStyleSheet(
                        """
                        QPushButton {
                            border: 1px solid #555;
                            background-color: #3d3d3d;
                            border-radius: 8px;
                            padding: 2px;
                        }
                        QPushButton:hover {
                            border: 2px solid #0078d4;
                            background-color: #4d4d4d;
                        }
                        QPushButton:pressed {
                            background-color: #0078d4;
                        }
                    """
                    )

                    grid_layout.addWidget(brush_btn, row, col)
                grid_widget.setLayout(grid_layout)
            else:
                # Empty grid message
                empty_label = QLabel("  (empty)")
                empty_label.setStyleSheet(
                    "color: #666; font-style: italic; font-size: 10px; margin-left: 10px;"
                )
                main_layout.addWidget(empty_label)
            grid_name_preset_layout.addWidget(grid_widget)
            grid_name_preset_layout.addStretch()
            main_layout.addLayout(grid_name_preset_layout)

        main_widget.setLayout(main_layout)
        popup_layout.addWidget(main_widget)

    def select_brush_preset_and_close(self, preset):
        """Select brush preset and close popup"""
        self.parent_docker.select_brush_preset(preset)
        if self.popup_window and not self.is_pinned:
            self.popup_window.hide()
