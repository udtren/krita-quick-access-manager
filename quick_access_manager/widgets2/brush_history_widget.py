from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor
from krita import Krita  # type: ignore

BRUSH_HISTORY_BACKGROUND_COLOR = "#b0b0b0"


class BrushHistoryWidget(QWidget):
    """Widget to display brush history in 2 rows"""

    def __init__(self, parent=None, brush_history_number=20, icon_size=30):
        super().__init__(parent)
        self.TOTAL_BRUSHES = brush_history_number  # Total number of brushes
        self.BRUSHES_PER_ROW = (
            brush_history_number // 2
        )  # Brushes per row (half of total)
        self.ICON_SIZE = icon_size
        self.brush_history = []
        self.brush_buttons = []
        self.init_ui()

        print(
            f"BrushHistoryWidget initialized with {self.BRUSHES_PER_ROW} brushes per row (2 rows, {self.TOTAL_BRUSHES} total), icon size: {icon_size}"
        )  # Debug output

        # Timer to periodically check for brush changes
        self.brush_check_timer = QTimer()
        self.brush_check_timer.timeout.connect(self.check_brush_change)
        self.brush_check_timer.start(500)  # Check every 500ms for better responsiveness

        # Force an immediate check to populate the current brush
        self.force_brush_update()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        button_size = self.ICON_SIZE

        # Create 2 rows for brush history
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(1)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(1)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        # Create brush buttons in 2 rows
        for i in range(self.TOTAL_BRUSHES):
            brush_btn = QPushButton()
            brush_btn.setFixedSize(button_size, button_size)
            brush_btn.setIconSize(
                QSize(button_size - 4, button_size - 4)
            )  # Icon slightly smaller than button
            brush_btn.setStyleSheet(
                f"border: 1px solid #888; border-radius: 4px; background-color: {BRUSH_HISTORY_BACKGROUND_COLOR};"
            )
            brush_btn.clicked.connect(lambda checked, idx=i: self.on_brush_clicked(idx))
            self.brush_buttons.append(brush_btn)

            # Add to appropriate row
            if i < self.BRUSHES_PER_ROW:
                row1_layout.addWidget(brush_btn)
            else:
                row2_layout.addWidget(brush_btn)

        row1_layout.addStretch()
        row2_layout.addStretch()
        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)
        layout.addStretch()
        self.setLayout(layout)

    def generate_brush_thumbnail(self, brush_preset, size=None):
        """Generate a thumbnail for the brush preset"""
        if size is None:
            size = self.ICON_SIZE - 4  # Use the configured icon size minus padding

        try:
            # Try to get the brush preset image/icon directly
            brush_image = brush_preset.image()
            if brush_image:
                # Convert Krita QImage to QPixmap
                pixmap = QPixmap.fromImage(brush_image)
                if not pixmap.isNull():
                    # Scale to desired size
                    scaled_pixmap = pixmap.scaled(
                        size, size, 1, 1
                    )  # Qt.KeepAspectRatio, Qt.SmoothTransformation
                    return QIcon(scaled_pixmap)

            # Fallback: create a simple icon with brush tip info
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(200, 200, 200))  # Light gray background

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw a simple brush representation
            brush_color = QColor(80, 80, 80)
            painter.setBrush(QBrush(brush_color))
            painter.setPen(brush_color)

            # Draw a circle representing the brush tip
            center = size // 2
            radius = size // 3
            painter.drawEllipse(
                center - radius, center - radius, radius * 2, radius * 2
            )

            painter.end()
            return QIcon(pixmap)

        except Exception as e:
            print(f"Error generating brush thumbnail: {e}")
            # Return a default icon
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(150, 150, 150))
            return QIcon(pixmap)

    def check_brush_change(self):
        """Check if the current brush preset has changed"""
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                current_preset = view.currentBrushPreset()
                if current_preset:
                    brush_name = current_preset.name()
                    print(f"Current brush detected: {brush_name}")  # Debug output

                    # Check if this brush is different from the last one in history
                    if not self.brush_history or self.brush_history[0][0] != brush_name:
                        print(
                            f"Brush changed, adding to history: {brush_name}"
                        )  # Debug output
                        self.add_brush_to_history(brush_name, current_preset)
                    else:
                        print(f"Same brush as last: {brush_name}")  # Debug output
            except Exception as e:
                print(f"Error getting current brush: {e}")
                import traceback

                traceback.print_exc()

    def add_brush_to_history(self, brush_name, brush_preset):
        """Add a brush to the history and update display"""
        print(f"Adding brush to history: {brush_name}")  # Debug output

        # Remove brush if it already exists in history
        for i, (name, preset) in enumerate(self.brush_history):
            if name == brush_name:
                print(
                    f"Removing existing brush from position {i}: {name}"
                )  # Debug output
                self.brush_history.pop(i)
                break

        # Add to front of history
        self.brush_history.insert(0, (brush_name, brush_preset))
        print(f"Added brush to front: {brush_name}")  # Debug output

        # Limit history size
        if len(self.brush_history) > self.TOTAL_BRUSHES:
            removed = self.brush_history[self.TOTAL_BRUSHES :]
            self.brush_history = self.brush_history[: self.TOTAL_BRUSHES]
            print(
                f"Trimmed history, removed: {[b[0] for b in removed]}"
            )  # Debug output

        # Update button display
        self.update_brush_buttons()
        print(
            f"Brush history now has {len(self.brush_history)} brushes: {[b[0] for b in self.brush_history]}"
        )  # Debug output

    def update_brush_buttons(self):
        """Update the brush buttons to show current history"""
        print(
            f"Updating brush buttons with {len(self.brush_history)} brushes"
        )  # Debug output
        for i, btn in enumerate(self.brush_buttons):
            if i < len(self.brush_history):
                brush_name, brush_preset = self.brush_history[i]

                # Generate and set thumbnail icon
                icon = self.generate_brush_thumbnail(brush_preset)
                btn.setIcon(icon)
                btn.setText("")  # Clear any text
                btn.setStyleSheet(
                    f"border: 1px solid #888; border-radius: 4px; background-color: {BRUSH_HISTORY_BACKGROUND_COLOR};"
                )
                btn.setToolTip(f"Brush: {brush_name}")
                print(f"Button {i}: {brush_name} (with thumbnail)")  # Debug output
            else:
                btn.setIcon(QIcon())  # Clear icon
                btn.setText("")
                btn.setStyleSheet(
                    f"border: 1px solid #888; border-radius: 4px; background-color: {BRUSH_HISTORY_BACKGROUND_COLOR};"
                )
                btn.setToolTip("")
                print(f"Button {i}: empty")  # Debug output

    def on_brush_clicked(self, index):
        """Handle brush button click to set brush preset"""
        if index < len(self.brush_history):
            brush_name, brush_preset = self.brush_history[index]
            print(f"Clicking brush: {brush_name}")  # Debug output

            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                try:
                    # Set the brush preset
                    view.setCurrentBrushPreset(brush_preset)

                    # Move this brush to front of history since it was used
                    self.add_brush_to_history(brush_name, brush_preset)

                    print(f"Successfully set brush to: {brush_name}")
                except Exception as e:
                    print(f"Error setting brush preset: {e}")

    def force_brush_update(self):
        """Force an immediate brush history update"""
        print("Force brush update called")  # Debug output
        self.check_brush_change()

    def add_test_brush(self):
        """Add a test brush to verify the widget is working"""
        print("Adding test brush")  # Debug output
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                current_preset = view.currentBrushPreset()
                if current_preset:
                    test_name = f"Test_{current_preset.name()}"
                    self.add_brush_to_history(test_name, current_preset)
                    print(f"Added test brush: {test_name}")
                else:
                    print("No current brush preset available")
            except Exception as e:
                print(f"Error adding test brush: {e}")
        else:
            print("No active window or view available")

    def closeEvent(self, event):
        """Clean up timer when widget is closed"""
        if hasattr(self, "brush_check_timer"):
            self.brush_check_timer.stop()
        super().closeEvent(event)
