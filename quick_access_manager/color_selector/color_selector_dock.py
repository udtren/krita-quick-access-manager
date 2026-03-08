from krita import DockWidget, Krita, ManagedColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QFont, QIntValidator
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QTimer
from ..config.popup_loader import PopupConfigLoader


class HueBar(QWidget):
    """Vertical hue bar — full spectrum top to bottom."""
    hueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(30)
        self.setMinimumHeight(100)
        self._hue = 0
        self._pressed = False

    def hue(self):
        return self._hue

    def setHue(self, h):
        self._hue = max(0, min(359, h))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        # Draw hue spectrum via gradient (6 primary hue stops)
        grad = QLinearGradient(0, 0, 0, h)
        for i in range(7):
            grad.setColorAt(i / 6, QColor.fromHsv(int(i * 360 / 6) % 360, 255, 255))
        painter.fillRect(0, 0, w, h, grad)

        # Draw marker
        marker_y = int((self._hue / 360.0) * h)
        painter.setPen(Qt.white)
        painter.drawRect(0, marker_y - 2, w - 1, 4)
        painter.setPen(Qt.black)
        painter.drawRect(1, marker_y - 1, w - 3, 2)
        painter.end()

    def _pick(self, pos):
        h = self.height()
        y = max(0, min(pos.y(), h - 1))
        self._hue = int((y / h) * 360) % 360
        self.update()
        self.hueChanged.emit(self._hue)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._pick(event.pos())

    def mouseReleaseEvent(self, event):
        self._pressed = False


class SVBox(QWidget):
    """Saturation (x-axis) / Value (y-axis) picker box."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 100)
        self._hue = 0
        self._sat = 255
        self._val = 255
        self._pressed = False

    def setHue(self, h):
        if h == self._hue:
            return
        self._hue = h
        self.update()

    def setSatVal(self, s, v):
        self._sat = s
        self._val = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        # S gradient: white → full-hue color (left to right)
        grad_s = QLinearGradient(0, 0, w, 0)
        grad_s.setColorAt(0, Qt.white)
        grad_s.setColorAt(1, QColor.fromHsv(self._hue, 255, 255))
        painter.fillRect(0, 0, w, h, grad_s)

        # V overlay: transparent → black (top to bottom)
        grad_v = QLinearGradient(0, 0, 0, h)
        grad_v.setColorAt(0, QColor(0, 0, 0, 0))
        grad_v.setColorAt(1, QColor(0, 0, 0, 255))
        painter.fillRect(0, 0, w, h, grad_v)

        # Crosshair
        cx = int((self._sat / 255.0) * (w - 1))
        cy = int(((255 - self._val) / 255.0) * (h - 1))
        for color, radius in [(Qt.black, 6), (Qt.white, 5)]:
            painter.setPen(color)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPoint(cx, cy), radius, radius)

        painter.end()

    def _pick(self, pos):
        w, h = self.width(), self.height()
        x = max(0, min(pos.x(), w - 1))
        y = max(0, min(pos.y(), h - 1))
        self._sat = int((x / (w - 1)) * 255) if w > 1 else 255
        self._val = 255 - (int((y / (h - 1)) * 255) if h > 1 else 0)
        self.update()
        self.colorChanged.emit(QColor.fromHsv(self._hue, self._sat, self._val))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._pick(event.pos())

    def mouseReleaseEvent(self, event):
        self._pressed = False


class ChannelBar(QWidget):
    """Horizontal gradient bar for a single color channel (H/S/V/R/G/B)."""
    valueChanged = pyqtSignal(int)

    def __init__(self, channel, parent=None):
        super().__init__(parent)
        self._channel = channel  # 'H', 'S', 'V', 'R', 'G', 'B'
        self._h = 0
        self._s = 255
        self._v = 255
        self._r = 255
        self._g = 0
        self._b = 0
        self._value = 0
        self._pressed = False
        self.setFixedHeight(16)
        self.setMinimumWidth(80)

    def _max_value(self):
        return 359 if self._channel == 'H' else 255

    def setColor(self, h, s, v, r, g, b):
        self._h, self._s, self._v = h, s, v
        self._r, self._g, self._b = r, g, b
        ch = self._channel
        if ch == 'H':
            self._value = h
        elif ch == 'S':
            self._value = s
        elif ch == 'V':
            self._value = v
        elif ch == 'R':
            self._value = r
        elif ch == 'G':
            self._value = g
        elif ch == 'B':
            self._value = b
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        # Draw gradient
        grad = QLinearGradient(0, 0, w, 0)
        ch = self._channel
        if ch == 'H':
            for i in range(7):
                grad.setColorAt(i / 6, QColor.fromHsv(int(i * 360 / 6) % 360, self._s, self._v))
        elif ch == 'S':
            grad.setColorAt(0, QColor.fromHsv(self._h, 0, self._v))
            grad.setColorAt(1, QColor.fromHsv(self._h, 255, self._v))
        elif ch == 'V':
            grad.setColorAt(0, QColor.fromHsv(self._h, self._s, 0))
            grad.setColorAt(1, QColor.fromHsv(self._h, self._s, 255))
        elif ch == 'R':
            grad.setColorAt(0, QColor(0, self._g, self._b))
            grad.setColorAt(1, QColor(255, self._g, self._b))
        elif ch == 'G':
            grad.setColorAt(0, QColor(self._r, 0, self._b))
            grad.setColorAt(1, QColor(self._r, 255, self._b))
        elif ch == 'B':
            grad.setColorAt(0, QColor(self._r, self._g, 0))
            grad.setColorAt(1, QColor(self._r, self._g, 255))
        painter.fillRect(0, 0, w, h, grad)

        # Draw marker
        max_val = self._max_value()
        marker_x = int((self._value / max_val) * (w - 1)) if max_val > 0 else 0
        painter.setPen(Qt.white)
        painter.drawRect(marker_x - 2, 0, 4, h - 1)
        painter.setPen(Qt.black)
        painter.drawRect(marker_x - 1, 1, 2, h - 3)
        painter.end()

    def _pick(self, pos):
        w = self.width()
        x = max(0, min(pos.x(), w - 1))
        max_val = self._max_value()
        self._value = int((x / (w - 1)) * max_val) if w > 1 else 0
        self.update()
        self.valueChanged.emit(self._value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._pick(event.pos())

    def mouseMoveEvent(self, event):
        if self._pressed:
            self._pick(event.pos())

    def mouseReleaseEvent(self, event):
        self._pressed = False


class ColorSelectorDock(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HueSVC")
        self._popup_loader = PopupConfigLoader()

        # Internal color state
        self._h, self._s, self._v = 0, 255, 255
        color = QColor.fromHsv(0, 255, 255)
        self._r, self._g, self._b = color.red(), color.green(), color.blue()

        main_widget = QWidget(self)
        outer_layout = QVBoxLayout(main_widget)
        outer_layout.setContentsMargins(4, 4, 4, 4)
        outer_layout.setSpacing(6)

        # ── Top: hue bar + SV box ──
        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.hue_bar = HueBar()
        self.sv_box = SVBox()

        top_layout.addWidget(self.hue_bar)
        top_layout.addWidget(self.sv_box, 1)
        outer_layout.addLayout(top_layout, 1)  # stretch=1 so SV box fills space

        # ── Bottom: 6 channel bars ──
        self.channel_bars = {}   # ch -> ChannelBar
        self.channel_labels = {} # ch -> QLineEdit

        font_size = self._popup_loader.get_color_selector_value_font_size()
        font = QFont()
        font.setPointSize(font_size)

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

        main_widget.setLayout(outer_layout)
        self.setWidget(main_widget)

        # Connect top picker signals
        self.hue_bar.hueChanged.connect(self._onHueBarChanged)
        self.sv_box.colorChanged.connect(self._onSVChanged)

        # Initialise label text
        self._updateChannelBars()

        # Poll Krita foreground color (interval configurable)
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self._popup_loader.get_color_selector_poll_interval())
        self._poll_timer.timeout.connect(self._pollKritaColor)
        self._poll_timer.start()

        # Debounce timer for bar dragging — fires after user stops
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._applyPendingColor)

        # Initialize color selector popup and register its shortcut
        from .color_selector_popup import ColorSelectorPopup
        self._color_popup = ColorSelectorPopup(self)
        self._color_popup.setup_popup_shortcut()

    # ── Sync helpers ────────────────────────────────────────────

    def _updateChannelBars(self):
        """Push current state to all channel bars and labels."""
        for bar in self.channel_bars.values():
            bar.setColor(self._h, self._s, self._v, self._r, self._g, self._b)
        self.channel_labels['H'].setText(str(self._h))
        self.channel_labels['S'].setText(str(self._s))
        self.channel_labels['V'].setText(str(self._v))
        self.channel_labels['R'].setText(str(self._r))
        self.channel_labels['G'].setText(str(self._g))
        self.channel_labels['B'].setText(str(self._b))

    def _applyHSV(self, h, s, v, push=True):
        """Set full state from HSV, update all widgets, optionally push to Krita."""
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

    def _applyRGB(self, r, g, b, push=True):
        """Set full state from exact RGB — avoids HSV round-trip drift."""
        self._r, self._g, self._b = r, g, b
        color = QColor(r, g, b)
        h = color.hsvHue()
        self._h = h if h != -1 else self._h
        self._s = color.hsvSaturation()
        self._v = color.value()

        self.hue_bar.setHue(self._h)
        self.sv_box.setHue(self._h)
        self.sv_box.setSatVal(self._s, self._v)
        self._updateChannelBars()
        if push:
            self._setKritaForeground(color)
            self._poll_timer.start()

    def _pollKritaColor(self):
        """Read Krita's current foreground color and sync UI if it changed."""
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
            return  # no change

        color = QColor(r, g, b)
        h = color.hsvHue() if color.hsvHue() != -1 else self._h
        s, v = color.hsvSaturation(), color.value()
        self._applyHSV(h, s, v, push=False)

    # ── Signal handlers ─────────────────────────────────────────

    def _onHueBarChanged(self, hue):
        self._applyHSV(hue, self._s, self._v)

    def _onSVChanged(self, qcolor):
        h = qcolor.hsvHue()
        if h == -1:
            h = self._h
        self._applyHSV(h, qcolor.hsvSaturation(), qcolor.value())

    def _onChannelChanged(self, channel, value, debounce=False):
        h, s, v = self._h, self._s, self._v
        r, g, b = self._r, self._g, self._b
        use_rgb = False

        if channel == 'H':
            h = value
        elif channel == 'S':
            s = value
        elif channel == 'V':
            v = value
        elif channel == 'R':
            r = value
            use_rgb = True
        elif channel == 'G':
            g = value
            use_rgb = True
        elif channel == 'B':
            b = value
            use_rgb = True

        if debounce:
            self._poll_timer.stop()
            if use_rgb:
                self._applyRGB(r, g, b, push=False)
            else:
                self._applyHSV(h, s, v, push=False)
            self._debounce_timer.start()
        else:
            if use_rgb:
                self._applyRGB(r, g, b)
            else:
                self._applyHSV(h, s, v)

    def _applyPendingColor(self):
        self._setKritaForeground(QColor(self._r, self._g, self._b))
        self._poll_timer.start()

    def _stepChannel(self, ch, delta):
        """Increment or decrement a channel value by delta."""
        current = {'H': self._h, 'S': self._s, 'V': self._v,
                   'R': self._r, 'G': self._g, 'B': self._b}[ch]
        max_val = 359 if ch == 'H' else 255
        self._onChannelChanged(ch, max(0, min(max_val, current + delta)))

    def _onChannelInput(self, ch):
        """Called when user finishes editing a channel value input."""
        text = self.channel_labels[ch].text()
        try:
            val = int(text)
        except ValueError:
            self._updateChannelBars()
            return
        max_val = 359 if ch == 'H' else 255
        val = max(0, min(max_val, val))
        self._onChannelChanged(ch, val)

    def _setKritaForeground(self, qcolor):
        """Push the selected color to Krita's foreground."""
        app = Krita.instance()
        view = app.activeWindow().activeView() if app.activeWindow() else None
        if not view:
            return

        doc = app.activeDocument()
        if not doc:
            return

        mc = ManagedColor("RGBA", "U8", "")
        components = mc.components()
        # ManagedColor RGBA components order: [blue, green, red, alpha]
        components[0] = qcolor.blueF()
        components[1] = qcolor.greenF()
        components[2] = qcolor.redF()
        components[3] = 1.0
        mc.setComponents(components)
        view.setForeGroundColor(mc)

    def canvasChanged(self, canvas):
        pass
