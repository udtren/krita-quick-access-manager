import json
import os
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QStackedWidget,
    QWidget,
    QScrollArea,
    QCheckBox,
)
from PyQt5.QtCore import Qt


class CommonConfigDialog(QDialog):
    """Dialog for editing common configuration settings"""

    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config_path = config_path
        self.resize(600, 400)

        self.fields = {}
        self.quick_adjust_fields = {}

        self.setup_ui()
        self.load_config()
        self.load_quick_adjust_config()
        self.setup_connections()

    def setup_ui(self):
        """Setup the UI elements with QStackedWidget"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create horizontal layout for tab list and content
        content_layout = QHBoxLayout()

        # Create tab list on the left
        self.tab_list = QListWidget()
        self.tab_list.addItem("Main")
        self.tab_list.addItem("Quick Adjust")
        self.tab_list.setMaximumWidth(150)
        self.tab_list.setCurrentRow(0)

        # Create stacked widget for content
        self.stacked_widget = QStackedWidget()

        # Create main config page
        self.main_page = self.create_main_page()
        self.stacked_widget.addWidget(self.main_page)

        # Create quick adjust config page
        self.quick_adjust_page = self.create_quick_adjust_page()
        self.stacked_widget.addWidget(self.quick_adjust_page)

        content_layout.addWidget(self.tab_list)
        content_layout.addWidget(self.stacked_widget, 1)

        main_layout.addLayout(content_layout)

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
                self.quick_adjust_fields[("layer_section", "opacity_slider", key)] = edit
            else:
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
                hlayout.addWidget(label)
                hlayout.addStretch()
                hlayout.addWidget(edit)
                self.quick_adjust_fields[("layer_section", "opacity_slider", key)] = edit

            layout.addLayout(hlayout)

        # Add fields for history sections
        for section_name in ["brush_history_section", "color_history_section"]:
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

        layout.addStretch()

    def setup_connections(self):
        """Setup button connections"""
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)
        self.tab_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)

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
                    # font_size
                    self.quick_adjust_config[key_tuple[0]] = edit.text()
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
                        self.quick_adjust_config[section][subsection][key] = edit.isChecked()
                    else:
                        val = edit.text()
                        self.quick_adjust_config[section][subsection][key] = val

            # Write quick adjust config to file
            with open(self.quick_adjust_path, "w", encoding="utf-8") as f:
                json.dump(self.quick_adjust_config, f, indent=4)

        self.accept()
