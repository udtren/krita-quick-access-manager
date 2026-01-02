from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QShortcut,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QKeySequence
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
            print(f"Error setting up popup shortcut: {e}")

    def show_popup_at_cursor(self):
        """Show popup window at cursor position"""
        try:
            if self.popup_window and self.popup_window.isVisible():
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
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        popup_layout = QVBoxLayout()
        popup_layout.setContentsMargins(5, 5, 5, 5)
        popup_layout.setSpacing(2)

        # Add popup content - simplified brush grids
        self.create_popup_content(popup_layout)

        self.popup_window.setLayout(popup_layout)
        # Auto-fit content size
        self.popup_window.adjustSize()

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
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Display all grids
        for grid_info in self.parent_docker.grids:
            grid_name = grid_info.get("name", "Unnamed Grid")
            grid_label = QLabel(grid_name)
            grid_label.setFixedWidth(self.popup_loader.get_grid_label_width())
            grid_label.setWordWrap(True)
            grid_label.setAlignment(Qt.AlignCenter)
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
                grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

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
                            from PyQt5.QtGui import QPixmap, QIcon

                            pixmap = QPixmap.fromImage(icon)
                            if not pixmap.isNull():
                                # Scale the pixmap to fit the button
                                scaled_pixmap = pixmap.scaled(
                                    icon_size,
                                    icon_size,
                                    Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation,
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
        if self.popup_window:
            self.popup_window.hide()
