from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from krita import Krita, ManagedColor  # type: ignore

COLOR_HISTORY_BACKGROUND_COLOR = "#b0b0b0"


class ColorHistoryWidget(QWidget):
    """Widget to display color history in a grid"""

    def __init__(self, parent=None, color_history_number=20, icon_size=30):
        super().__init__(parent)
        self.COLOR_HISTORY_NUMBER = color_history_number
        self.ICON_SIZE = icon_size
        self.color_history = []
        self.color_buttons = []
        self.init_ui()

        # Timer to periodically check for color changes
        self.color_check_timer = QTimer()
        self.color_check_timer.timeout.connect(self.check_color_change)
        self.color_check_timer.start(200)  # Check every 200ms for better responsiveness

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Create 2 rows for color history
        colors_per_row = self.COLOR_HISTORY_NUMBER // 2
        button_size = self.ICON_SIZE

        # First row
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(1)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        # Second row
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(1)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        # Create color buttons
        for i in range(self.COLOR_HISTORY_NUMBER):
            color_btn = QPushButton()
            color_btn.setFixedSize(button_size, button_size)
            color_btn.setStyleSheet(
                f"border: 1px solid #888; border-radius: 4px; background-color: {COLOR_HISTORY_BACKGROUND_COLOR};"
            )
            color_btn.clicked.connect(lambda checked, idx=i: self.on_color_clicked(idx))
            self.color_buttons.append(color_btn)

            # Add to appropriate row
            if i < colors_per_row:
                row1_layout.addWidget(color_btn)
            else:
                row2_layout.addWidget(color_btn)

        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)
        self.setLayout(layout)

    def check_color_change(self):
        """Check if the current foreground color has changed"""
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                # Get current foreground color
                fg_color = view.foregroundColor()
                if fg_color:
                    # Get color components and convert to 0-255 range
                    components = fg_color.components()
                    if len(components) >= 3:
                        # Fix the component order - Krita might return BGR instead of RGB
                        color_rgb = (
                            int(components[2] * 255),  # Blue -> Red
                            int(components[1] * 255),  # Green -> Green
                            int(components[0] * 255),  # Red -> Blue
                        )

                        # Add to history if it's different from the last color
                        if not self.color_history or self.color_history[0] != color_rgb:
                            self.add_color_to_history(color_rgb)
            except Exception as e:
                # Try alternative method
                try:
                    fg_color = view.foregroundColor()
                    if fg_color:
                        # Try using colorProfile and colorSpace - also fix component order
                        color_rgb = (
                            int(fg_color.blue() * 255),  # Blue -> Red
                            int(fg_color.green() * 255),  # Green -> Green
                            int(fg_color.red() * 255),  # Red -> Blue
                        )

                        # Add to history if it's different from the last color
                        if not self.color_history or self.color_history[0] != color_rgb:
                            self.add_color_to_history(color_rgb)
                except Exception as e2:
                    print(f"Error getting foreground color: {e2}")
                    pass

    def add_color_to_history(self, color_rgb):
        """Add a color to the history and update display"""
        print(f"Adding color to history: RGB{color_rgb}")  # Debug output

        # Remove color if it already exists in history
        if color_rgb in self.color_history:
            self.color_history.remove(color_rgb)

        # Add to front of history
        self.color_history.insert(0, color_rgb)

        # Limit history size
        if len(self.color_history) > self.COLOR_HISTORY_NUMBER:
            self.color_history = self.color_history[: self.COLOR_HISTORY_NUMBER]

        # Update button colors
        self.update_color_buttons()
        print(f"Color history now has {len(self.color_history)} colors")  # Debug output

    def update_color_buttons(self):
        """Update the color buttons to show current history"""
        for i, btn in enumerate(self.color_buttons):
            if i < len(self.color_history):
                r, g, b = self.color_history[i]
                btn.setStyleSheet(
                    f"border: 1px solid #888; border-radius: 4px; background-color: rgb({r}, {g}, {b});"
                )
                btn.setToolTip(f"RGB({r}, {g}, {b})")
            else:
                btn.setStyleSheet(
                    f"border: 1px solid #888; border-radius: 4px; background-color: {COLOR_HISTORY_BACKGROUND_COLOR};"
                )
                btn.setToolTip("")

    def on_color_clicked(self, index):
        """Handle color button click to set foreground color"""
        if index < len(self.color_history):
            r, g, b = self.color_history[index]
            print(f"Clicking color: RGB({r}, {g}, {b})")  # Debug output

            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()

                try:
                    # Simple approach: Create ManagedColor and set RGB components directly
                    color = ManagedColor("RGBA", "U8", "")
                    # Set components in the correct order: Blue, Green, Red, Alpha (BGR order for Krita)
                    color.setComponents([b / 255.0, g / 255.0, r / 255.0, 1.0])
                    view.setForeGroundColor(color)
                    print(f"Successfully set foreground color to RGB({r}, {g}, {b})")

                except Exception as e:
                    print(f"Failed to set foreground color: {e}")
                    # Fallback: try with QColor
                    try:
                        color = ManagedColor("RGBA", "U8", "")
                        qcolor = QColor(r, g, b)
                        color.fromQColor(qcolor)
                        view.setForeGroundColor(color)
                        print(f"Successfully set color using QColor fallback")
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")

    def force_color_update(self):
        """Force an immediate color history update"""
        self.check_color_change()

    def add_test_color(self):
        """Add a test color to verify the widget is working"""
        import random

        test_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        self.add_color_to_history(test_color)
        print(f"Added test color: RGB{test_color}")

    def closeEvent(self, event):
        """Clean up timer when widget is closed"""
        if hasattr(self, "color_check_timer"):
            self.color_check_timer.stop()
        super().closeEvent(event)
