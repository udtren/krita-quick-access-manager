from krita import Krita, ManagedColor
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QShortcut,
)
from PyQt5.QtGui import QColor, QFont, QIntValidator
from PyQt5.QtCore import Qt, QTimer

from .color_selector_dock import HueBar, SVBox, ChannelBar
from ..config.popup_loader import PopupConfigLoader


class ColorSelectorPopupWindow(QFrame):
    """Frameless popup window containing the full color selector UI."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # Internal color state
        self._h, self._s, self._v = 0, 255, 255
        color = QColor.fromHsv(0, 255, 255)
        self._r, self._g, self._b = color.red(), color.green(), color.blue()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(6)

        # ── Top: hue bar + SV box ──
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.hue_bar = HueBar()
        self.hue_bar.setMinimumHeight(150)
        self.sv_box = SVBox()
        self.sv_box.setMinimumSize(200, 150)

        top_layout.addWidget(self.hue_bar)
        top_layout.addWidget(self.sv_box, 1)
        outer_layout.addLayout(top_layout, 1)

        # ── Bottom: 6 channel bars ──
        self.channel_bars = {}
        self.channel_labels = {}

        font = QFont()
        font.setPointSize(10)

        channels_layout = QVBoxLayout()
        channels_layout.setSpacing(3)
        channels_layout.setContentsMargins(0, 0, 0, 0)
        channels_layout.setAlignment(Qt.AlignTop)

        for ch in ('H', 'S', 'V', 'R', 'G', 'B'):
            row = QHBoxLayout()
            row.setSpacing(4)

            bar = ChannelBar(ch)

            max_val = 359 if ch == 'H' else 255
            val_edit = QLineEdit("0")
            val_edit.setFixedWidth(42)
            val_edit.setAlignment(Qt.AlignRight)
            val_edit.setFont(font)
            val_edit.setValidator(QIntValidator(0, max_val))
            val_edit.editingFinished.connect(lambda c=ch: self._onChannelInput(c))

            up_btn = QPushButton("▲")
            down_btn = QPushButton("▼")
            for btn in (up_btn, down_btn):
                btn.setFixedSize(18, 13)
                btn.setStyleSheet("QPushButton { padding: 0; font-size: 8px; }")
            up_btn.clicked.connect(lambda _, c=ch: self._stepChannel(c, 1))
            down_btn.clicked.connect(lambda _, c=ch: self._stepChannel(c, -1))

            arrow_layout = QVBoxLayout()
            arrow_layout.setSpacing(1)
            arrow_layout.setContentsMargins(0, 0, 0, 0)
            arrow_layout.addWidget(up_btn)
            arrow_layout.addWidget(down_btn)

            row.addWidget(bar, 1)
            row.addLayout(arrow_layout)
            row.addWidget(val_edit)
            channels_layout.addLayout(row)

            self.channel_bars[ch] = bar
            self.channel_labels[ch] = val_edit
            bar.valueChanged.connect(lambda val, c=ch: self._onChannelChanged(c, val, debounce=True))

        outer_layout.addLayout(channels_layout)

        # Connect top picker signals
        self.hue_bar.hueChanged.connect(self._onHueBarChanged)
        self.sv_box.colorChanged.connect(self._onSVChanged)

        # Poll Krita foreground color every second
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._pollKritaColor)

        # Debounce timer for bar dragging
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._applyPendingColor)

        self._updateChannelBars()
        self.adjustSize()

    # ── Visibility ───────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self._pollKritaColor()   # sync to current Krita color on open
        self._poll_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._poll_timer.stop()
        self._debounce_timer.stop()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hide()

    # ── Sync helpers ─────────────────────────────────────────────

    def _updateChannelBars(self):
        for bar in self.channel_bars.values():
            bar.setColor(self._h, self._s, self._v, self._r, self._g, self._b)
        self.channel_labels['H'].setText(str(self._h))
        self.channel_labels['S'].setText(str(self._s))
        self.channel_labels['V'].setText(str(self._v))
        self.channel_labels['R'].setText(str(self._r))
        self.channel_labels['G'].setText(str(self._g))
        self.channel_labels['B'].setText(str(self._b))

    def _applyHSV(self, h, s, v, push=True):
        self._h, self._s, self._v = h, s, v
        color = QColor.fromHsv(h, s, v)
        self._r, self._g, self._b = color.red(), color.green(), color.blue()

        self.hue_bar.setHue(h)
        self.sv_box.setHue(h)
        self.sv_box.setSatVal(s, v)
        self._updateChannelBars()
        if push:
            self._setKritaForeground(color)
            self._poll_timer.start()

    def _pollKritaColor(self):
        app = Krita.instance()
        if not app.activeWindow():
            return
        view = app.activeWindow().activeView()
        if not view:
            return
        mc = view.foregroundColor()
        if not mc:
            return
        qcolor = mc.colorForCanvas(app.activeWindow().activeView().canvas())
        if not qcolor or not qcolor.isValid():
            return

        r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
        if (r, g, b) == (self._r, self._g, self._b):
            return

        color = QColor(r, g, b)
        h = color.hsvHue() if color.hsvHue() != -1 else self._h
        s, v = color.hsvSaturation(), color.value()
        self._applyHSV(h, s, v, push=False)

    # ── Signal handlers ──────────────────────────────────────────

    def _onHueBarChanged(self, hue):
        self._applyHSV(hue, self._s, self._v)

    def _onSVChanged(self, qcolor):
        h = qcolor.hsvHue() if qcolor.hsvHue() != -1 else self._h
        self._applyHSV(h, qcolor.hsvSaturation(), qcolor.value())

    def _onChannelChanged(self, channel, value, debounce=False):
        h, s, v = self._h, self._s, self._v
        r, g, b = self._r, self._g, self._b

        if channel == 'H':
            h = value
        elif channel == 'S':
            s = value
        elif channel == 'V':
            v = value
        elif channel == 'R':
            r = value
            c = QColor(r, g, b)
            h = c.hsvHue() if c.hsvHue() != -1 else self._h
            s, v = c.hsvSaturation(), c.value()
        elif channel == 'G':
            g = value
            c = QColor(r, g, b)
            h = c.hsvHue() if c.hsvHue() != -1 else self._h
            s, v = c.hsvSaturation(), c.value()
        elif channel == 'B':
            b = value
            c = QColor(r, g, b)
            h = c.hsvHue() if c.hsvHue() != -1 else self._h
            s, v = c.hsvSaturation(), c.value()

        if debounce:
            self._poll_timer.stop()
            self._applyHSV(h, s, v, push=False)
            self._debounce_timer.start()
        else:
            self._applyHSV(h, s, v)

    def _applyPendingColor(self):
        self._setKritaForeground(QColor.fromHsv(self._h, self._s, self._v))
        self._poll_timer.start()

    def _stepChannel(self, ch, delta):
        current = {'H': self._h, 'S': self._s, 'V': self._v,
                   'R': self._r, 'G': self._g, 'B': self._b}[ch]
        max_val = 359 if ch == 'H' else 255
        self._onChannelChanged(ch, max(0, min(max_val, current + delta)))

    def _onChannelInput(self, ch):
        text = self.channel_labels[ch].text()
        try:
            val = int(text)
        except ValueError:
            self._updateChannelBars()
            return
        max_val = 359 if ch == 'H' else 255
        self._onChannelChanged(ch, max(0, min(max_val, val)))

    def _setKritaForeground(self, qcolor):
        app = Krita.instance()
        view = app.activeWindow().activeView() if app.activeWindow() else None
        if not view:
            return
        doc = app.activeDocument()
        if not doc:
            return
        mc = ManagedColor("RGBA", "U8", "")
        components = mc.components()
        components[0] = qcolor.blueF()
        components[1] = qcolor.greenF()
        components[2] = qcolor.redF()
        components[3] = 1.0
        mc.setComponents(components)
        view.setForeGroundColor(mc)


class ColorSelectorPopup:
    """Manages the color selector popup lifecycle and shortcut registration."""

    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
        self.popup_window = None
        self.popup_shortcut = None
        self.popup_loader = PopupConfigLoader()

    def setup_popup_shortcut(self):
        """Register the global shortcut to open/close the popup."""
        try:
            app = Krita.instance()
            main_window = app.activeWindow().qwindow() if app.activeWindow() else self.parent_docker

            shortcut_key = self.popup_loader.get_color_selector_popup_shortcut()
            self.popup_shortcut = QShortcut(shortcut_key, main_window)
            self.popup_shortcut.activated.connect(self.show_popup_at_cursor)
            self.popup_shortcut.setContext(Qt.ApplicationShortcut)
        except Exception as e:
            print(f"Error setting up color selector popup shortcut: {e}")

    def show_popup_at_cursor(self):
        """Toggle the popup at the current cursor position."""
        try:
            from PyQt5.QtGui import QCursor

            if self.popup_window and self.popup_window.isVisible():
                self.popup_window.hide()
                return

            if self.popup_window is None:
                self.popup_window = ColorSelectorPopupWindow()

            self.popup_window.adjustSize()
            w = self.popup_window.width()
            h = self.popup_window.height()
            cursor_pos = QCursor.pos()
            self.popup_window.move(
                cursor_pos.x() - w // 2,
                cursor_pos.y() - h // 2,
            )
            self.popup_window.show()
            self.popup_window.raise_()
        except Exception:
            import traceback
            traceback.print_exc()
