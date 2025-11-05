from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QShortcut,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QKeySequence
from krita import Krita  # type: ignore

BrushSetsPopupShortcut = QKeySequence(Qt.Key_W)
BrushIconSize = 46


class BrushSetsPopup:
    """Handles the popup functionality for brush sets"""

    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
        self.popup_window = None
        self.popup_shortcut = None

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

            self.popup_shortcut = QShortcut(BrushSetsPopupShortcut, parent)
            self.popup_shortcut.activated.connect(self.show_popup_at_cursor)

            # Enable the shortcut for application-wide use
            self.popup_shortcut.setContext(Qt.ApplicationShortcut)

        except Exception as e:
            print(f"Error setting up popup shortcut: {e}")

    def show_popup_at_cursor(self):
        """Show popup window at cursor position"""
        print("Popup shortcut activated!")  # Debug message
        try:
            if self.popup_window and self.popup_window.isVisible():
                print("Hiding existing popup")
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

            # Auto-hide after 10 seconds (optional)
            QTimer.singleShot(10000, self.popup_window.hide)

        except Exception as e:
            print(f"Error showing popup: {e}")
            import traceback

            traceback.print_exc()

    def create_popup_window(self):
        """Create the popup window with brush grid content"""
        self.popup_window = QFrame()
        self.popup_window.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.popup_window.setStyleSheet(
            """
            QFrame {
                border: 2px solid #0078d4;
                background-color: #2d2d2d;
                border-radius: 5px;
            }
        """
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
            # Create grid for brushes (removed grid header label)
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
                    icon_size = BrushIconSize
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
                                print(f"Successfully set icon for {preset.name()}")
                            else:
                                print(f"Failed to create pixmap for {preset.name()}")
                                raise Exception("Null pixmap")
                        else:
                            print(f"No image available for {preset.name()}")
                            raise Exception("No image")
                    except Exception as e:
                        print(f"Error loading brush icon for {preset.name()}: {e}")
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
                            border-radius: 3px;
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
                main_layout.addWidget(grid_widget)
            else:
                # Empty grid message
                empty_label = QLabel("  (empty)")
                empty_label.setStyleSheet(
                    "color: #666; font-style: italic; font-size: 10px; margin-left: 10px;"
                )
                main_layout.addWidget(empty_label)

        main_widget.setLayout(main_layout)
        popup_layout.addWidget(main_widget)

    def select_brush_preset_and_close(self, preset):
        """Select brush preset and close popup"""
        self.parent_docker.select_brush_preset(preset)
        if self.popup_window:
            self.popup_window.hide()
