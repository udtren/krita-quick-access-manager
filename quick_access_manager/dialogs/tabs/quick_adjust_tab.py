import json
import os
from ...compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QCheckBox, QTextEdit, QGroupBox, QComboBox, Qt,
)
from ...utils.config_utils import get_config_dir


class QuickAdjustTab:
    """Tab for quick_adjust_docker.json and docker_buttons.json settings."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.quick_adjust_fields = {}
        self.docker_buttons_fields = []
        self.quick_adjust_config = {}
        self.quick_adjust_path = None
        self.docker_buttons_config = {}
        self.docker_buttons_path = None
        self._layout = None
        self.docker_buttons_container = None

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
        config_dir = os.path.dirname(self.config_path)
        quick_adjust_path = os.path.join(config_dir, "quick_adjust_docker.json")

        if not os.path.exists(quick_adjust_path):
            self.quick_adjust_config = {}
            self._load_docker_buttons()
            return

        with open(quick_adjust_path, "r", encoding="utf-8") as f:
            self.quick_adjust_config = json.load(f)

        self.quick_adjust_path = quick_adjust_path
        layout = self._layout

        # brush_section
        brush_section = self.quick_adjust_config.get("brush_section", {})
        layout.addWidget(QLabel("[brush_section]"))
        for slider_name in ["size_slider", "opacity_slider", "flow_slider"]:
            slider = brush_section.get(slider_name, {})
            if slider_name == "flow_slider" and not slider:
                slider = {"enabled": True, "number_size": "12px"}
                if "brush_section" not in self.quick_adjust_config:
                    self.quick_adjust_config["brush_section"] = {}
                self.quick_adjust_config["brush_section"]["flow_slider"] = slider
            layout.addWidget(QLabel(f"  {slider_name}:"))
            for key, value in slider.items():
                hl = QHBoxLayout()
                label = QLabel(f"    {key}")
                label.setAlignment(Qt.AlignLeft)
                if isinstance(value, bool):
                    edit = QCheckBox()
                    edit.setChecked(value)
                else:
                    edit = QLineEdit(str(value))
                    edit.setFixedWidth(80)
                    edit.setAlignment(Qt.AlignRight)
                hl.addWidget(label)
                hl.addStretch()
                hl.addWidget(edit)
                layout.addLayout(hl)
                self.quick_adjust_fields[("brush_section", slider_name, key)] = edit

        # layer_section
        layer_section = self.quick_adjust_config.get("layer_section", {})
        layout.addWidget(QLabel("[layer_section]"))
        opacity_slider = layer_section.get("opacity_slider", {})
        layout.addWidget(QLabel("  opacity_slider:"))
        for key, value in opacity_slider.items():
            hl = QHBoxLayout()
            label = QLabel(f"    {key}")
            label.setAlignment(Qt.AlignLeft)
            if isinstance(value, bool):
                edit = QCheckBox()
                edit.setChecked(value)
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
            hl.addWidget(label)
            hl.addStretch()
            hl.addWidget(edit)
            layout.addLayout(hl)
            self.quick_adjust_fields[("layer_section", "opacity_slider", key)] = edit

        # history sections
        for section_name in ["color_history_section", "brush_history_section"]:
            section = self.quick_adjust_config.get(section_name, {})
            layout.addWidget(QLabel(f"[{section_name}]"))
            for key, value in section.items():
                hl = QHBoxLayout()
                label = QLabel(f"  {key}")
                label.setAlignment(Qt.AlignLeft)
                if isinstance(value, bool):
                    edit = QCheckBox()
                    edit.setChecked(value)
                else:
                    edit = QLineEdit(str(value))
                    edit.setFixedWidth(80)
                    edit.setAlignment(Qt.AlignRight)
                hl.addWidget(label)
                hl.addStretch()
                hl.addWidget(edit)
                layout.addLayout(hl)
                self.quick_adjust_fields[(section_name, key)] = edit

        # status_bar_section
        status_bar = self.quick_adjust_config.get("status_bar_section", {})
        layout.addWidget(QLabel("[status_bar_section]"))
        for key, value in status_bar.items():
            hl = QHBoxLayout()
            label = QLabel(f"  {key}")
            label.setAlignment(Qt.AlignLeft)
            if isinstance(value, bool):
                edit = QCheckBox()
                edit.setChecked(value)
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
            hl.addWidget(label)
            hl.addStretch()
            hl.addWidget(edit)
            layout.addLayout(hl)
            self.quick_adjust_fields[("status_bar_section", key)] = edit

        # docker_toggle_section
        docker_toggle = self.quick_adjust_config.get("docker_toggle_section", {})
        layout.addWidget(QLabel("[docker_toggle_section]"))
        for key, value in docker_toggle.items():
            hl = QHBoxLayout()
            label = QLabel(f"  {key}")
            label.setAlignment(Qt.AlignLeft)
            if isinstance(value, bool):
                edit = QCheckBox()
                edit.setChecked(value)
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
            hl.addWidget(label)
            hl.addStretch()
            hl.addWidget(edit)
            layout.addLayout(hl)
            self.quick_adjust_fields[("docker_toggle_section", key)] = edit

        # Alt Erase
        layout.addWidget(QLabel("[Alt Erase]"))
        hl = QHBoxLayout()
        label = QLabel("  Hold key to temporarily activate erase mode")
        label.setAlignment(Qt.AlignLeft)
        chk = QCheckBox()
        chk.setChecked(self.quick_adjust_config.get("alt_erase_enabled", True))
        hl.addWidget(label)
        hl.addStretch()
        hl.addWidget(chk)
        layout.addLayout(hl)
        self.quick_adjust_fields[("alt_erase_enabled",)] = chk

        hl = QHBoxLayout()
        label = QLabel("  Toggle Key (e.g. Alt, Shift, A, F1)")
        label.setAlignment(Qt.AlignLeft)
        key_edit = QLineEdit(self.quick_adjust_config.get("alt_erase_key", "Alt"))
        key_edit.setFixedWidth(80)
        key_edit.setAlignment(Qt.AlignRight)
        hl.addWidget(label)
        hl.addStretch()
        hl.addWidget(key_edit)
        layout.addLayout(hl)
        self.quick_adjust_fields[("alt_erase_key",)] = key_edit

        # floating_widgets
        floating_widgets = self.quick_adjust_config.get("floating_widgets", {})
        if "floating_widgets" not in self.quick_adjust_config:
            self.quick_adjust_config["floating_widgets"] = {
                "tool_options": {"enabled": True, "start_visible": True},
                "color_selector": {"enabled": True, "start_visible": False},
            }
            floating_widgets = self.quick_adjust_config["floating_widgets"]

        layout.addWidget(QLabel("[floating_widgets]"))
        for widget_name in ["tool_options", "color_selector"]:
            default_start_visible = True if widget_name == "tool_options" else False
            widget_config = floating_widgets.get(widget_name, {"enabled": True, "start_visible": default_start_visible})
            if widget_name not in floating_widgets:
                floating_widgets[widget_name] = {"enabled": True, "start_visible": default_start_visible}
                widget_config = floating_widgets[widget_name]
            else:
                if "start_visible" not in widget_config:
                    widget_config["start_visible"] = default_start_visible
                    floating_widgets[widget_name]["start_visible"] = default_start_visible

            layout.addWidget(QLabel(f"  {widget_name}:"))
            for key, value in widget_config.items():
                if key == "start_visible":
                    continue
                hl = QHBoxLayout()
                label = QLabel(f"    {key}")
                label.setAlignment(Qt.AlignLeft)
                if isinstance(value, bool):
                    edit = QCheckBox()
                    edit.setChecked(value)
                    hl.addWidget(label)
                    hl.addStretch()
                    hl.addWidget(edit)
                elif key == "position":
                    edit = QComboBox()
                    edit.addItems(["left_align_top", "right_align_top"])
                    edit.setCurrentText(str(value))
                    edit.setFixedWidth(120)
                    hl.addWidget(label)
                    hl.addStretch()
                    hl.addWidget(edit)
                else:
                    edit = QLineEdit(str(value))
                    edit.setFixedWidth(80)
                    edit.setAlignment(Qt.AlignRight)
                    hl.addWidget(label)
                    hl.addStretch()
                    hl.addWidget(edit)
                layout.addLayout(hl)
                self.quick_adjust_fields[("floating_widgets", widget_name, key)] = edit

        # font_size
        font_size = self.quick_adjust_config.get("font_size", "12px")
        layout.addWidget(QLabel("[General]"))
        hl = QHBoxLayout()
        label = QLabel("  font_size")
        label.setAlignment(Qt.AlignLeft)
        edit = QLineEdit(str(font_size))
        edit.setFixedWidth(80)
        edit.setAlignment(Qt.AlignRight)
        hl.addWidget(label)
        hl.addStretch()
        hl.addWidget(edit)
        layout.addLayout(hl)
        self.quick_adjust_fields[("font_size",)] = edit

        # blender_mode_list
        blender_modes = self.quick_adjust_config.get("blender_mode_list", [])
        vl = QVBoxLayout()
        label = QLabel("  blender_mode_list (one per line)")
        label.setAlignment(Qt.AlignLeft)
        blender_edit = QTextEdit()
        blender_edit.setPlainText("\n".join(blender_modes))
        blender_edit.setMinimumHeight(100)
        blender_edit.setMaximumHeight(150)
        blender_edit.setPlaceholderText("Enter blend modes, one per line")
        vl.addWidget(label)
        vl.addWidget(blender_edit)
        layout.addLayout(vl)
        self.quick_adjust_fields[("blender_mode_list",)] = blender_edit

        self._load_docker_buttons()
        layout.addStretch()

    def _load_docker_buttons(self):
        layout = self._layout
        docker_buttons_path = os.path.join(get_config_dir(), "docker_buttons.json")

        if not os.path.exists(docker_buttons_path):
            from ...config.quick_adjust_docker_loader import ensure_docker_buttons_config_exists
            ensure_docker_buttons_config_exists()

        with open(docker_buttons_path, "r", encoding="utf-8") as f:
            self.docker_buttons_config = json.load(f)

        self.docker_buttons_path = docker_buttons_path

        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("[Docker Toggle Buttons]"))
        layout.addWidget(
            QLabel(
                "Configure buttons to toggle visibility of docker panels.\n"
                "Each button can have: name, width, icon, keywords, and description."
            )
        )

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Button")
        add_btn.clicked.connect(self.add_docker_button_ui)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.docker_buttons_container = QVBoxLayout()
        layout.addLayout(self.docker_buttons_container)

        for button_config in self.docker_buttons_config.get("docker_buttons", []):
            self.add_docker_button_ui(button_config)

    def add_docker_button_ui(self, button_config=None):
        if not isinstance(button_config, dict):
            button_config = {
                "button_name": "",
                "button_width": 50,
                "button_icon": "",
                "docker_keywords": [],
                "description": "",
            }

        group_box = QGroupBox(f"Docker Button: {button_config.get('button_name', 'New Button')}")
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)
        fields = {}

        hl = QHBoxLayout()
        label = QLabel("Button Name:")
        edit = QLineEdit(button_config.get("button_name", ""))
        edit.setPlaceholderText("e.g., Tool, Layers, Brush")
        hl.addWidget(label)
        hl.addWidget(edit)
        group_layout.addLayout(hl)
        fields["button_name"] = edit
        edit.textChanged.connect(lambda text, gb=group_box: gb.setTitle(f"Docker Button: {text or 'New Button'}"))

        hl = QHBoxLayout()
        label = QLabel("Button Width:")
        edit = QLineEdit(str(button_config.get("button_width", 50)))
        edit.setFixedWidth(80)
        edit.setPlaceholderText("50")
        hl.addWidget(label)
        hl.addWidget(edit)
        hl.addStretch()
        group_layout.addLayout(hl)
        fields["button_width"] = edit

        hl = QHBoxLayout()
        label = QLabel("Button Icon:")
        edit = QLineEdit(button_config.get("button_icon", ""))
        edit.setPlaceholderText("e.g., brush_sets.png (optional)")
        hl.addWidget(label)
        hl.addWidget(edit)
        group_layout.addLayout(hl)
        fields["button_icon"] = edit

        hl = QHBoxLayout()
        label = QLabel("Docker Keywords:")
        keywords_list = button_config.get("docker_keywords", [])
        keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else ""
        edit = QLineEdit(keywords_str)
        edit.setPlaceholderText("e.g., tool, option (comma-separated)")
        hl.addWidget(label)
        hl.addWidget(edit)
        group_layout.addLayout(hl)
        fields["docker_keywords"] = edit

        hl = QHBoxLayout()
        label = QLabel("Description:")
        edit = QLineEdit(button_config.get("description", ""))
        edit.setPlaceholderText("e.g., Tool Options Docker")
        hl.addWidget(label)
        hl.addWidget(edit)
        group_layout.addLayout(hl)
        fields["description"] = edit

        remove_btn = QPushButton("Remove This Button")
        remove_btn.clicked.connect(lambda: self._remove_docker_button_ui(group_box, fields))
        group_layout.addWidget(remove_btn)

        self.docker_buttons_fields.append({"group_box": group_box, "fields": fields})
        self.docker_buttons_container.addWidget(group_box)

    def _remove_docker_button_ui(self, group_box, fields):
        for item in self.docker_buttons_fields:
            if item["group_box"] == group_box:
                self.docker_buttons_fields.remove(item)
                break
        group_box.setParent(None)
        group_box.deleteLater()

    def save(self):
        if self.quick_adjust_path and self.quick_adjust_fields:
            for key_tuple, edit in self.quick_adjust_fields.items():
                if len(key_tuple) == 1:
                    key = key_tuple[0]
                    if key == "blender_mode_list":
                        modes_str = edit.toPlainText().strip()
                        self.quick_adjust_config[key] = [
                            m.strip() for m in modes_str.split("\n") if m.strip()
                        ] if modes_str else []
                    elif isinstance(edit, QCheckBox):
                        self.quick_adjust_config[key] = edit.isChecked()
                    else:
                        self.quick_adjust_config[key] = edit.text()
                elif len(key_tuple) == 2:
                    section, key = key_tuple
                    if isinstance(edit, QCheckBox):
                        self.quick_adjust_config[section][key] = edit.isChecked()
                    else:
                        val = edit.text()
                        try:
                            val = int(val)
                        except Exception:
                            pass
                        self.quick_adjust_config[section][key] = val
                elif len(key_tuple) == 3:
                    section, subsection, key = key_tuple
                    if isinstance(edit, QCheckBox):
                        self.quick_adjust_config[section][subsection][key] = edit.isChecked()
                    elif isinstance(edit, QComboBox):
                        self.quick_adjust_config[section][subsection][key] = edit.currentText()
                    else:
                        self.quick_adjust_config[section][subsection][key] = edit.text()

            with open(self.quick_adjust_path, "w", encoding="utf-8") as f:
                json.dump(self.quick_adjust_config, f, indent=4)

        if self.docker_buttons_path and self.docker_buttons_fields:
            docker_buttons_list = []
            for item in self.docker_buttons_fields:
                fields = item["fields"]
                try:
                    width = int(fields["button_width"].text())
                except ValueError:
                    width = 50
                keywords_str = fields["docker_keywords"].text().strip()
                keywords_list = [kw.strip() for kw in keywords_str.split(",") if kw.strip()] if keywords_str else []
                docker_buttons_list.append({
                    "button_name": fields["button_name"].text(),
                    "button_icon": fields["button_icon"].text(),
                    "description": fields["description"].text(),
                    "button_width": width,
                    "docker_keywords": keywords_list,
                })
            with open(self.docker_buttons_path, "w", encoding="utf-8") as f:
                json.dump({"docker_buttons": docker_buttons_list}, f, indent=4)
