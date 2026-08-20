"""Action item configuration dialog for the remastered palette."""

import os
from uuid import uuid4

from krita import Krita  # type: ignore

from ..compat import (
    QApplication,
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QIcon,
    QIntValidator,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPainter,
    QPen,
    QPixmap,
    QPushButton,
    QRect,
    QRubberBand,
    QScrollArea,
    QSize,
    QSpinBox,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from ..gesture import is_gesture_enabled
from ..infrastructure import (
    AliasRepository,
    DockerManager,
    get_default_icons_dir,
    get_system_icons_dir,
)
from ..shared import (
    ACTION_ITEM,
    BRUSH_ITEM,
    BRUSH_SIZE_ITEM,
    COLOR_ITEM,
    COLOR_SWATCH_BORDER_COLOR,
    COLOR_SWATCH_BORDER_WIDTH,
    DOCKER_TOGGLE_ITEM,
    LABEL_ITEM,
    SCRIPT_ITEM,
    SEPARATOR_ITEM,
    SEPARATOR_ORIENTATION_VERTICAL,
    PaletteItem,
)


class ActionItemConfigDialog(QDialog):
    """Configure an Action palette item from plain config data."""

    def __init__(self, actions, config=None, parent=None, selected_action_id=None):
        super().__init__(parent)
        self._actions = actions
        self.config = dict(config or {})
        if selected_action_id:
            self.config["action_id"] = selected_action_id
        self.selected_action_id = selected_action_id
        self.bg_color = QColor(self.config.get("backgroundColor", "#3a263f"))
        self.font_color = QColor(self.config.get("fontColor", "#ffffff"))
        self.icon_path = self.config.get("icon_name", "")
        self.setup_ui()
        self.load_values()

    def normalized_item(self, item):
        if item.type == ACTION_ITEM and item.payload.get("icon_name"):
            return item.copy_with(col_span=1)
        return item

    def setup_ui(self):
        self.setWindowTitle("Action Button Config")
        self.resize(300, 220)
        self.setMinimumWidth(280)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        for action_id, action in sorted(self._actions.items()):
            text = action.text() if hasattr(action, "text") else action_id
            self.action_combo.addItem(f"{text} ({action_id})", action_id)
        layout.addWidget(self.action_combo)
        if self.selected_action_id:
            self.action_combo.setEnabled(False)

        layout.addWidget(QLabel("Button Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Font Size:"))
        self.font_size_edit = QLineEdit()
        layout.addWidget(self.font_size_edit)

        layout.addWidget(QLabel("Background Color:"))
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedHeight(24)
        self.bg_color_button.clicked.connect(self.pick_bg_color)
        layout.addWidget(self.bg_color_button)

        layout.addWidget(QLabel("Font Color:"))
        self.font_color_button = QPushButton()
        self.font_color_button.setFixedHeight(24)
        self.font_color_button.clicked.connect(self.pick_font_color)
        layout.addWidget(self.font_color_button)

        self.icon_button = QPushButton("Icon")
        self.icon_button.clicked.connect(self.pick_icon)
        layout.addWidget(self.icon_button)

        self.icon_path_label = QLabel("")
        self.icon_path_label.setWordWrap(True)
        self.icon_path_label.setStyleSheet("color: #b8b8b8; font-size: 11px;")
        layout.addWidget(self.icon_path_label)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_values(self):
        action_id = self.config.get("action_id")
        if action_id:
            index = self.action_combo.findData(action_id)
            if index >= 0:
                self.action_combo.setCurrentIndex(index)
        self.name_edit.setText(self.config.get("customName", ""))
        if not self.name_edit.text() and action_id:
            self.name_edit.setText(action_id)
        self.font_size_edit.setText(str(self.config.get("fontSize", "18")))
        self.update_icon_label()
        self.update_color_buttons()

    def pick_icon(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            get_default_icons_dir(),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if selected:
            self.icon_path = self._stored_icon_path(selected)
            self.update_icon_label()

    def update_icon_label(self):
        self.icon_path_label.setText(self.icon_path or "No icon selected")

    def _stored_icon_path(self, selected_path):
        default_dir = os.path.normcase(os.path.abspath(get_default_icons_dir()))
        selected_abs = os.path.abspath(selected_path)
        selected_dir = os.path.normcase(os.path.dirname(selected_abs))
        if selected_dir == default_dir:
            return os.path.basename(selected_abs)
        return selected_abs

    def pick_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color
            self.update_color_buttons()

    def pick_font_color(self):
        color = QColorDialog.getColor(self.font_color, self, "Select Font Color")
        if color.isValid():
            self.font_color = color
            self.update_color_buttons()

    def update_color_buttons(self):
        self.bg_color_button.setStyleSheet(
            f"background-color: {self.bg_color.name()}; border: 1px solid #888;"
        )
        self.bg_color_button.setText(self.bg_color.name())
        self.font_color_button.setStyleSheet(
            f"background-color: {self.font_color.name()}; border: 1px solid #888;"
        )
        self.font_color_button.setText(self.font_color.name())

    def get_config(self):
        return {
            "action_id": self.action_combo.currentData(),
            "customName": self.name_edit.text().strip(),
            "fontSize": self.font_size_edit.text().strip() or "18",
            "backgroundColor": self.bg_color.name(),
            "fontColor": self.font_color.name(),
            "icon_name": self.icon_path,
        }


class LabelItemConfigDialog(QDialog):
    """Configure a Label palette item."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        self.bg_color = QColor(self.config.get("backgroundColor", "#263746"))
        self.font_color = QColor(self.config.get("fontColor", "#4FC3F7"))
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setWindowTitle("Label Config")
        self.resize(300, 180)
        self.setMinimumWidth(280)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Label Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Font Size:"))
        self.font_size_edit = QLineEdit()
        layout.addWidget(self.font_size_edit)

        layout.addWidget(QLabel("Background Color:"))
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedHeight(24)
        self.bg_color_button.clicked.connect(self.pick_bg_color)
        layout.addWidget(self.bg_color_button)

        layout.addWidget(QLabel("Text Color:"))
        self.font_color_button = QPushButton()
        self.font_color_button.setFixedHeight(24)
        self.font_color_button.clicked.connect(self.pick_font_color)
        layout.addWidget(self.font_color_button)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_values(self):
        self.name_edit.setText(self.config.get("text", "Label"))
        self.font_size_edit.setText(str(self.config.get("fontSize", "18")))
        self.update_color_buttons()

    def pick_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color
            self.update_color_buttons()

    def pick_font_color(self):
        color = QColorDialog.getColor(self.font_color, self, "Select Text Color")
        if color.isValid():
            self.font_color = color
            self.update_color_buttons()

    def update_color_buttons(self):
        self.bg_color_button.setStyleSheet(
            f"background-color: {self.bg_color.name()}; border: 1px solid #888;"
        )
        self.bg_color_button.setText(self.bg_color.name())
        self.font_color_button.setStyleSheet(
            f"background-color: {self.font_color.name()}; border: 1px solid #888;"
        )
        self.font_color_button.setText(self.font_color.name())

    def get_config(self):
        return {
            "text": self.name_edit.text().strip() or "Label",
            "fontSize": self.font_size_edit.text().strip() or "18",
            "backgroundColor": self.bg_color.name(),
            "fontColor": self.font_color.name(),
        }


class BrushSizeItemConfigDialog(QDialog):
    """Configure a Brush Size palette item - a 1x1 button that sets the
    active brush's size to a fixed number when clicked."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        self.bg_color = QColor(self.config.get("backgroundColor", "#3a263f"))
        self.font_color = QColor(self.config.get("fontColor", "#ffffff"))
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setWindowTitle("Brush Size Config")
        self.resize(300, 180)
        self.setMinimumWidth(280)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Size (numbers only):"))
        self.text_edit = QLineEdit()
        # Digits only - this is a brush size, not free text like a Label.
        self.text_edit.setValidator(QIntValidator(1, 10000, self.text_edit))
        layout.addWidget(self.text_edit)

        layout.addWidget(QLabel("Font Size:"))
        self.font_size_edit = QLineEdit()
        layout.addWidget(self.font_size_edit)

        layout.addWidget(QLabel("Background Color:"))
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedHeight(24)
        self.bg_color_button.clicked.connect(self.pick_bg_color)
        layout.addWidget(self.bg_color_button)

        layout.addWidget(QLabel("Font Color:"))
        self.font_color_button = QPushButton()
        self.font_color_button.setFixedHeight(24)
        self.font_color_button.clicked.connect(self.pick_font_color)
        layout.addWidget(self.font_color_button)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_values(self):
        self.text_edit.setText(str(self.config.get("text", "")))
        self.font_size_edit.setText(str(self.config.get("fontSize", "18")))
        self.update_color_buttons()

    def pick_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color
            self.update_color_buttons()

    def pick_font_color(self):
        color = QColorDialog.getColor(self.font_color, self, "Select Font Color")
        if color.isValid():
            self.font_color = color
            self.update_color_buttons()

    def update_color_buttons(self):
        self.bg_color_button.setStyleSheet(
            f"background-color: {self.bg_color.name()}; border: 1px solid #888;"
        )
        self.bg_color_button.setText(self.bg_color.name())
        self.font_color_button.setStyleSheet(
            f"background-color: {self.font_color.name()}; border: 1px solid #888;"
        )
        self.font_color_button.setText(self.font_color.name())

    def get_config(self):
        # The validator already blocks non-digit input, but strip defensively
        # (e.g. an empty field on OK) rather than saving a blank size.
        digits = "".join(ch for ch in self.text_edit.text() if ch.isdigit())
        return {
            "text": digits or "1",
            "fontSize": self.font_size_edit.text().strip() or "18",
            "backgroundColor": self.bg_color.name(),
            "fontColor": self.font_color.name(),
        }


class DockerToggleItemConfigDialog(QDialog):
    """Configure a Docker Toggle palette item."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        self.dockers = DockerManager.get_dockers_dict() if DockerManager else {}
        self.icon_path = self.config.get("icon_name", "")
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setWindowTitle("Docker Toggle Config")
        self.resize(320, 220)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Docker:"))
        self.docker_combo = QComboBox()
        for docker_id, title in sorted(
            self.dockers.items(), key=lambda entry: entry[1].lower()
        ):
            self.docker_combo.addItem(f"{title} ({docker_id})", docker_id)
        layout.addWidget(self.docker_combo)

        layout.addWidget(QLabel("Button Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        self.icon_button = QPushButton("Icon")
        self.icon_button.clicked.connect(self.pick_icon)
        layout.addWidget(self.icon_button)

        self.icon_path_label = QLabel("")
        self.icon_path_label.setWordWrap(True)
        self.icon_path_label.setStyleSheet("color: #b8b8b8; font-size: 11px;")
        layout.addWidget(self.icon_path_label)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_values(self):
        docker_id = self.config.get("docker_id")
        if docker_id:
            index = self.docker_combo.findData(docker_id)
            if index >= 0:
                self.docker_combo.setCurrentIndex(index)
        self.name_edit.setText(self.config.get("customName", ""))
        self.update_icon_label()

    def pick_icon(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            get_default_icons_dir(),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if selected:
            self.icon_path = selected
            self.update_icon_label()

    def update_icon_label(self):
        self.icon_path_label.setText(self.icon_path or "No icon selected")

    def get_config(self):
        return {
            "docker_id": self.docker_combo.currentData(),
            "customName": self.name_edit.text().strip(),
            "icon_name": self.icon_path,
        }


class ColorItemConfigDialog(QDialog):
    """Configure a Color palette item that sets the foreground color."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        self.color = QColor(self.config.get("color", "#ffffff"))
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setWindowTitle("Color Swatch Config")
        self.resize(280, 150)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Color:"))
        self.color_button = QPushButton()
        self.color_button.setFixedHeight(28)
        self.color_button.clicked.connect(self.pick_color)
        layout.addWidget(self.color_button)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_values(self):
        self.update_color_button()

    def pick_color(self):
        color = QColorDialog.getColor(self.color, self, "Select Color")
        if color.isValid():
            self.color = color
            self.update_color_button()

    def update_color_button(self):
        self.color_button.setStyleSheet(
            f"background-color: {self.color.name()}; border: 1px solid #888;"
        )
        self.color_button.setText(self.color.name())

    def get_config(self):
        return {"color": self.color.name()}


class ScriptItemConfigDialog(QDialog):
    """Configure a Script palette item that runs a user-selected .py file."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        self.script_path = self.config.get("script_path", "")
        self.icon_path = self.config.get("icon_name", "")
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setWindowTitle("Script Item Config")
        self.resize(340, 240)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Button Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        self.script_button = QPushButton("Select Script (.py)")
        self.script_button.clicked.connect(self.pick_script)
        layout.addWidget(self.script_button)

        self.script_path_label = QLabel("")
        self.script_path_label.setWordWrap(True)
        self.script_path_label.setStyleSheet("color: #b8b8b8; font-size: 11px;")
        layout.addWidget(self.script_path_label)

        self.icon_button = QPushButton("Icon")
        self.icon_button.clicked.connect(self.pick_icon)
        layout.addWidget(self.icon_button)

        self.icon_path_label = QLabel("")
        self.icon_path_label.setWordWrap(True)
        self.icon_path_label.setStyleSheet("color: #b8b8b8; font-size: 11px;")
        layout.addWidget(self.icon_path_label)

        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.accept_if_valid)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_values(self):
        self.name_edit.setText(self.config.get("customName", ""))
        self.update_script_label()
        self.update_icon_label()

    def pick_script(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select Script",
            self.script_path or os.path.expanduser("~"),
            "Python Scripts (*.py)",
        )
        if selected:
            self.script_path = selected
            self.update_script_label()

    def update_script_label(self):
        self.script_path_label.setText(self.script_path or "No script selected")

    def pick_icon(self):
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select Icon",
            get_default_icons_dir(),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if selected:
            self.icon_path = selected
            self.update_icon_label()

    def update_icon_label(self):
        self.icon_path_label.setText(self.icon_path or "No icon selected")

    def accept_if_valid(self):
        if not self.script_path or not os.path.isfile(self.script_path):
            QMessageBox.warning(
                self, "No Script Selected", "Please select an existing .py file."
            )
            return
        self.accept()

    def get_config(self):
        return {
            "script_path": self.script_path,
            "customName": self.name_edit.text().strip(),
            "icon_name": self.icon_path,
        }


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
            QLabel("Temporary Brush Sets (key hold \u2192 switch brush):")
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


class GridEditCanvas(QWidget):
    """Grid background that supports rubber-band (marquee) multi-select."""

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog
        self.rubber_band = None
        self.origin = None
        self.grid_rows = 0
        self.grid_columns = 0

    def paintEvent(self, event):
        """Draw the cell guides.

        Cheaper than the QFrame-per-cell approach it replaces, which rebuilt
        rows x columns widgets on every drop.
        """
        super().paintEvent(event)
        if not self.grid_rows or not self.grid_columns:
            return
        cell = self.dialog.cell_size
        spacing = self.dialog.spacing
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#3f3f3f"), 1))
        painter.setBrush(Qt.NoBrush)
        for row in range(self.grid_rows):
            y = 4 + row * (cell + spacing)
            for col in range(self.grid_columns):
                x = 4 + col * (cell + spacing)
                painter.drawRect(x, y, cell - 1, cell - 1)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            if self.rubber_band is None:
                self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.origin is not None and self.rubber_band is not None:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.origin is not None and self.rubber_band is not None:
            selection_rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            self.origin = None
            additive = QApplication.keyboardModifiers() == Qt.ControlModifier
            self.dialog.select_items_in_rect(selection_rect, additive=additive)
            return
        super().mouseReleaseEvent(event)


# Width, in pixels, of the right-edge strip that starts a resize drag instead
# of a move drag on a Label/Separator button.
RESIZE_HANDLE_WIDTH = 8


class GridEditItemButton(QPushButton):
    """Grid edit item button that supports click selection, cell drag movement,
    and - for Label/Separator items only - a drag handle that resizes instead
    of moving the item: the right edge for width (col_span), or the bottom
    edge for height (row_span) on a vertical Separator, which grows downward
    instead of sideways."""

    def __init__(self, item, dialog):
        super().__init__(dialog.item_label(item))
        self.item = item
        self.dialog = dialog
        self.drag_start_global_pos = None
        self.drag_mode = None  # "move" or "resize"
        self.setCursor(Qt.SizeAllCursor)
        if self._resizable:
            self.setMouseTracking(True)

    @property
    def _resizable(self):
        return self.dialog.is_resizable(self.item)

    @property
    def _resize_axis(self):
        return self.dialog.resize_axis(self.item) if self._resizable else None

    def _on_resize_handle(self, pos):
        if not self._resizable:
            return False
        if self._resize_axis == "row":
            return pos.y() >= self.height() - RESIZE_HANDLE_WIDTH
        return pos.x() >= self.width() - RESIZE_HANDLE_WIDTH

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._resizable:
            return
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 110), 1))
        if self._resize_axis == "row":
            y = self.height() - RESIZE_HANDLE_WIDTH // 2
            painter.drawLine(6, y, self.width() - 6, y)
        else:
            x = self.width() - RESIZE_HANDLE_WIDTH // 2
            painter.drawLine(x, 6, x, self.height() - 6)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_global_pos = event.globalPos()
            self.drag_mode = "resize" if self._on_resize_handle(event.pos()) else "move"
        elif event.button() == Qt.RightButton:
            self.dialog.show_item_context_menu(self.item, event.globalPos())
            return
        super().mousePressEvent(event)

    def _resize_delta(self, event):
        """The along-axis delta (in cells) for the resize currently in progress."""
        dx = event.globalPos().x() - self.drag_start_global_pos.x()
        dy = event.globalPos().y() - self.drag_start_global_pos.y()
        span = dy if self._resize_axis == "row" else dx
        return int(round(span / float(self.dialog.cell_size)))

    def mouseMoveEvent(self, event):
        if self.drag_start_global_pos is not None and event.buttons() & Qt.LeftButton:
            if self.drag_mode == "resize":
                delta = self._resize_delta(event)
                if delta:
                    kwargs = (
                        {"row_delta": delta}
                        if self._resize_axis == "row"
                        else {"col_delta": delta}
                    )
                    self.dialog.show_resize_highlight(self.item, **kwargs)
                else:
                    self.dialog.hide_drop_highlight()
            else:
                dx = event.globalPos().x() - self.drag_start_global_pos.x()
                dy = event.globalPos().y() - self.drag_start_global_pos.y()
                col_delta = int(round(dx / float(self.dialog.cell_size)))
                row_delta = int(round(dy / float(self.dialog.cell_size)))
                if col_delta or row_delta:
                    self.dialog.show_drop_highlight(self.item, row_delta, col_delta)
                else:
                    self.dialog.hide_drop_highlight()
        elif self._resizable:
            if self._on_resize_handle(event.pos()):
                cursor = Qt.SizeVerCursor if self._resize_axis == "row" else Qt.SizeHorCursor
            else:
                cursor = Qt.SizeAllCursor
            self.setCursor(cursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dialog.hide_drop_highlight()
        if event.button() == Qt.LeftButton and self.drag_start_global_pos is not None:
            if self.drag_mode == "resize":
                delta = self._resize_delta(event)
                if delta:
                    self.dialog.ensure_selected_for_drag(self.item.id)
                    if self._resize_axis == "row":
                        self.dialog.resize_selected(delta, 0)
                    else:
                        self.dialog.resize_selected(0, delta)
                self.drag_start_global_pos = None
                self.drag_mode = None
                return
            dx = event.globalPos().x() - self.drag_start_global_pos.x()
            dy = event.globalPos().y() - self.drag_start_global_pos.y()
            col_delta = int(round(dx / float(self.dialog.cell_size)))
            row_delta = int(round(dy / float(self.dialog.cell_size)))
            if col_delta or row_delta:
                self.dialog.ensure_selected_for_drag(self.item.id)
                self.dialog.move_selected(row_delta, col_delta)
                self.drag_start_global_pos = None
                self.drag_mode = None
                return
        self.drag_start_global_pos = None
        self.drag_mode = None
        super().mouseReleaseEvent(event)


class GridEditDialog(QDialog):
    """Edit every tab's grid in a separate dialog without auto-compacting on save."""

    def __init__(self, tabs, active_tab_id=None, parent=None):
        super().__init__(parent)
        self.cell_size = 42
        self.spacing = 4
        self.visible_rows = 10
        self.saved_tabs = None
        # Read once for the lifetime of the dialog: rebuild_grid() runs on every
        # drop and would otherwise re-read the alias config once per item.
        self._alias_data = AliasRepository().load()

        self.tab_order = [tab.id for tab in tabs]
        self.tab_names = {tab.id: tab.name for tab in tabs}
        self.tab_state = {}
        for tab in tabs:
            grid = tab.grids[0] if tab.grids else None
            items = [
                self.normalized_item(PaletteItem.from_dict(item.to_dict()))
                for item in (grid.items if grid else [])
            ]
            self.tab_state[tab.id] = {
                "columns": int(grid.columns) if grid else 8,
                "items": items,
                "selected_ids": set(),
                "history": [],
                "item_widgets": {},
                "drop_highlight": None,
                "canvas": None,
            }

        # Current-tab context, swapped by _load_tab_state/_save_current_tab_state.
        self.current_tab_id = None
        self.columns = 8
        self.items = []
        self.selected_ids = set()
        self.history = []
        self.item_widgets = {}
        self.drop_highlight = None
        self.grid_host = None
        # "row" or "col" - which span the current selection's Wider/Narrower
        # click resizes; set by update_resize_controls().
        self._resize_axis_state = None

        self.setup_ui()

        initial_tab_id = (
            active_tab_id
            if active_tab_id in self.tab_state
            else (self.tab_order[0] if self.tab_order else None)
        )
        for tab_id in self.tab_order:
            self._load_tab_state(tab_id)
            self.rebuild_grid()
            self._save_current_tab_state()
        if initial_tab_id is not None:
            self._load_tab_state(initial_tab_id)
            self.tab_widget.setCurrentIndex(self.tab_order.index(initial_tab_id))
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def alias_entry(self, category, item_id):
        return self._alias_data.get(category, {}).get(item_id, {})

    def normalized_item(self, item):
        if item.type == ACTION_ITEM:
            alias = self.alias_entry("actions", item.payload.get("action_id", ""))
            if alias.get("icon_name"):
                return item.copy_with(col_span=1)
        return item

    def setup_ui(self):
        self.setWindowTitle("Grid Edit")
        self.resize(720, 520)
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        self.undo_btn = QPushButton()
        undo_icon_path = os.path.join(get_system_icons_dir(), "undo.png")
        if os.path.exists(undo_icon_path):
            self.undo_btn.setIcon(QIcon(undo_icon_path))
            self.undo_btn.setIconSize(QSize(18, 18))
        else:
            self.undo_btn.setText("Undo")
        self.undo_btn.setToolTip("Undo last move/resize")
        self.undo_btn.setEnabled(False)
        self.undo_btn.setFixedHeight(24)
        self.undo_btn.clicked.connect(self.undo)
        control_layout.addWidget(self.undo_btn)

        self.wider_btn = QPushButton("Wider")
        self.narrower_btn = QPushButton("Narrower")

        self.wider_btn.clicked.connect(lambda: self.grow_selected(1))
        self.narrower_btn.clicked.connect(lambda: self.grow_selected(-1))

        for button in (
            self.wider_btn,
            self.narrower_btn,
        ):
            button.setFixedHeight(24)
            control_layout.addWidget(button)
        control_layout.addStretch(1)
        layout.addLayout(control_layout)

        self.tab_widget = QTabWidget()
        for tab_id in self.tab_order:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            canvas = GridEditCanvas(self)
            scroll.setWidget(canvas)
            self.tab_state[tab_id]["canvas"] = canvas
            self.tab_widget.addTab(scroll, self.tab_names[tab_id])
        layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.accept_save)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _save_current_tab_state(self):
        if self.current_tab_id is None:
            return
        state = self.tab_state[self.current_tab_id]
        state["items"] = self.items
        state["selected_ids"] = self.selected_ids
        state["history"] = self.history
        state["item_widgets"] = self.item_widgets
        state["drop_highlight"] = self.drop_highlight

    def _load_tab_state(self, tab_id):
        self.current_tab_id = tab_id
        state = self.tab_state[tab_id]
        self.columns = state["columns"]
        self.items = state["items"]
        self.selected_ids = state["selected_ids"]
        self.history = state["history"]
        self.item_widgets = state["item_widgets"]
        self.drop_highlight = state["drop_highlight"]
        self.grid_host = state["canvas"]
        self.undo_btn.setEnabled(bool(self.history))
        self.update_selection_styles()

    def _on_tab_changed(self, index):
        if index < 0 or index >= len(self.tab_order):
            return
        tab_id = self.tab_order[index]
        if tab_id == self.current_tab_id:
            return
        self._save_current_tab_state()
        self._load_tab_state(tab_id)

    def _rebuild_tab(self, tab_id):
        """Rebuild a tab's canvas immediately, even if it isn't the one currently shown."""
        previous_tab_id = self.current_tab_id
        if previous_tab_id != tab_id:
            self._save_current_tab_state()
        self._load_tab_state(tab_id)
        self.rebuild_grid()
        self._save_current_tab_state()
        if previous_tab_id is not None and previous_tab_id != tab_id:
            self._load_tab_state(previous_tab_id)

    def rebuild_grid(self):
        for child in self.grid_host.findChildren(QWidget):
            child.deleteLater()
        self.item_widgets = {}
        self.drop_highlight = None
        self.grid_host.rubber_band = None
        self.grid_host.origin = None
        spacing = self.spacing
        max_bottom = max([item.bottom for item in self.items], default=0)
        rows = max(self.visible_rows, max_bottom + 2)
        width = self.columns * self.cell_size + max(0, self.columns - 1) * spacing + 8
        height = rows * self.cell_size + max(0, rows - 1) * spacing + 8
        self.grid_host.setMinimumSize(width, height)
        self.grid_host.grid_rows = rows
        self.grid_host.grid_columns = self.columns
        self.grid_host.update()
        for item in sorted(
            self.items, key=lambda entry: (entry.row, entry.col, entry.id)
        ):
            widget = self.create_item_widget(item)
            self.item_widgets[item.id] = widget
            widget.setParent(self.grid_host)
            x, y, item_width, item_height = self.item_geometry(item, spacing)
            widget.setGeometry(x, y, item_width, item_height)
            widget.raise_()
            widget.show()
        self.update_selection_styles()

    def item_geometry(self, item, spacing):
        x = 4 + item.col * (self.cell_size + spacing)
        y = 4 + item.row * (self.cell_size + spacing)
        width = item.col_span * self.cell_size + max(0, item.col_span - 1) * spacing
        height = item.row_span * self.cell_size + max(0, item.row_span - 1) * spacing
        return x, y, width, height

    def show_drop_highlight(self, item, row_delta, col_delta):
        """Outline the cell(s) the dragged item would land on."""
        target_row = max(0, item.row + row_delta)
        target_col = max(0, min(item.col + col_delta, self.columns - item.col_span))
        target = item.copy_with(row=target_row, col=target_col)
        x, y, width, height = self.item_geometry(target, self.spacing)
        if self.drop_highlight is None:
            self.drop_highlight = QFrame(self.grid_host)
            self.drop_highlight.setStyleSheet(
                "QFrame { border: 2px solid #4FC3F7; background-color: rgba(79, 195, 247, 60); border-radius: 3px; }"
            )
        self.drop_highlight.setGeometry(x, y, width, height)
        self.drop_highlight.raise_()
        self.drop_highlight.show()

    def show_resize_highlight(self, item, row_delta=0, col_delta=0):
        """Outline the size a Label/Separator's edge drag would apply -
        col_delta for the right-edge (width) handle, row_delta for the
        bottom-edge (height) handle a vertical Separator uses instead."""
        target_row_span = max(1, item.row_span + row_delta)
        target_col_span = max(
            1, min(self.columns - item.col, item.col_span + col_delta)
        )
        target = item.copy_with(row_span=target_row_span, col_span=target_col_span)
        x, y, width, height = self.item_geometry(target, self.spacing)
        if self.drop_highlight is None:
            self.drop_highlight = QFrame(self.grid_host)
            self.drop_highlight.setStyleSheet(
                "QFrame { border: 2px solid #4FC3F7; background-color: rgba(79, 195, 247, 60); border-radius: 3px; }"
            )
        self.drop_highlight.setGeometry(x, y, width, height)
        self.drop_highlight.raise_()
        self.drop_highlight.show()

    def hide_drop_highlight(self):
        if self.drop_highlight is not None:
            self.drop_highlight.hide()

    def create_item_widget(self, item):
        button = GridEditItemButton(item, self)
        button.setMinimumSize(self.cell_size, 36)
        if (
            item.type
            in (
                BRUSH_ITEM,
                ACTION_ITEM,
                DOCKER_TOGGLE_ITEM,
                COLOR_ITEM,
                SCRIPT_ITEM,
                BRUSH_SIZE_ITEM,
            )
            and item.col_span == 1
        ):
            button.setFixedSize(self.cell_size, self.cell_size)
        self.apply_item_icon(button, item)
        button.clicked.connect(
            lambda checked=False, item_id=item.id: self.toggle_selection(item_id)
        )
        return button

    def apply_item_icon(self, button, item):
        if item.type == BRUSH_ITEM:
            brush_name = item.payload.get("brush_name", "")
            try:
                preset = Krita.instance().resources("preset").get(brush_name)
                image = preset.image() if preset else None
                if image:
                    pixmap = QPixmap.fromImage(image)
                    if not pixmap.isNull():
                        button.setIcon(QIcon(pixmap))
                        button.setIconSize(QSize(34, 34))
                        button.setText("")
                        return
            except Exception:
                pass
        elif item.type == ACTION_ITEM:
            icon_name = self.alias_entry(
                "actions", item.payload.get("action_id", "")
            ).get("icon_name")
            icon_path = self.resolve_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setText("")
        elif item.type == DOCKER_TOGGLE_ITEM:
            icon_name = self.alias_entry(
                "dockers", item.payload.get("docker_id", "")
            ).get("icon_name")
            icon_path = self.resolve_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setText("")
        elif item.type == SCRIPT_ITEM:
            icon_name = item.payload.get("icon_name")
            icon_path = self.resolve_icon_path(icon_name)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setText("")
        elif item.type == COLOR_ITEM:
            button.setText("")

    def resolve_icon_path(self, icon_name):
        if not icon_name:
            return None
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
        icon_path = os.path.join(get_default_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            return icon_path
        return None

    def item_label(self, item):
        if item.type == BRUSH_ITEM:
            return "Brush"
        if item.type == ACTION_ITEM:
            action_id = item.payload.get("action_id", "Action")
            return self.alias_entry("actions", action_id).get("custom_name") or action_id
        if item.type == LABEL_ITEM:
            return item.payload.get("text", "Label")
        if item.type == SEPARATOR_ITEM:
            vertical = item.payload.get("orientation") == SEPARATOR_ORIENTATION_VERTICAL
            return "|" if vertical else "---"
        if item.type == DOCKER_TOGGLE_ITEM:
            docker_id = item.payload.get("docker_id", "Docker")
            return self.alias_entry("dockers", docker_id).get("custom_name") or docker_id
        if item.type == COLOR_ITEM:
            return ""
        if item.type == SCRIPT_ITEM:
            return item.payload.get("customName") or "Script"
        if item.type == BRUSH_SIZE_ITEM:
            return item.payload.get("text", "")
        return item.type

    def ensure_selected_for_drag(self, item_id):
        if item_id not in self.selected_ids:
            self.selected_ids = {item_id}
            self.update_selection_styles()

    def select_items_in_rect(self, rect, additive=False):
        """Select every item whose cell footprint intersects the marquee rect."""
        hit_ids = set()
        for item in self.items:
            x, y, width, height = self.item_geometry(item, self.spacing)
            if rect.intersects(QRect(x, y, width, height)):
                hit_ids.add(item.id)
        if additive:
            self.selected_ids |= hit_ids
        else:
            self.selected_ids = hit_ids
        self.update_selection_styles()

    def toggle_selection(self, item_id):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if item_id in self.selected_ids:
                self.selected_ids.remove(item_id)
            else:
                self.selected_ids.add(item_id)
        else:
            self.selected_ids = {item_id}
        self.update_selection_styles()

    def update_selection_styles(self):
        for item in self.items:
            widget = self.item_widgets.get(item.id)
            if not widget:
                continue
            widget.setStyleSheet(self.item_style(item, item.id in self.selected_ids))
        self.update_resize_controls()

    def item_style(self, item, selected):
        colors = {
            BRUSH_ITEM: ("#2f2f2f", "#555555"),
            ACTION_ITEM: ("#3a263f", "#6b4a73"),
            LABEL_ITEM: (
                item.payload.get("backgroundColor", "#263746"),
                item.payload.get("fontColor", "#4FC3F7"),
            ),
            SEPARATOR_ITEM: ("#303030", "#777777"),
            DOCKER_TOGGLE_ITEM: ("#263a2f", "#4a8b6b"),
            COLOR_ITEM: (
                item.payload.get("color", "#ffffff"),
                COLOR_SWATCH_BORDER_COLOR,
            ),
            SCRIPT_ITEM: ("#2f2a1f", "#8b7a4a"),
            BRUSH_SIZE_ITEM: (
                item.payload.get("backgroundColor", "#3a263f"),
                "#6b4a73",
            ),
        }
        background, border = colors.get(item.type, ("#333333", "#555555"))
        if item.type == COLOR_ITEM and not selected:
            border_width = COLOR_SWATCH_BORDER_WIDTH
        else:
            border_width = 2 if selected else 1
        border_color = "#4FC3F7" if selected else border
        custom_text_color_types = (LABEL_ITEM, BRUSH_SIZE_ITEM)
        text_color = (
            item.payload.get("fontColor", "#ffffff")
            if item.type in custom_text_color_types
            else "#ffffff"
        )
        font_size = (
            item.payload.get("fontSize", "18")
            if item.type in custom_text_color_types
            else "18"
        )
        return (
            f"QPushButton {{ background: {background}; color: {text_color}; font-size: {font_size}px; border: {border_width}px solid {border_color}; "
            "border-radius: 3px; padding: 0px 4px; }"
        )

    def resize_axis(self, item):
        """"row" for a vertical Separator (it grows/shrinks by row_span);
        "col" for everything else resizable (Label, horizontal Separator,
        Action)."""
        if (
            item.type == SEPARATOR_ITEM
            and item.payload.get("orientation") == SEPARATOR_ORIENTATION_VERTICAL
        ):
            return "row"
        return "col"

    def is_resizable(self, item):
        """Label/Separator resize freely; an Action item resizes only when it
        has no alias icon - an icon-mode Action is pinned to col_span=1 by
        PaletteController._action_col_span() on every load, so letting it
        widen here would just get silently reverted."""
        if item.type in (LABEL_ITEM, SEPARATOR_ITEM):
            return True
        if item.type == ACTION_ITEM:
            action_id = item.payload.get("action_id", "")
            return not self.alias_entry("actions", action_id).get("icon_name")
        return False

    def update_resize_controls(self):
        selected = self.selected_items()
        resizable = [item for item in selected if self.is_resizable(item)]
        axes = {self.resize_axis(item) for item in resizable}
        # Mixed row/col selections (e.g. a Label plus a vertical Separator)
        # have no single delta that means the same thing for both, so the
        # buttons stay disabled until the selection resizes along one axis.
        can_resize = bool(selected) and len(resizable) == len(selected) and len(axes) == 1
        self._resize_axis_state = next(iter(axes)) if can_resize else None
        if self._resize_axis_state == "row":
            self.wider_btn.setText("Taller")
            self.narrower_btn.setText("Shorter")
        else:
            self.wider_btn.setText("Wider")
            self.narrower_btn.setText("Narrower")
        self.wider_btn.setEnabled(can_resize)
        self.narrower_btn.setEnabled(can_resize)
        tooltip = "Resize selected Label/Separator items only"
        self.wider_btn.setToolTip(tooltip)
        self.narrower_btn.setToolTip(tooltip)

    def grow_selected(self, delta):
        if self._resize_axis_state == "row":
            self.resize_selected(delta, 0)
        else:
            self.resize_selected(0, delta)

    def selected_items(self):
        return [item for item in self.items if item.id in self.selected_ids]

    def show_item_context_menu(self, item, global_pos):
        if item.id not in self.selected_ids:
            self.selected_ids = {item.id}
            self.update_selection_styles()
        if not self.selected_items():
            return
        other_tab_ids = [tid for tid in self.tab_order if tid != self.current_tab_id]
        menu = QMenu(self)
        copy_menu = menu.addMenu("Copy to Tab")
        move_menu = menu.addMenu("Move to Tab")
        copy_menu.setEnabled(bool(other_tab_ids))
        move_menu.setEnabled(bool(other_tab_ids))
        for tab_id in other_tab_ids:
            name = self.tab_names.get(tab_id, tab_id)
            copy_action = copy_menu.addAction(name)
            copy_action.triggered.connect(
                lambda checked=False, tid=tab_id: self.copy_selected_to_tab(tid)
            )
            move_action = move_menu.addAction(name)
            move_action.triggered.connect(
                lambda checked=False, tid=tab_id: self.move_selected_to_tab(tid)
            )
        menu.exec(global_pos)

    def _new_item_id(self, item_type):
        return f"{item_type}-{uuid4().hex[:12]}"

    def copy_selected_to_tab(self, target_tab_id):
        selected = self.selected_items()
        if not selected or target_tab_id == self.current_tab_id:
            return
        self._push_history()
        clones = [item.copy_with(id=self._new_item_id(item.type)) for item in selected]
        self._append_items_to_tab(target_tab_id, clones)

    def move_selected_to_tab(self, target_tab_id):
        selected = self.selected_items()
        if not selected or target_tab_id == self.current_tab_id:
            return
        self._push_history()
        moved_ids = {item.id for item in selected}
        clones = [item.copy_with(id=self._new_item_id(item.type)) for item in selected]
        self.items = [item for item in self.items if item.id not in moved_ids]
        self.selected_ids -= moved_ids
        self.rebuild_grid()
        self._append_items_to_tab(target_tab_id, clones)

    def _append_items_to_tab(self, target_tab_id, new_items):
        """Place copied/moved items below the target tab's last existing row, same as a new item add."""
        if not new_items:
            return
        target_state = self.tab_state[target_tab_id]
        target_items = target_state["items"]
        target_columns = target_state["columns"]
        base_row = max((it.bottom for it in target_items), default=0)
        min_row = min(it.row for it in new_items)
        min_col = min(it.col for it in new_items)
        placed = []
        for it in new_items:
            new_col = min(
                max(0, it.col - min_col), max(0, target_columns - it.col_span)
            )
            placed.append(it.copy_with(row=base_row + (it.row - min_row), col=new_col))
        target_state["items"] = target_items + placed
        target_state["selected_ids"] = {it.id for it in placed}
        self._rebuild_tab(target_tab_id)

    MAX_HISTORY = 20

    def _push_history(self):
        snapshot = [item.copy_with() for item in self.items]
        self.history.append(snapshot)
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)
        self.undo_btn.setEnabled(True)

    def undo(self):
        if not self.history:
            return
        self.items = self.history.pop()
        self.selected_ids &= {item.id for item in self.items}
        self.undo_btn.setEnabled(bool(self.history))
        self.rebuild_grid()

    def move_selected(self, row_delta, col_delta):
        if not self.selected_ids:
            return
        selected = self.selected_items()
        min_row = min(item.row for item in selected)
        min_col = min(item.col for item in selected)
        row_delta = max(row_delta, -min_row)
        col_delta = max(col_delta, -min_col)
        if row_delta == 0 and col_delta == 0:
            return
        self._push_history()
        moved_selected = []
        for item in selected:
            moved_selected.append(
                item.copy_with(row=item.row + row_delta, col=item.col + col_delta)
            )
        self.items = self.place_group_with_push(moved_selected)
        self.rebuild_grid()

    def place_group_with_push(self, active_items):
        active_ids = {item.id for item in active_items}
        placed = sorted(active_items, key=lambda item: (item.row, item.col, item.id))
        for item in self.sorted_items(
            [item for item in self.items if item.id not in active_ids]
        ):
            candidate = item.copy_with(row=max(0, item.row), col=max(0, item.col))
            if candidate.col_span > self.columns:
                placed.append(candidate)
                continue
            if self.needs_reposition(candidate, placed):
                candidate = self.first_free_position(candidate, placed)
            placed.append(candidate)
        return placed

    def first_free_position(self, item, placed):
        # An item wider than the grid can never satisfy the column check below,
        # so leave it where it is instead of scanning forever.
        if item.col_span > self.columns:
            return item.copy_with(row=max(0, item.row), col=0)
        cursor = self.linear_index(item.row, item.col)
        while True:
            row = cursor // self.columns
            col = cursor % self.columns
            if col + item.col_span <= self.columns:
                candidate = item.copy_with(row=row, col=col)
                if not self.needs_reposition(candidate, placed):
                    return candidate
            cursor += 1

    def needs_reposition(self, item, placed):
        if item.col + item.col_span > self.columns:
            return True
        return any(self.items_overlap(item, other) for other in placed)

    def items_overlap(self, item, other):
        return not (
            item.right <= other.col
            or other.right <= item.col
            or item.bottom <= other.row
            or other.bottom <= item.row
        )

    def sorted_items(self, items):
        return sorted(
            items, key=lambda item: (self.linear_index(item.row, item.col), item.id)
        )

    def linear_index(self, row, col):
        return max(0, int(row)) * self.columns + max(0, int(col))

    def resize_selected(self, row_delta, col_delta):
        selected = self.selected_items()
        if not selected or any(not self.is_resizable(item) for item in selected):
            return
        self._push_history()
        resized = []
        for item in selected:
            resized.append(
                item.copy_with(
                    row_span=max(1, item.row_span + row_delta),
                    # Never let an item grow past the grid width - a wider item
                    # can never be placed and would stall the layout pass.
                    col_span=max(1, min(self.columns, item.col_span + col_delta)),
                )
            )
        self.items = self.place_group_with_push(resized)
        self.rebuild_grid()

    def accept_save(self):
        self._save_current_tab_state()
        self.saved_tabs = {
            tab_id: [PaletteItem.from_dict(item.to_dict()) for item in state["items"]]
            for tab_id, state in self.tab_state.items()
        }
        self.accept()
