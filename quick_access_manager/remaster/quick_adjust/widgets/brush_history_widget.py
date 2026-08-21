from krita import Krita  # type: ignore

from ...compat import (
    QApplication,
    QBrush,
    QColor,
    QEvent,
    QHBoxLayout,
    QIcon,
    QPainter,
    QPixmap,
    QPushButton,
    QSize,
    Qt,
    QVBoxLayout,
    QWidget,
)

BRUSH_HISTORY_BACKGROUND_COLOR = "#b0b0b0"


class BrushHistoryWidget(QWidget):
    """Widget to display brush history in 2 rows"""

    def __init__(self, parent=None, brush_history_number=20, icon_size=30):
        super().__init__(parent)
        self.TOTAL_BRUSHES = brush_history_number
        self.BRUSHES_PER_ROW = brush_history_number // 2
        self.ICON_SIZE = icon_size
        self.brush_history = []
        self.brush_buttons = []
        self.init_ui()
        self.install_event_filter()
        self.force_brush_update()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        button_size = self.ICON_SIZE

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(1)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(1)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        for i in range(self.TOTAL_BRUSHES):
            brush_btn = QPushButton()
            brush_btn.setFixedSize(button_size, button_size)
            brush_btn.setIconSize(QSize(button_size - 4, button_size - 4))
            brush_btn.setStyleSheet(
                f"border: 1px solid #888; border-radius: 4px; background-color: {BRUSH_HISTORY_BACKGROUND_COLOR};"
            )
            brush_btn.clicked.connect(lambda checked, idx=i: self.on_brush_clicked(idx))
            self.brush_buttons.append(brush_btn)

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

    def install_event_filter(self):
        self.set_filter_active(True)

    def set_filter_active(self, active):
        """Add/remove the application-wide mouse filter.

        This filter sees every click in Krita, so it is only installed while the
        docker is actually visible. closeEvent is not reliable for a docker
        child widget, which is why removal cannot depend on it alone.
        """
        if active == getattr(self, "_filter_installed", False):
            return
        try:
            app = QApplication.instance()
            if app is None:
                return
            if active:
                app.installEventFilter(self)
            else:
                app.removeEventFilter(self)
            self._filter_installed = active
        except Exception as e:
            print(f"Error updating event filter: {e}")

    def eventFilter(self, obj, event):
        if event.type() != QEvent.MouseButtonPress:
            return super().eventFilter(obj, event)
        if event.modifiers() == Qt.NoModifier:
            self.check_brush_change()
        return super().eventFilter(obj, event)

    def generate_brush_thumbnail(self, brush_preset, size=None):
        if size is None:
            size = self.ICON_SIZE - 4

        try:
            brush_image = brush_preset.image()
            if brush_image:
                pixmap = QPixmap.fromImage(brush_image)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(size, size, 1, 1)
                    return QIcon(scaled_pixmap)

            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(200, 200, 200))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            brush_color = QColor(80, 80, 80)
            painter.setBrush(QBrush(brush_color))
            painter.setPen(brush_color)

            center = size // 2
            radius = size // 3
            painter.drawEllipse(
                center - radius, center - radius, radius * 2, radius * 2
            )

            painter.end()
            return QIcon(pixmap)
        except Exception as e:
            print(f"Error generating brush thumbnail: {e}")
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor(150, 150, 150))
            return QIcon(pixmap)

    def check_brush_change(self):
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                current_preset = view.currentBrushPreset()
                if current_preset:
                    brush_name = current_preset.name()
                    if not self.brush_history or self.brush_history[0][0] != brush_name:
                        self.add_brush_to_history(brush_name, current_preset)
            except Exception:
                import traceback

                traceback.print_exc()

    def add_brush_to_history(self, brush_name, brush_preset):
        for i, (name, preset) in enumerate(self.brush_history):
            if name == brush_name:
                self.brush_history.pop(i)
                break

        self.brush_history.insert(0, (brush_name, brush_preset))

        if len(self.brush_history) > self.TOTAL_BRUSHES:
            self.brush_history = self.brush_history[: self.TOTAL_BRUSHES]

        self.update_brush_buttons()

    def update_brush_buttons(self):
        for i, btn in enumerate(self.brush_buttons):
            if i < len(self.brush_history):
                brush_name, brush_preset = self.brush_history[i]
                icon = self.generate_brush_thumbnail(brush_preset)
                btn.setIcon(icon)
                btn.setText("")
                btn.setStyleSheet(
                    f"border: 1px solid #888; border-radius: 4px; background-color: {BRUSH_HISTORY_BACKGROUND_COLOR};"
                )
                btn.setToolTip(f"Brush: {brush_name}")
            else:
                btn.setIcon(QIcon())
                btn.setText("")
                btn.setStyleSheet(
                    f"border: 1px solid #888; border-radius: 4px; background-color: {BRUSH_HISTORY_BACKGROUND_COLOR};"
                )
                btn.setToolTip("")

    def on_brush_clicked(self, index):
        if index < len(self.brush_history):
            brush_name, brush_preset = self.brush_history[index]
            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                try:
                    view.setCurrentBrushPreset(brush_preset)
                    self.add_brush_to_history(brush_name, brush_preset)
                except Exception as e:
                    print(f"Error setting brush preset: {e}")

    def force_brush_update(self):
        self.check_brush_change()

    def closeEvent(self, event):
        self.set_filter_active(False)
        super().closeEvent(event)
