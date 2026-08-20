"""Per-item-type config dialogs: Action, Label, Brush Size, Brush Blend Mode,
Docker Toggle, Color, Script. Each asks for a small, item-type-specific set
of fields (name/text, font size/color, background color, plus an icon or
docker/action picker where relevant) and exposes the result via get_config().
"""

import os

from ...compat import (
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QIntValidator,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)
from ...infrastructure import DockerManager, get_default_icons_dir
from ...shared import ACTION_ITEM


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


class BrushBlendModeItemConfigDialog(QDialog):
    """Configure a Brush Blend Mode palette item - a 2x1 button that sets
    the active brush's blend mode to a Krita blend mode id (free text,
    e.g. "multiply") when clicked."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        self.bg_color = QColor(self.config.get("backgroundColor", "#263a3a"))
        self.font_color = QColor(self.config.get("fontColor", "#ffffff"))
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        self.setWindowTitle("Brush Blend Mode Config")
        self.resize(300, 180)
        self.setMinimumWidth(280)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Text:"))
        self.text_edit = QLineEdit()
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
        return {
            "text": self.text_edit.text().strip(),
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
