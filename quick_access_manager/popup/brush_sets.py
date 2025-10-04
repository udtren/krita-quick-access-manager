from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QHBoxLayout,
    QShortcut,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QKeySequence
from krita import Krita  # type: ignore
from ..utils.config_utils import get_brush_icon_size

BrushSetsPopupShortcut = QKeySequence(Qt.Key_W)
BrushIconSize = 32


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

            print(
                f"Popup shortcut registered successfully with parent: {type(parent).__name__}"
            )
            print(f"Shortcut key sequence: {self.popup_shortcut.key().toString()}")

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

            print("Creating/showing popup window")
            # Always recreate popup window to reflect current parent content
            self.create_popup_window()

            # Position at cursor
            cursor_pos = QCursor.pos()
            print(f"Cursor position: {cursor_pos.x()}, {cursor_pos.y()}")
            self.popup_window.move(cursor_pos.x() + 10, cursor_pos.y() + 10)
            self.popup_window.show()
            self.popup_window.raise_()

            # Auto-hide after 10 seconds (optional)
            QTimer.singleShot(10000, self.popup_window.hide)
            print("Popup window shown successfully")

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

        # # Add close button
        # header_layout = QHBoxLayout()
        # close_btn = QPushButton("✕")
        # close_btn.setFixedSize(20, 20)
        # close_btn.clicked.connect(self.popup_window.hide)
        # close_btn.setStyleSheet(
        #     """
        #     QPushButton {
        #         border: none;
        #         color: white;
        #         font-weight: bold;
        #         background-color: #ff4444;
        #         border-radius: 10px;
        #     }
        #     QPushButton:hover {
        #         background-color: #ff6666;
        #     }
        # """
        # )

        # header_layout.addStretch()
        # header_layout.addWidget(close_btn)
        # popup_layout.addLayout(header_layout)

        # Add popup content - simplified brush grids
        self.create_popup_content(popup_layout)

        self.popup_window.setLayout(popup_layout)
        # Auto-fit content size
        self.popup_window.adjustSize()
        # Set reasonable minimum and maximum sizes
        # self.popup_window.setMinimumSize(200, 150)
        # self.popup_window.setMaximumSize(600, 700)

    def create_popup_content(self, popup_layout):
        """Create simplified brush grid content for popup"""
        if not self.parent_docker.grids:
            no_grids_label = QLabel("No brush grids available")
            no_grids_label.setStyleSheet("color: #999; font-style: italic;")
            popup_layout.addWidget(no_grids_label)
            return

        # Create a scroll area for all grids
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #555;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #888;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #aaa;
            }
        """
        )

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(2, 2, 2, 2)

        # Display all grids
        for grid_info in self.parent_docker.grids:
            # Create grid for brushes (removed grid header label)
            if grid_info.get("brush_presets"):
                grid_widget = QWidget()
                grid_layout = QGridLayout()
                grid_layout.setSpacing(1)
                grid_layout.setContentsMargins(0, 0, 0, 0)

                columns = self.parent_docker.get_dynamic_columns()

                for index, preset in enumerate(grid_info["brush_presets"]):
                    row = index // columns
                    col = index % columns

                    # Create brush button with icon
                    brush_btn = QPushButton()
                    icon_size = max(
                        BrushIconSize, get_brush_icon_size() - 1
                    )  # Slightly smaller for popup
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
                scroll_layout.addWidget(grid_widget)
            else:
                # Empty grid message
                empty_label = QLabel("  (empty)")
                empty_label.setStyleSheet(
                    "color: #666; font-style: italic; font-size: 10px; margin-left: 10px;"
                )
                scroll_layout.addWidget(empty_label)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        popup_layout.addWidget(scroll_area)

    def select_brush_preset_and_close(self, preset):
        """Select brush preset and close popup"""
        self.parent_docker.select_brush_preset(preset)
        if self.popup_window:
            self.popup_window.hide()
