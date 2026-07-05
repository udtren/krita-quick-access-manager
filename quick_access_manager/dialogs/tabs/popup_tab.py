from ...compat import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QKeySequenceEdit,
    QComboBox,
    QCheckBox,
    Qt,
)
from ...config.popup_loader import PopupConfigLoader


class PopupTab:
    """Tab for popup shortcut and appearance settings (popup.json)."""

    def __init__(self):
        self.popup_fields = {}
        self.popup_loader = PopupConfigLoader()
        self._layout = None

    def create_page(self):
        page = QWidget()
        outer = QVBoxLayout()
        page.setLayout(outer)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self._layout = QVBoxLayout()
        inner.setLayout(self._layout)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._load()
        return page

    def _load(self):
        layout = self._layout

        layout.addWidget(QLabel("[Popup Shortcuts]"))
        layout.addWidget(
            QLabel(
                "Configure keyboard shortcuts for popup windows.\n"
                "Note: Changes require Krita restart to take effect."
            )
        )

        def _shortcut_row(label_text, field_key, get_str_fn):
            hl = QHBoxLayout()
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignLeft)
            edit = QKeySequenceEdit()
            edit.setKeySequence(get_str_fn())
            edit.setMaximumWidth(150)
            hl.addWidget(label)
            hl.addStretch()
            hl.addWidget(edit)
            layout.addLayout(hl)
            self.popup_fields[field_key] = edit

        _shortcut_row(
            "Actions Popup Shortcut",
            "actions_popup_shortcut",
            self.popup_loader.get_actions_popup_shortcut_string,
        )
        _shortcut_row(
            "Brush Sets Popup Shortcut",
            "brush_sets_popup_shortcut",
            self.popup_loader.get_brush_sets_popup_shortcut_string,
        )
        _shortcut_row(
            "Color Selector Popup Shortcut",
            "color_selector_popup_shortcut",
            self.popup_loader.get_color_selector_popup_shortcut_string,
        )
        _shortcut_row(
            "Preset Switch Popup Shortcut",
            "preset_switch_popup_shortcut",
            self.popup_loader.get_preset_switch_popup_shortcut_string,
        )

        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("[Popup Appearance]"))

        def _int_row(label_text, field_key, get_fn):
            hl = QHBoxLayout()
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignLeft)
            edit = QLineEdit(str(get_fn()))
            edit.setFixedWidth(80)
            edit.setAlignment(Qt.AlignRight)
            hl.addWidget(label)
            hl.addStretch()
            hl.addWidget(edit)
            layout.addLayout(hl)
            self.popup_fields[field_key] = edit

        _int_row(
            "Brush Icon Size", "brush_icon_size", self.popup_loader.get_brush_icon_size
        )
        _int_row(
            "Grid Label Width",
            "grid_label_width",
            self.popup_loader.get_grid_label_width,
        )

        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("[Color Selector Popup]"))

        _int_row(
            "Popup Width",
            "color_selector_popup_width",
            self.popup_loader.get_color_selector_popup_width,
        )
        _int_row(
            "Popup Height",
            "color_selector_popup_height",
            self.popup_loader.get_color_selector_popup_height,
        )
        _int_row(
            "Brush/Layer Controls Panel Width",
            "color_selector_controls_panel_width",
            self.popup_loader.get_color_selector_controls_panel_width,
        )
        _int_row(
            "Value Font Size",
            "color_selector_value_font_size",
            self.popup_loader.get_color_selector_value_font_size,
        )
        _int_row(
            "Foreground Color Check Interval (ms)",
            "color_selector_poll_interval",
            self.popup_loader.get_color_selector_poll_interval,
        )

        hl = QHBoxLayout()
        label = QLabel("R/G/B Display Mode")
        label.setAlignment(Qt.AlignLeft)
        combo = QComboBox()
        combo.addItem("Percentage (0-100)", "percentage")
        combo.addItem("Value (0-255)", "value")
        current_mode = self.popup_loader.get_color_selector_rgb_display_mode()
        combo.setCurrentIndex(0 if current_mode == "percentage" else 1)
        hl.addWidget(label)
        hl.addStretch()
        hl.addWidget(combo)
        layout.addLayout(hl)
        self.popup_fields["color_selector_rgb_display_mode"] = combo

        hl = QHBoxLayout()
        label = QLabel("Show Brush/Layer Controls Panel")
        label.setAlignment(Qt.AlignLeft)
        checkbox = QCheckBox()
        checkbox.setChecked(
            self.popup_loader.get_color_selector_controls_panel_enabled()
        )
        hl.addWidget(label)
        hl.addStretch()
        hl.addWidget(checkbox)
        layout.addLayout(hl)
        self.popup_fields["color_selector_controls_panel_enabled"] = checkbox

        layout.addStretch()

    def save(self):
        _int_setters = {
            "brush_icon_size": self.popup_loader.set_brush_icon_size,
            "grid_label_width": self.popup_loader.set_grid_label_width,
            "color_selector_popup_width": self.popup_loader.set_color_selector_popup_width,
            "color_selector_popup_height": self.popup_loader.set_color_selector_popup_height,
            "color_selector_controls_panel_width": self.popup_loader.set_color_selector_controls_panel_width,
            "color_selector_value_font_size": self.popup_loader.set_color_selector_value_font_size,
            "color_selector_poll_interval": self.popup_loader.set_color_selector_poll_interval,
        }
        _shortcut_setters = {
            "actions_popup_shortcut": self.popup_loader.set_actions_popup_shortcut,
            "brush_sets_popup_shortcut": self.popup_loader.set_brush_sets_popup_shortcut,
            "color_selector_popup_shortcut": self.popup_loader.set_color_selector_popup_shortcut,
            "preset_switch_popup_shortcut": self.popup_loader.set_preset_switch_popup_shortcut,
        }

        for key, edit in self.popup_fields.items():
            if key in _shortcut_setters:
                _shortcut_setters[key](edit.keySequence().toString())
            elif key == "color_selector_rgb_display_mode":
                self.popup_loader.set_color_selector_rgb_display_mode(
                    edit.currentData()
                )
            elif key == "color_selector_controls_panel_enabled":
                self.popup_loader.set_color_selector_controls_panel_enabled(
                    edit.isChecked()
                )
            elif key in _int_setters:
                try:
                    _int_setters[key](int(edit.text()))
                except ValueError:
                    pass
