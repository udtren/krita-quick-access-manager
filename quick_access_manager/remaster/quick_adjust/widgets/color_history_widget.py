from krita import Krita, ManagedColor  # type: ignore

from ...compat import (
    QApplication,
    QColor,
    QEvent,
    QHBoxLayout,
    QPushButton,
    Qt,
    QVBoxLayout,
    QWidget,
)

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
        self.install_event_filter()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        colors_per_row = self.COLOR_HISTORY_NUMBER // 2
        button_size = self.ICON_SIZE

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(1)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(1)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        for i in range(self.COLOR_HISTORY_NUMBER):
            color_btn = QPushButton()
            color_btn.setFixedSize(button_size, button_size)
            color_btn.setStyleSheet(
                f"border: 1px solid #888; border-radius: 4px; background-color: {COLOR_HISTORY_BACKGROUND_COLOR};"
            )
            color_btn.clicked.connect(lambda checked, idx=i: self.on_color_clicked(idx))
            self.color_buttons.append(color_btn)

            if i < colors_per_row:
                row1_layout.addWidget(color_btn)
            else:
                row2_layout.addWidget(color_btn)

        row1_layout.addStretch()
        row2_layout.addStretch()
        layout.addLayout(row1_layout)
        layout.addLayout(row2_layout)
        layout.addStretch()
        self.setLayout(layout)

    def install_event_filter(self):
        try:
            app = QApplication.instance()
            if app:
                app.installEventFilter(self)
        except Exception as e:
            print(f"Error installing event filter: {e}")

    def eventFilter(self, obj, event):
        if event.type() != QEvent.MouseButtonPress:
            return super().eventFilter(obj, event)
        if event.modifiers() == Qt.NoModifier:
            self.check_color_change()
        return super().eventFilter(obj, event)

    def check_color_change(self):
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            view = app.activeWindow().activeView()
            try:
                fg_color = view.foregroundColor()
                if fg_color:
                    components = fg_color.components()
                    if len(components) >= 3:
                        color_rgb = (
                            int(components[2] * 255),
                            int(components[1] * 255),
                            int(components[0] * 255),
                        )
                        if not self.color_history or self.color_history[0] != color_rgb:
                            self.add_color_to_history(color_rgb)
            except Exception:
                try:
                    fg_color = view.foregroundColor()
                    if fg_color:
                        color_rgb = (
                            int(fg_color.blue() * 255),
                            int(fg_color.green() * 255),
                            int(fg_color.red() * 255),
                        )
                        if not self.color_history or self.color_history[0] != color_rgb:
                            self.add_color_to_history(color_rgb)
                except Exception as e2:
                    print(f"Error getting foreground color: {e2}")

    def add_color_to_history(self, color_rgb):
        if color_rgb in self.color_history:
            self.color_history.remove(color_rgb)
        self.color_history.insert(0, color_rgb)
        if len(self.color_history) > self.COLOR_HISTORY_NUMBER:
            self.color_history = self.color_history[: self.COLOR_HISTORY_NUMBER]
        self.update_color_buttons()

    def update_color_buttons(self):
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
        if index < len(self.color_history):
            r, g, b = self.color_history[index]
            app = Krita.instance()
            if app.activeWindow() and app.activeWindow().activeView():
                view = app.activeWindow().activeView()
                try:
                    color = ManagedColor("RGBA", "U8", "")
                    color.setComponents([b / 255.0, g / 255.0, r / 255.0, 1.0])
                    view.setForeGroundColor(color)
                except Exception:
                    try:
                        color = ManagedColor("RGBA", "U8", "")
                        qcolor = QColor(r, g, b)
                        color.fromQColor(qcolor)
                        view.setForeGroundColor(color)
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")

    def force_color_update(self):
        self.check_color_change()

    def add_test_color(self):
        import random

        test_color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        self.add_color_to_history(test_color)

    def closeEvent(self, event):
        try:
            app = QApplication.instance()
            if app:
                app.removeEventFilter(self)
        except Exception as e:
            print(f"Error removing event filter: {e}")
        super().closeEvent(event)
