import json
import os
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QScrollArea,
    QCheckBox,
    QTextEdit,
    QKeySequenceEdit,
    QTabWidget,
)
from PyQt5.QtCore import Qt
from ..config.popup_loader import PopupConfigLoader


class CommonConfigDialog(QDialog):
    """Dialog for editing common configuration settings"""

    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config_path = config_path
        self.resize(600, 400)

        self.fields = {}
        self.quick_adjust_fields = {}
        self.popup_fields = {}
        self.popup_loader = PopupConfigLoader()

        self.setup_ui()
        self.load_config()
        self.load_quick_adjust_config()
        self.load_popup_config()
        self.setup_connections()

    def setup_ui(self):
        """Setup the UI elements with QTabWidget"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create and add main config page
        self.main_page = self.create_main_page()
        self.tab_widget.addTab(self.main_page, "Main")

        # Create and add quick adjust config page
        self.quick_adjust_page = self.create_quick_adjust_page()
        self.tab_widget.addTab(self.quick_adjust_page, "Quick Adjust")

        # Create and add popup config page
        self.popup_page = self.create_popup_page()
        self.tab_widget.addTab(self.popup_page, "Popup")

        main_layout.addWidget(self.tab_widget)

        # Add info message
        self.info_label = QLabel("Some changes require Krita restart to take effect")
        main_layout.addWidget(self.info_label)

        # Button layout
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

    def create_main_page(self):
        """Create the main configuration page"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.main_page_layout = QVBoxLayout()
        scroll_widget.setLayout(self.main_page_layout)
        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)
        return page

    def create_quick_adjust_page(self):
        """Create the quick adjust configuration page"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.quick_adjust_page_layout = QVBoxLayout()
        scroll_widget.setLayout(self.quick_adjust_page_layout)
        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)
        return page

    def create_popup_page(self):
        """Create the popup shortcuts configuration page"""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.popup_page_layout = QVBoxLayout()
        scroll_widget.setLayout(self.popup_page_layout)
        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)
        return page

    def load_config(self):
        """Load main configuration from file"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Create editable fields for color/font/layout in main page
        layout = self.main_page_layout

        for section in ["color", "font", "layout"]:
            group = self.config.get(section, {})
            layout.addWidget(QLabel(f"[{section}]"))

            for key, value in group.items():
                hlayout = QHBoxLayout()
                label = QLabel(key)
                label.setAlignment(Qt.AlignLeft)
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                layout.addLayout(hlayout)
                self.fields[(section, key)] = edit

        layout.addStretch()

    def load_quick_adjust_config(self):
        """Load quick adjust docker configuration from file"""
        # Get the quick_adjust_docker.json path
        config_dir = os.path.dirname(self.config_path)
        quick_adjust_path = os.path.join(config_dir, "quick_adjust_docker.json")

        if not os.path.exists(quick_adjust_path):
            self.quick_adjust_config = {}
            return

        with open(quick_adjust_path, "r", encoding="utf-8") as f:
            self.quick_adjust_config = json.load(f)

        self.quick_adjust_path = quick_adjust_path
        layout = self.quick_adjust_page_layout

        # Add fields for brush_section
        brush_section = self.quick_adjust_config.get("brush_section", {})
        layout.addWidget(QLabel("[brush_section]"))
        for slider_name in ["size_slider", "opacity_slider", "rotation_slider"]:
            slider = brush_section.get(slider_name, {})
            layout.addWidget(QLabel(f"  {slider_name}:"))

            for key, value in slider.items():
                hlayout = QHBoxLayout()
                label = QLabel(f"    {key}")
                label.setAlignment(Qt.AlignLeft)

                if isinstance(value, bool):
                    edit = QCheckBox()
                    edit.setChecked(value)
                    hlayout.addWidget(label)
                    hlayout.addStretch()
                    hlayout.addWidget(edit)
                    self.quick_adjust_fields[("brush_section", slider_name, key)] = edit
                else:
                    edit = QLineEdit(str(value))
                    edit.setFixedWidth(80)
                    edit.setAlignment(Qt.AlignRight)
                    hlayout.addWidget(label)
                    hlayout.addStretch()
                    hlayout.addWidget(edit)
                    self.quick_adjust_fields[("brush_section", slider_name, key)] = edit

                layout.addLayout(hlayout)

        # Add fields for layer_section
        layer_section = self.quick_adjust_config.get("layer_section", {})
        layout.addWidget(QLabel("[layer_section]"))
        opacity_slider = layer_section.get("opacity_slider", {})
        layout.addWidget(QLabel("  opacity_slider:"))

        for key, value in opacity_slider.items():
            hlayout = QHBoxLayout()
            label = QLabel(f"    {key}")
            label.setAlignment(Qt.AlignLeft)

            if isinstance(value, bool):
                edit = QCheckBox()
                edit.setChecked(value)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("layer_section", "opacity_slider", key)] = (
                    edit
                )
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("layer_section", "opacity_slider", key)] = (
                    edit
                )

            layout.addLayout(hlayout)

        # Add fields for history sections
        for section_name in ["color_history_section", "brush_history_section"]:
            section = self.quick_adjust_config.get(section_name, {})
            layout.addWidget(QLabel(f"[{section_name}]"))

            for key, value in section.items():
                hlayout = QHBoxLayout()
                label = QLabel(f"  {key}")
                label.setAlignment(Qt.AlignLeft)

                if isinstance(value, bool):
                    edit = QCheckBox()
                    edit.setChecked(value)
                    hlayout.addWidget(label)
                    hlayout.addStretch()
                    hlayout.addWidget(edit)
                    self.quick_adjust_fields[(section_name, key)] = edit
                else:
                    edit = QLineEdit(str(value))
                    edit.setFixedWidth(80)
                    edit.setAlignment(Qt.AlignRight)
                    hlayout.addWidget(label)
                    hlayout.addStretch()
                    hlayout.addWidget(edit)
                    self.quick_adjust_fields[(section_name, key)] = edit

                layout.addLayout(hlayout)

        # Add fields for status_bar_section
        status_bar = self.quick_adjust_config.get("status_bar_section", {})
        layout.addWidget(QLabel("[status_bar_section]"))

        for key, value in status_bar.items():
            hlayout = QHBoxLayout()
            label = QLabel(f"  {key}")
            label.setAlignment(Qt.AlignLeft)

            if isinstance(value, bool):
                edit = QCheckBox()
                edit.setChecked(value)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("status_bar_section", key)] = edit
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("status_bar_section", key)] = edit

            layout.addLayout(hlayout)

        # Add fields for docker_toggle_section
        docker_toggle = self.quick_adjust_config.get("docker_toggle_section", {})
        layout.addWidget(QLabel("[docker_toggle_section]"))

        for key, value in docker_toggle.items():
            hlayout = QHBoxLayout()
            label = QLabel(f"  {key}")
            label.setAlignment(Qt.AlignLeft)

            if isinstance(value, bool):
                edit = QCheckBox()
                edit.setChecked(value)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("docker_toggle_section", key)] = edit
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("docker_toggle_section", key)] = edit

            layout.addLayout(hlayout)

        # Add font_size field
        font_size = self.quick_adjust_config.get("font_size", "12px")
        layout.addWidget(QLabel("[General]"))
        hlayout = QHBoxLayout()
        label = QLabel("  font_size")
        label.setAlignment(Qt.AlignLeft)
        edit = QLineEdit(str(font_size))
        edit.setFixedWidth(80)
        edit.setAlignment(Qt.AlignRight)
        hlayout.addWidget(label)
        hlayout.addStretch()
        hlayout.addWidget(edit)
        layout.addLayout(hlayout)
        self.quick_adjust_fields[("font_size",)] = edit

        # Add blender_mode_list field
        blender_modes = self.quick_adjust_config.get("blender_mode_list", [])
        vlayout = QVBoxLayout()
        label = QLabel("  blender_mode_list (one per line)")
        label.setAlignment(Qt.AlignLeft)
        # Convert list to newline-separated string for editing
        blender_modes_str = "\n".join(blender_modes)
        edit = QTextEdit()
        edit.setPlainText(blender_modes_str)
        edit.setMinimumHeight(100)
        edit.setMaximumHeight(150)
        edit.setPlaceholderText("Enter blend modes, one per line")
        vlayout.addWidget(label)
        vlayout.addWidget(edit)
        layout.addLayout(vlayout)
        self.quick_adjust_fields[("blender_mode_list",)] = edit

        layout.addStretch()

    def load_popup_config(self):
        """Load popup shortcuts configuration"""
        layout = self.popup_page_layout

        layout.addWidget(QLabel("[Popup Shortcuts]"))
        layout.addWidget(
            QLabel(
                "Configure keyboard shortcuts for popup windows.\n"
                "Note: Changes require Krita restart to take effect."
            )
        )

        # Actions Popup Shortcut
        hlayout = QHBoxLayout()
        label = QLabel("Actions Popup Shortcut")
        label.setAlignment(Qt.AlignLeft)
        edit = QKeySequenceEdit()
        edit.setKeySequence(self.popup_loader.get_actions_popup_shortcut_string())
        edit.setMaximumWidth(150)
        hlayout.addWidget(label)
        hlayout.addStretch()
        hlayout.addWidget(edit)
        layout.addLayout(hlayout)
        self.popup_fields["actions_popup_shortcut"] = edit

        # Brush Sets Popup Shortcut
        hlayout = QHBoxLayout()
        label = QLabel("Brush Sets Popup Shortcut")
        label.setAlignment(Qt.AlignLeft)
        edit = QKeySequenceEdit()
        edit.setKeySequence(self.popup_loader.get_brush_sets_popup_shortcut_string())
        edit.setMaximumWidth(150)
        hlayout.addWidget(label)
        hlayout.addStretch()
        hlayout.addWidget(edit)
        layout.addLayout(hlayout)
        self.popup_fields["brush_sets_popup_shortcut"] = edit

        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("[Popup Appearance]"))

        # Brush Icon Size
        hlayout = QHBoxLayout()
        label = QLabel("Brush Icon Size")
        label.setAlignment(Qt.AlignLeft)
        edit = QLineEdit(str(self.popup_loader.get_brush_icon_size()))
        edit.setFixedWidth(80)
        edit.setAlignment(Qt.AlignRight)
        hlayout.addWidget(label)
        hlayout.addStretch()
        hlayout.addWidget(edit)
        layout.addLayout(hlayout)
        self.popup_fields["brush_icon_size"] = edit

        # Grid Label Width
        hlayout = QHBoxLayout()
        label = QLabel("Grid Label Width")
        label.setAlignment(Qt.AlignLeft)
        edit = QLineEdit(str(self.popup_loader.get_grid_label_width()))
        edit.setFixedWidth(80)
        edit.setAlignment(Qt.AlignRight)
        hlayout.addWidget(label)
        hlayout.addStretch()
        hlayout.addWidget(edit)
        layout.addLayout(hlayout)
        self.popup_fields["grid_label_width"] = edit

        layout.addStretch()

    def setup_connections(self):
        """Setup button connections"""
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)
        # QTabWidget handles tab switching automatically, no connection needed

    def save_and_close(self):
        """Save configuration and close dialog"""
        # Save main config edits
        for (section, key), edit in self.fields.items():
            val = edit.text()

            # Type conversion for layout section
            if section == "layout":
                try:
                    val = int(val)
                except Exception:
                    pass

            self.config[section][key] = val

        # Write main config to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

        # Save quick adjust config edits
        if hasattr(self, "quick_adjust_path") and self.quick_adjust_fields:
            for key_tuple, edit in self.quick_adjust_fields.items():
                if len(key_tuple) == 1:
                    # font_size or blender_mode_list
                    key = key_tuple[0]
                    if key == "blender_mode_list":
                        # Convert newline-separated string to list
                        modes_str = edit.toPlainText().strip()
                        if modes_str:
                            # Split by newline and strip whitespace from each mode
                            modes_list = [
                                mode.strip()
                                for mode in modes_str.split("\n")
                                if mode.strip()
                            ]
                            self.quick_adjust_config[key] = modes_list
                        else:
                            self.quick_adjust_config[key] = []
                    else:
                        # font_size or other single values
                        self.quick_adjust_config[key] = edit.text()
                elif len(key_tuple) == 2:
                    # history sections or status_bar
                    section, key = key_tuple
                    if isinstance(edit, QCheckBox):
                        self.quick_adjust_config[section][key] = edit.isChecked()
                    else:
                        val = edit.text()
                        # Try to convert to int
                        try:
                            val = int(val)
                        except:
                            pass
                        self.quick_adjust_config[section][key] = val
                elif len(key_tuple) == 3:
                    # brush_section or layer_section
                    section, subsection, key = key_tuple
                    if isinstance(edit, QCheckBox):
                        self.quick_adjust_config[section][subsection][
                            key
                        ] = edit.isChecked()
                    else:
                        val = edit.text()
                        self.quick_adjust_config[section][subsection][key] = val

            # Write quick adjust config to file
            with open(self.quick_adjust_path, "w", encoding="utf-8") as f:
                json.dump(self.quick_adjust_config, f, indent=4)

        # Save popup config edits
        if self.popup_fields:
            for key, edit in self.popup_fields.items():
                if key == "actions_popup_shortcut":
                    shortcut_str = edit.keySequence().toString()
                    self.popup_loader.set_actions_popup_shortcut(shortcut_str)
                elif key == "brush_sets_popup_shortcut":
                    shortcut_str = edit.keySequence().toString()
                    self.popup_loader.set_brush_sets_popup_shortcut(shortcut_str)
                elif key == "brush_icon_size":
                    try:
                        size = int(edit.text())
                        self.popup_loader.set_brush_icon_size(size)
                    except ValueError:
                        pass
                elif key == "grid_label_width":
                    try:
                        width = int(edit.text())
                        self.popup_loader.set_grid_label_width(width)
                    except ValueError:
                        pass

        self.accept()
