"""HueSVC color-picker popup for the remastered plugin.

Ported from the legacy `color_selector_popup.py`. The embedded brush/layer
controls panel (BrushLayerControlsWidget/BrushToggleWidget) was intentionally
left behind, matching the docker port — only the standalone color picker is
migrated here.
"""

from krita import Krita, ManagedColor  # type: ignore

from ..compat import (
    QColor,
    QCursor,
    QFont,
    QFrame,
    QHBoxLayout,
    QIntValidator,
    QLineEdit,
    QPushButton,
    QShortcut,
    Qt,
    QTimer,
    QVBoxLayout,
)
from ..infrastructure import PaletteRepository
from .docker import DEFAULT_HUESVC_SETTINGS, ChannelBar, FgBgColorWidget, HueBar, SVBox


def _load_huesvc_settings():
    document = PaletteRepository().load()
    settings = dict(DEFAULT_HUESVC_SETTINGS)
    settings.update(document.settings.get("huesvc", {}))
    return settings


class HueSvcPopup(QFrame):
    """Frameless popup window containing the HueSVC color selector UI."""

    def __init__(self, parent=None, close_shortcuts=None):
        super().__init__(
            parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.close_shortcuts = list(close_shortcuts or [])
        self.shortcut_handlers = []

        self._settings = _load_huesvc_settings()

        self._h, self._s, self._v = 0, 255, 255
        color = QColor.fromHsv(0, 255, 255)
        self._r, self._g, self._b = color.red(), color.green(), color.blue()
        self._bg_r, self._bg_g, self._bg_b = 255, 255, 255

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(6)

        fg_bg_layout = QHBoxLayout()
        fg_bg_layout.setContentsMargins(0, 0, 0, 0)
        self.fg_bg_widget = FgBgColorWidget()
        self.fg_bg_widget.swapRequested.connect(self._swapColors)
        fg_bg_layout.addWidget(self.fg_bg_widget)
        fg_bg_layout.addStretch()
        outer_layout.addLayout(fg_bg_layout)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(6)

        self.hue_bar = HueBar()
        self.hue_bar.setMinimumHeight(150)
        self.sv_box = SVBox()
        self.sv_box.setMinimumSize(200, 150)

        top_layout.addWidget(self.hue_bar)
        top_layout.addWidget(self.sv_box, 1)
        outer_layout.addLayout(top_layout, 1)

        self.channel_bars = {}
        self.channel_labels = {}

        font = QFont()
        font.setPointSize(self._settings["value_font_size"])

        channels_layout = QVBoxLayout()
        channels_layout.setSpacing(3)
        channels_layout.setContentsMargins(0, 0, 0, 0)
        channels_layout.setAlignment(Qt.AlignTop)

        for ch in ("H", "S", "V", "R", "G", "B"):
            row = QHBoxLayout()
            row.setSpacing(4)

            bar = ChannelBar(ch)

            if ch == "H":
                max_val = 359
            elif ch in ("R", "G", "B"):
                max_val = 255 if self._settings["rgb_display_mode"] == "value" else 100
            else:
                max_val = 100
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
            bar.valueChanged.connect(
                lambda val, c=ch: self._onChannelChanged(
                    c,
                    (
                        round(val * 255 / 100)
                        if c in ("R", "G", "B")
                        and self._settings["rgb_display_mode"] == "value"
                        else val
                    ),
                    debounce=True,
                )
            )

        outer_layout.addLayout(channels_layout)

        self.hue_bar.hueChanged.connect(self._onHueBarChanged)
        self.sv_box.colorChanged.connect(self._onSVChanged)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self._settings["poll_interval"])
        self._poll_timer.timeout.connect(self._pollKritaColor)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._applyPendingColor)

        self._updateChannelBars()
        self.register_close_shortcuts()

    # ------------------------------------------------------------------
    # Visibility / positioning
    # ------------------------------------------------------------------
    def register_close_shortcuts(self):
        for key_sequence in self.close_shortcuts:
            try:
                if key_sequence.isEmpty():
                    continue
            except AttributeError:
                pass
            shortcut = QShortcut(key_sequence, self)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.activated.connect(self.close_popup)
            self.shortcut_handlers.append(shortcut)

    def close_popup(self):
        self.close()

    def show_at_cursor(self):
        self.resize(self._settings["popup_width"], self._settings["popup_height"])
        cursor_pos = QCursor.pos()
        self.move(
            cursor_pos.x() - self.width() // 4, cursor_pos.y() - self.height() // 3
        )
        self.show()
        self.raise_()
        self.activateWindow()
        self._pollKritaColor()
        self._poll_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._poll_timer.stop()
        self._debounce_timer.stop()

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------
    def _updateChannelBars(self):
        def d(x):
            return round(x * 100 / 255)

        s100, v100 = d(self._s), d(self._v)
        r100, g100, b100 = d(self._r), d(self._g), d(self._b)
        for bar in self.channel_bars.values():
            bar.setColor(self._h, s100, v100, r100, g100, b100)
        rgb_mode = self._settings["rgb_display_mode"]
        r_disp = self._r if rgb_mode == "value" else r100
        g_disp = self._g if rgb_mode == "value" else g100
        b_disp = self._b if rgb_mode == "value" else b100
        self.channel_labels["H"].setText(str(self._h))
        self.channel_labels["S"].setText(str(s100))
        self.channel_labels["V"].setText(str(v100))
        self.channel_labels["R"].setText(str(r_disp))
        self.channel_labels["G"].setText(str(g_disp))
        self.channel_labels["B"].setText(str(b_disp))
        self.fg_bg_widget.setColors(
            QColor(self._r, self._g, self._b),
            QColor(self._bg_r, self._bg_g, self._bg_b),
        )

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

    def _applyRGB(self, r, g, b, push=True):
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
        app = Krita.instance()
        if not app.activeWindow():
            return
        view = app.activeWindow().activeView()
        if not view:
            return
        canvas = view.canvas()

        mc = view.foregroundColor()
        if mc:
            qcolor = mc.colorForCanvas(canvas)
            if qcolor and qcolor.isValid():
                r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
                if (r, g, b) != (self._r, self._g, self._b):
                    color = QColor(r, g, b)
                    h = color.hsvHue() if color.hsvHue() != -1 else self._h
                    s, v = color.hsvSaturation(), color.value()
                    self._applyHSV(h, s, v, push=False)

        mc_bg = view.backgroundColor()
        if mc_bg:
            qcolor_bg = mc_bg.colorForCanvas(canvas)
            if qcolor_bg and qcolor_bg.isValid():
                r, g, b = qcolor_bg.red(), qcolor_bg.green(), qcolor_bg.blue()
                if (r, g, b) != (self._bg_r, self._bg_g, self._bg_b):
                    self._bg_r, self._bg_g, self._bg_b = r, g, b
                    self.fg_bg_widget.setColors(
                        QColor(self._r, self._g, self._b),
                        QColor(self._bg_r, self._bg_g, self._bg_b),
                    )

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------
    def _onHueBarChanged(self, hue):
        self._applyHSV(hue, self._s, self._v)

    def _onSVChanged(self, qcolor):
        h = qcolor.hsvHue() if qcolor.hsvHue() != -1 else self._h
        self._applyHSV(h, qcolor.hsvSaturation(), qcolor.value())

    def _onChannelChanged(self, channel, value, debounce=False):
        h, s, v = self._h, self._s, self._v
        r, g, b = self._r, self._g, self._b
        use_rgb = False

        def i(x):
            return round(x * 255 / 100)

        rgb_mode = self._settings["rgb_display_mode"]
        if channel == "H":
            h = value
        elif channel == "S":
            s = i(value)
        elif channel == "V":
            v = i(value)
        elif channel == "R":
            r = value if rgb_mode == "value" else i(value)
            use_rgb = True
        elif channel == "G":
            g = value if rgb_mode == "value" else i(value)
            use_rgb = True
        elif channel == "B":
            b = value if rgb_mode == "value" else i(value)
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
        if ch == "H":
            current, max_val = self._h, 359
        elif ch in ("S", "V"):
            internal = {"S": self._s, "V": self._v}[ch]
            current, max_val = round(internal * 100 / 255), 100
        else:
            internal = {"R": self._r, "G": self._g, "B": self._b}[ch]
            if self._settings["rgb_display_mode"] == "value":
                current, max_val = internal, 255
            else:
                current, max_val = round(internal * 100 / 255), 100
        self._onChannelChanged(ch, max(0, min(max_val, current + delta)))

    def _onChannelInput(self, ch):
        text = self.channel_labels[ch].text()
        try:
            val = int(text)
        except ValueError:
            self._updateChannelBars()
            return
        if ch == "H":
            max_val = 359
        elif ch in ("R", "G", "B"):
            max_val = 255 if self._settings["rgb_display_mode"] == "value" else 100
        else:
            max_val = 100
        self._onChannelChanged(ch, max(0, min(max_val, val)))

    def _swapColors(self):
        app = Krita.instance()
        if not app.activeWindow():
            return
        view = app.activeWindow().activeView()
        if not view:
            return
        mc_fg = view.foregroundColor()
        mc_bg = view.backgroundColor()
        if not mc_fg or not mc_bg:
            return
        view.setForeGroundColor(mc_bg)
        view.setBackGroundColor(mc_fg)
        canvas = view.canvas()
        qcolor_new_fg = mc_bg.colorForCanvas(canvas)
        if qcolor_new_fg and qcolor_new_fg.isValid():
            color = QColor(
                qcolor_new_fg.red(), qcolor_new_fg.green(), qcolor_new_fg.blue()
            )
            h = color.hsvHue() if color.hsvHue() != -1 else self._h
            self._applyHSV(h, color.hsvSaturation(), color.value(), push=False)
        qcolor_new_bg = mc_fg.colorForCanvas(canvas)
        if qcolor_new_bg and qcolor_new_bg.isValid():
            self._bg_r, self._bg_g, self._bg_b = (
                qcolor_new_bg.red(),
                qcolor_new_bg.green(),
                qcolor_new_bg.blue(),
            )
        self.fg_bg_widget.setColors(
            QColor(self._r, self._g, self._b),
            QColor(self._bg_r, self._bg_g, self._bg_b),
        )

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
