"""The Quick Access Palette's Settings dialog (Default/Popup/HueSVC/Quick
Adjust tabs)."""

from ...compat import (
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    Qt,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from ...gesture import is_gesture_enabled


class PaletteConfigDialog(QDialog):
    """Configuration dialog for Quick Access Palette."""

    def __init__(
        self,
        columns,
        docker_icon_size=42,
        popup_icon_size=42,
        huesvc_value_font_size=10,
        huesvc_poll_interval=250,
        huesvc_rgb_display_mode="percentage",
        huesvc_popup_width=350,
        huesvc_popup_height=550,
        huesvc_controls_panel_font_size=12,
        quick_adjust_settings=None,
        config_dialog_width=340,
        config_dialog_height=480,
        huesvc_enabled=True,
        quick_adjust_enabled=True,
        header_button_color="#828282",
        tab_active_font_size=12,
        tab_active_font_color="#ffffff",
        tab_active_background_color="#3f3f3f",
        tab_inactive_font_size=12,
        tab_inactive_font_color="#a0a0a0",
        tab_inactive_background_color="#2b2b2b",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(int(config_dialog_width), int(config_dialog_height))
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        default_page = QWidget()
        default_layout = QVBoxLayout(default_page)

        default_layout.addWidget(QLabel("Columns:"))
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 64)
        self.columns_spin.setValue(int(columns))
        default_layout.addWidget(self.columns_spin)

        default_layout.addWidget(QLabel("Docker Icon Size:"))
        self.docker_icon_size_spin = QSpinBox()
        self.docker_icon_size_spin.setRange(24, 96)
        self.docker_icon_size_spin.setValue(int(docker_icon_size))
        self.docker_icon_size_spin.setSuffix(" px")
        default_layout.addWidget(self.docker_icon_size_spin)

        default_layout.addWidget(self._separator())
        default_layout.addWidget(QLabel("Features"))
        self.gesture_enabled_checkbox = QCheckBox("Enable Gesture Recognition")
        self.gesture_enabled_checkbox.setChecked(is_gesture_enabled())
        default_layout.addWidget(self.gesture_enabled_checkbox)

        self.huesvc_enabled_checkbox = QCheckBox("Enable HueSVC Docker")
        self.huesvc_enabled_checkbox.setChecked(bool(huesvc_enabled))
        default_layout.addWidget(self.huesvc_enabled_checkbox)

        self.quick_adjust_enabled_checkbox = QCheckBox("Enable Quick Adjust Docker")
        self.quick_adjust_enabled_checkbox.setChecked(bool(quick_adjust_enabled))
        default_layout.addWidget(self.quick_adjust_enabled_checkbox)

        default_layout.addWidget(self._separator())
        default_layout.addWidget(QLabel("Settings Dialog Size"))
        default_layout.addWidget(QLabel("Width:"))
        self.config_dialog_width_spin = QSpinBox()
        self.config_dialog_width_spin.setRange(280, 1200)
        self.config_dialog_width_spin.setValue(int(config_dialog_width))
        self.config_dialog_width_spin.setSuffix(" px")
        default_layout.addWidget(self.config_dialog_width_spin)

        default_layout.addWidget(QLabel("Height:"))
        self.config_dialog_height_spin = QSpinBox()
        self.config_dialog_height_spin.setRange(200, 1200)
        self.config_dialog_height_spin.setValue(int(config_dialog_height))
        self.config_dialog_height_spin.setSuffix(" px")
        default_layout.addWidget(self.config_dialog_height_spin)

        default_layout.addWidget(self._separator())
        default_layout.addWidget(QLabel("Header Button Color"))
        self.header_button_color = QColor(header_button_color)
        self.header_button_color_btn = QPushButton()
        self.header_button_color_btn.setFixedHeight(28)
        self.header_button_color_btn.clicked.connect(self.pick_header_button_color)
        self._update_header_button_color_btn()
        default_layout.addWidget(self.header_button_color_btn)

        default_layout.addWidget(self._separator())
        default_layout.addWidget(QLabel("Active Tab Style"))
        default_layout.addWidget(QLabel("Font Size:"))
        self.tab_active_font_size_spin = QSpinBox()
        self.tab_active_font_size_spin.setRange(6, 24)
        self.tab_active_font_size_spin.setValue(int(tab_active_font_size))
        self.tab_active_font_size_spin.setSuffix(" px")
        default_layout.addWidget(self.tab_active_font_size_spin)
        default_layout.addWidget(QLabel("Font Color:"))
        self.tab_active_font_color_btn = self._add_tab_color_row(
            default_layout, tab_active_font_color, "tab_active_font_color"
        )
        default_layout.addWidget(QLabel("Background Color:"))
        self.tab_active_background_color_btn = self._add_tab_color_row(
            default_layout, tab_active_background_color, "tab_active_background_color"
        )

        default_layout.addWidget(self._separator())
        default_layout.addWidget(QLabel("Other Tabs Style"))
        default_layout.addWidget(QLabel("Font Size:"))
        self.tab_inactive_font_size_spin = QSpinBox()
        self.tab_inactive_font_size_spin.setRange(6, 24)
        self.tab_inactive_font_size_spin.setValue(int(tab_inactive_font_size))
        self.tab_inactive_font_size_spin.setSuffix(" px")
        default_layout.addWidget(self.tab_inactive_font_size_spin)
        default_layout.addWidget(QLabel("Font Color:"))
        self.tab_inactive_font_color_btn = self._add_tab_color_row(
            default_layout, tab_inactive_font_color, "tab_inactive_font_color"
        )
        default_layout.addWidget(QLabel("Background Color:"))
        self.tab_inactive_background_color_btn = self._add_tab_color_row(
            default_layout, tab_inactive_background_color, "tab_inactive_background_color"
        )

        default_layout.addStretch(1)
        self.tabs.addTab(default_page, "Default")

        popup_page = QWidget()
        popup_layout = QVBoxLayout(popup_page)
        popup_layout.addWidget(QLabel("Popup Icon Size:"))
        self.popup_icon_size_spin = QSpinBox()
        self.popup_icon_size_spin.setRange(24, 96)
        self.popup_icon_size_spin.setValue(int(popup_icon_size))
        self.popup_icon_size_spin.setSuffix(" px")
        popup_layout.addWidget(self.popup_icon_size_spin)
        popup_layout.addStretch(1)
        self.tabs.addTab(popup_page, "Popup")

        huesvc_page = QWidget()
        huesvc_layout = QVBoxLayout(huesvc_page)

        huesvc_layout.addWidget(QLabel("Value Font Size:"))
        self.huesvc_font_size_spin = QSpinBox()
        self.huesvc_font_size_spin.setRange(6, 24)
        self.huesvc_font_size_spin.setValue(int(huesvc_value_font_size))
        self.huesvc_font_size_spin.setSuffix(" pt")
        huesvc_layout.addWidget(self.huesvc_font_size_spin)

        huesvc_layout.addWidget(QLabel("Foreground Color Poll Interval:"))
        self.huesvc_poll_interval_spin = QSpinBox()
        self.huesvc_poll_interval_spin.setRange(50, 5000)
        self.huesvc_poll_interval_spin.setSingleStep(50)
        self.huesvc_poll_interval_spin.setValue(int(huesvc_poll_interval))
        self.huesvc_poll_interval_spin.setSuffix(" ms")
        huesvc_layout.addWidget(self.huesvc_poll_interval_spin)

        huesvc_layout.addWidget(QLabel("RGB Display Mode:"))
        self.huesvc_rgb_mode_combo = QComboBox()
        self.huesvc_rgb_mode_combo.addItem("Percentage (0-100)", "percentage")
        self.huesvc_rgb_mode_combo.addItem("Value (0-255)", "value")
        index = self.huesvc_rgb_mode_combo.findData(huesvc_rgb_display_mode)
        if index >= 0:
            self.huesvc_rgb_mode_combo.setCurrentIndex(index)
        huesvc_layout.addWidget(self.huesvc_rgb_mode_combo)

        huesvc_layout.addWidget(self._separator())
        huesvc_layout.addWidget(QLabel("Popup Size"))
        huesvc_layout.addWidget(QLabel("Width:"))
        self.huesvc_popup_width_spin = QSpinBox()
        self.huesvc_popup_width_spin.setRange(200, 1200)
        self.huesvc_popup_width_spin.setValue(int(huesvc_popup_width))
        self.huesvc_popup_width_spin.setSuffix(" px")
        huesvc_layout.addWidget(self.huesvc_popup_width_spin)

        huesvc_layout.addWidget(QLabel("Height:"))
        self.huesvc_popup_height_spin = QSpinBox()
        self.huesvc_popup_height_spin.setRange(200, 1200)
        self.huesvc_popup_height_spin.setValue(int(huesvc_popup_height))
        self.huesvc_popup_height_spin.setSuffix(" px")
        huesvc_layout.addWidget(self.huesvc_popup_height_spin)

        huesvc_layout.addWidget(self._separator())
        huesvc_layout.addWidget(QLabel("Right Panel (brush/layer controls) Font Size:"))
        self.huesvc_controls_panel_font_size_spin = QSpinBox()
        self.huesvc_controls_panel_font_size_spin.setRange(6, 24)
        self.huesvc_controls_panel_font_size_spin.setValue(
            int(huesvc_controls_panel_font_size)
        )
        self.huesvc_controls_panel_font_size_spin.setSuffix(" px")
        huesvc_layout.addWidget(self.huesvc_controls_panel_font_size_spin)

        huesvc_layout.addStretch(1)
        self.tabs.addTab(huesvc_page, "HueSVC")

        quick_adjust_settings = quick_adjust_settings or {}
        quick_adjust_page = QWidget()
        quick_adjust_layout = QVBoxLayout(quick_adjust_page)

        quick_adjust_layout.addWidget(QLabel("Font Size:"))
        self.quick_adjust_font_size_spin = QSpinBox()
        self.quick_adjust_font_size_spin.setRange(8, 24)
        self.quick_adjust_font_size_spin.setSuffix(" px")
        self.quick_adjust_font_size_spin.setValue(
            int(
                str(quick_adjust_settings.get("font_size", "12px")).replace("px", "")
                or 12
            )
        )
        quick_adjust_layout.addWidget(self.quick_adjust_font_size_spin)

        self.quick_adjust_size_checkbox = QCheckBox("Enable Size Slider")
        self.quick_adjust_size_checkbox.setChecked(
            quick_adjust_settings.get("size_slider_enabled", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_size_checkbox)

        self.quick_adjust_opacity_checkbox = QCheckBox("Enable Opacity Slider")
        self.quick_adjust_opacity_checkbox.setChecked(
            quick_adjust_settings.get("opacity_slider_enabled", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_opacity_checkbox)

        self.quick_adjust_flow_checkbox = QCheckBox("Enable Flow Slider")
        self.quick_adjust_flow_checkbox.setChecked(
            quick_adjust_settings.get("flow_slider_enabled", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_flow_checkbox)

        self.quick_adjust_layer_opacity_checkbox = QCheckBox(
            "Enable Layer Opacity Slider"
        )
        self.quick_adjust_layer_opacity_checkbox.setChecked(
            quick_adjust_settings.get("layer_opacity_slider_enabled", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_layer_opacity_checkbox)

        quick_adjust_layout.addWidget(self._separator())
        self.quick_adjust_color_history_checkbox = QCheckBox("Enable Color History")
        self.quick_adjust_color_history_checkbox.setChecked(
            quick_adjust_settings.get("color_history_enabled", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_color_history_checkbox)

        quick_adjust_layout.addWidget(QLabel("Color History Count:"))
        self.quick_adjust_color_history_total_spin = QSpinBox()
        self.quick_adjust_color_history_total_spin.setRange(2, 40)
        self.quick_adjust_color_history_total_spin.setValue(
            int(quick_adjust_settings.get("color_history_total", 14))
        )
        quick_adjust_layout.addWidget(self.quick_adjust_color_history_total_spin)

        quick_adjust_layout.addWidget(QLabel("Color History Icon Size:"))
        self.quick_adjust_color_history_icon_spin = QSpinBox()
        self.quick_adjust_color_history_icon_spin.setRange(16, 64)
        self.quick_adjust_color_history_icon_spin.setSuffix(" px")
        self.quick_adjust_color_history_icon_spin.setValue(
            int(quick_adjust_settings.get("color_history_icon_size", 30))
        )
        quick_adjust_layout.addWidget(self.quick_adjust_color_history_icon_spin)

        quick_adjust_layout.addWidget(self._separator())
        self.quick_adjust_brush_history_checkbox = QCheckBox("Enable Brush History")
        self.quick_adjust_brush_history_checkbox.setChecked(
            quick_adjust_settings.get("brush_history_enabled", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_brush_history_checkbox)

        quick_adjust_layout.addWidget(QLabel("Brush History Count:"))
        self.quick_adjust_brush_history_total_spin = QSpinBox()
        self.quick_adjust_brush_history_total_spin.setRange(2, 40)
        self.quick_adjust_brush_history_total_spin.setValue(
            int(quick_adjust_settings.get("brush_history_total", 14))
        )
        quick_adjust_layout.addWidget(self.quick_adjust_brush_history_total_spin)

        quick_adjust_layout.addWidget(QLabel("Brush History Icon Size:"))
        self.quick_adjust_brush_history_icon_spin = QSpinBox()
        self.quick_adjust_brush_history_icon_spin.setRange(16, 64)
        self.quick_adjust_brush_history_icon_spin.setSuffix(" px")
        self.quick_adjust_brush_history_icon_spin.setValue(
            int(quick_adjust_settings.get("brush_history_icon_size", 34))
        )
        quick_adjust_layout.addWidget(self.quick_adjust_brush_history_icon_spin)

        quick_adjust_layout.addWidget(self._separator())
        quick_adjust_layout.addWidget(
            QLabel("Temporary Key Hold Modes (leave blank to disable):")
        )
        quick_adjust_layout.addWidget(QLabel("Alt Erase Key:"))
        self.quick_adjust_alt_erase_edit = QLineEdit(
            quick_adjust_settings.get("alt_erase_key", "")
        )
        quick_adjust_layout.addWidget(self.quick_adjust_alt_erase_edit)

        quick_adjust_layout.addWidget(QLabel("Preserve Alpha Key:"))
        self.quick_adjust_preserve_alpha_edit = QLineEdit(
            quick_adjust_settings.get("preserve_alpha_key", "")
        )
        quick_adjust_layout.addWidget(self.quick_adjust_preserve_alpha_edit)

        quick_adjust_layout.addWidget(QLabel("Select Outline Key:"))
        self.quick_adjust_select_outline_edit = QLineEdit(
            quick_adjust_settings.get("select_outline_key", "")
        )
        quick_adjust_layout.addWidget(self.quick_adjust_select_outline_edit)

        quick_adjust_layout.addWidget(self._separator())
        quick_adjust_layout.addWidget(QLabel("Floating Tool Options"))
        self.quick_adjust_tool_options_checkbox = QCheckBox(
            "Enable Floating Tool Options"
        )
        self.quick_adjust_tool_options_checkbox.setChecked(
            quick_adjust_settings.get("tool_options_enabled", False)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_tool_options_checkbox)

        self.quick_adjust_tool_options_visible_checkbox = QCheckBox("Start Visible")
        self.quick_adjust_tool_options_visible_checkbox.setChecked(
            quick_adjust_settings.get("tool_options_start_visible", True)
        )
        quick_adjust_layout.addWidget(self.quick_adjust_tool_options_visible_checkbox)

        quick_adjust_layout.addWidget(QLabel("Position:"))
        self.quick_adjust_tool_options_position_combo = QComboBox()
        self.quick_adjust_tool_options_position_combo.addItem(
            "Left of Docker", "left_align_top"
        )
        self.quick_adjust_tool_options_position_combo.addItem(
            "Right of Docker", "right_align_top"
        )
        self.quick_adjust_tool_options_position_combo.addItem(
            "Bottom Left of Docker", "bottom_left"
        )
        position_index = self.quick_adjust_tool_options_position_combo.findData(
            quick_adjust_settings.get("tool_options_position", "left_align_top")
        )
        if position_index >= 0:
            self.quick_adjust_tool_options_position_combo.setCurrentIndex(
                position_index
            )
        quick_adjust_layout.addWidget(self.quick_adjust_tool_options_position_combo)

        quick_adjust_layout.addWidget(self._separator())
        quick_adjust_layout.addWidget(
            QLabel("Temporary Brush Sets (key hold → switch brush):")
        )
        self.temp_brush_set_table = QTableWidget()
        self.temp_brush_set_table.setColumnCount(3)
        self.temp_brush_set_table.setHorizontalHeaderLabels(
            ["Key", "Brush Name", "Size Scale"]
        )
        self.temp_brush_set_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.temp_brush_set_table.setMinimumHeight(120)
        for entry in (quick_adjust_settings or {}).get("temp_brush_sets", []):
            self._add_temp_brush_set_row(
                entry.get("key", ""),
                entry.get("brush", ""),
                entry.get("size_scale", 0.0),
            )
        quick_adjust_layout.addWidget(self.temp_brush_set_table)

        temp_brush_set_btn_layout = QHBoxLayout()
        add_temp_brush_set_btn = QPushButton("Add Row")
        add_temp_brush_set_btn.clicked.connect(
            lambda: self._add_temp_brush_set_row("", "", 0.0)
        )
        remove_temp_brush_set_btn = QPushButton("Remove Selected")
        remove_temp_brush_set_btn.clicked.connect(
            self._remove_selected_temp_brush_set_row
        )
        temp_brush_set_btn_layout.addWidget(add_temp_brush_set_btn)
        temp_brush_set_btn_layout.addWidget(remove_temp_brush_set_btn)
        quick_adjust_layout.addLayout(temp_brush_set_btn_layout)

        quick_adjust_layout.addWidget(self._separator())
        quick_adjust_layout.addWidget(
            QLabel(
                "Blend Modes (one per line - shown in the Quick Adjust docker "
                "and the HueSVC popup's blend mode dropdown):"
            )
        )
        self.quick_adjust_blender_mode_edit = QTextEdit()
        self.quick_adjust_blender_mode_edit.setPlainText(
            "\n".join(quick_adjust_settings.get("blender_mode_list", []))
        )
        self.quick_adjust_blender_mode_edit.setMinimumHeight(100)
        self.quick_adjust_blender_mode_edit.setMaximumHeight(150)
        self.quick_adjust_blender_mode_edit.setPlaceholderText(
            "Enter blend modes, one per line"
        )
        quick_adjust_layout.addWidget(self.quick_adjust_blender_mode_edit)

        quick_adjust_layout.addStretch(1)
        self.tabs.addTab(quick_adjust_page, "Quick Adjust")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.tabs)
        layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_columns(self):
        return self.columns_spin.value()

    def get_docker_icon_size(self):
        return self.docker_icon_size_spin.value()

    def pick_header_button_color(self):
        color = QColorDialog.getColor(
            self.header_button_color, self, "Select Header Button Color"
        )
        if color.isValid():
            self.header_button_color = color
            self._update_header_button_color_btn()

    def _update_header_button_color_btn(self):
        self.header_button_color_btn.setStyleSheet(
            f"background-color: {self.header_button_color.name()}; border: 1px solid #888;"
        )
        self.header_button_color_btn.setText(self.header_button_color.name())

    def get_header_button_color(self):
        return self.header_button_color.name()

    def _add_tab_color_row(self, layout, initial_hex, attr_name):
        """A full-width color-picker button, storing its QColor on
        self.<attr_name> - used for the Active/Other Tab Style rows, which
        need four independent color pickers with the same click/repaint logic
        as header_button_color_btn above."""
        setattr(self, attr_name, QColor(initial_hex))
        button = QPushButton()
        button.setFixedHeight(28)
        button.clicked.connect(
            lambda checked=False: self._pick_tab_color(attr_name, button)
        )
        self._update_tab_color_btn(attr_name, button)
        layout.addWidget(button)
        return button

    def _pick_tab_color(self, attr_name, button):
        current = getattr(self, attr_name)
        color = QColorDialog.getColor(current, self, "Select Color")
        if color.isValid():
            setattr(self, attr_name, color)
            self._update_tab_color_btn(attr_name, button)

    def _update_tab_color_btn(self, attr_name, button):
        color = getattr(self, attr_name)
        button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")
        button.setText(color.name())

    def get_tab_active_font_size(self):
        return self.tab_active_font_size_spin.value()

    def get_tab_active_font_color(self):
        return self.tab_active_font_color.name()

    def get_tab_active_background_color(self):
        return self.tab_active_background_color.name()

    def get_tab_inactive_font_size(self):
        return self.tab_inactive_font_size_spin.value()

    def get_tab_inactive_font_color(self):
        return self.tab_inactive_font_color.name()

    def get_tab_inactive_background_color(self):
        return self.tab_inactive_background_color.name()

    def get_popup_icon_size(self):
        return self.popup_icon_size_spin.value()

    def get_gesture_enabled(self):
        return self.gesture_enabled_checkbox.isChecked()

    def get_huesvc_enabled(self):
        return self.huesvc_enabled_checkbox.isChecked()

    def get_quick_adjust_enabled(self):
        return self.quick_adjust_enabled_checkbox.isChecked()

    def get_huesvc_value_font_size(self):
        return self.huesvc_font_size_spin.value()

    def get_huesvc_poll_interval(self):
        return self.huesvc_poll_interval_spin.value()

    def get_huesvc_rgb_display_mode(self):
        return self.huesvc_rgb_mode_combo.currentData()

    def get_huesvc_popup_width(self):
        return self.huesvc_popup_width_spin.value()

    def get_huesvc_popup_height(self):
        return self.huesvc_popup_height_spin.value()

    def get_huesvc_controls_panel_font_size(self):
        return self.huesvc_controls_panel_font_size_spin.value()

    def get_config_dialog_width(self):
        return self.config_dialog_width_spin.value()

    def get_config_dialog_height(self):
        return self.config_dialog_height_spin.value()

    def _add_temp_brush_set_row(self, key, brush, size_scale):
        row = self.temp_brush_set_table.rowCount()
        self.temp_brush_set_table.insertRow(row)
        self.temp_brush_set_table.setItem(row, 0, QTableWidgetItem(key))
        self.temp_brush_set_table.setItem(row, 1, QTableWidgetItem(brush))
        self.temp_brush_set_table.setItem(row, 2, QTableWidgetItem(str(size_scale)))

    def _remove_selected_temp_brush_set_row(self):
        rows = {index.row() for index in self.temp_brush_set_table.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self.temp_brush_set_table.removeRow(row)

    def _temp_brush_sets_from_table(self):
        entries = []
        for row in range(self.temp_brush_set_table.rowCount()):
            key_item = self.temp_brush_set_table.item(row, 0)
            brush_item = self.temp_brush_set_table.item(row, 1)
            scale_item = self.temp_brush_set_table.item(row, 2)
            key = key_item.text().strip() if key_item else ""
            brush = brush_item.text().strip() if brush_item else ""
            if not key or not brush:
                continue
            try:
                size_scale = float(scale_item.text().strip()) if scale_item else 0.0
            except ValueError:
                size_scale = 0.0
            entries.append({"key": key, "brush": brush, "size_scale": size_scale})
        return entries

    def get_quick_adjust_settings(self):
        return {
            "font_size": f"{self.quick_adjust_font_size_spin.value()}px",
            "size_slider_enabled": self.quick_adjust_size_checkbox.isChecked(),
            "opacity_slider_enabled": self.quick_adjust_opacity_checkbox.isChecked(),
            "flow_slider_enabled": self.quick_adjust_flow_checkbox.isChecked(),
            "layer_opacity_slider_enabled": self.quick_adjust_layer_opacity_checkbox.isChecked(),
            "color_history_enabled": self.quick_adjust_color_history_checkbox.isChecked(),
            "color_history_total": self.quick_adjust_color_history_total_spin.value(),
            "color_history_icon_size": self.quick_adjust_color_history_icon_spin.value(),
            "brush_history_enabled": self.quick_adjust_brush_history_checkbox.isChecked(),
            "brush_history_total": self.quick_adjust_brush_history_total_spin.value(),
            "brush_history_icon_size": self.quick_adjust_brush_history_icon_spin.value(),
            "alt_erase_key": self.quick_adjust_alt_erase_edit.text().strip(),
            "preserve_alpha_key": self.quick_adjust_preserve_alpha_edit.text().strip(),
            "select_outline_key": self.quick_adjust_select_outline_edit.text().strip(),
            "tool_options_enabled": self.quick_adjust_tool_options_checkbox.isChecked(),
            "tool_options_start_visible": self.quick_adjust_tool_options_visible_checkbox.isChecked(),
            "tool_options_position": self.quick_adjust_tool_options_position_combo.currentData(),
            "temp_brush_sets": self._temp_brush_sets_from_table(),
            "blender_mode_list": self._blender_mode_list_from_editor(),
        }

    def _blender_mode_list_from_editor(self):
        modes_str = self.quick_adjust_blender_mode_edit.toPlainText().strip()
        if not modes_str:
            return []
        return [m.strip() for m in modes_str.split("\n") if m.strip()]

    def _separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator
