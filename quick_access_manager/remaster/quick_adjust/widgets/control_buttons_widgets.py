import os

from krita import Krita  # type: ignore

from ...compat import (
    QFrame,
    QIcon,
    QLabel,
    QPixmap,
    QPushButton,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from ...gesture import (
    is_gesture_filter_paused,
    pause_gesture_event_filter,
    resume_gesture_event_filter,
)
from ...infrastructure import get_quick_adjust_icons_dir
from ..floating_widgets.tool_options import FloatToolOptions
from ..settings import (
    is_tool_options_enabled,
    is_tool_options_start_visible,
    set_tool_options_start_visible,
)


class ControlButtonWidget(QWidget):
    """Status/toggle button column: Tool Options floating widget, erase mode,
    preserve alpha, selection status, and gesture pause/resume.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_dir = get_quick_adjust_icons_dir()

        self.is_selected = False
        self.is_gesture_paused = False
        self.is_preserve_alpha = False
        self.is_erase_mode = False
        self.float_tool_options = None

        self.init_ui()
        self.update_status()

        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignTop)

        application = Krita.instance()
        app_notifier = application.notifier()
        app_notifier.windowCreated.connect(self.enableToolOptionsExtension)

        self.tool_options_toggle_btn = QPushButton()
        self.tool_options_toggle_btn.setFixedSize(16, 16)
        self.tool_options_toggle_btn.setToolTip("Toggle Tool Options")
        self.tool_options_toggle_btn.setIcon(
            QIcon(os.path.join(self.icon_dir, "tool_options_on.png"))
        )
        self.tool_options_toggle_btn.setCheckable(True)
        self.tool_options_toggle_btn.setChecked(False)
        self.tool_options_toggle_btn.clicked.connect(
            self.toggle_tool_options_visibility
        )

        self.preserve_alpha_label = QLabel()
        self.preserve_alpha_label.setFixedSize(16, 16)
        self.preserve_alpha_label.setScaledContents(True)
        self.preserve_alpha_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "preserve_alpha_off.png"))
        )
        self.preserve_alpha_label.setToolTip("Preserve Alpha: Off")
        self.preserve_alpha_label.setCursor(Qt.PointingHandCursor)
        self.preserve_alpha_label.mousePressEvent = self.toggle_preserve_alpha

        self.erase_mode_label = QLabel()
        self.erase_mode_label.setFixedSize(16, 16)
        self.erase_mode_label.setScaledContents(True)
        self.erase_mode_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "erase_mode_off.png"))
        )
        self.erase_mode_label.setToolTip("Erase Mode: Off")
        self.erase_mode_label.setCursor(Qt.PointingHandCursor)
        self.erase_mode_label.mousePressEvent = self.toggle_erase_mode

        self.selection_info_label = QLabel()
        self.selection_info_label.setFixedSize(16, 16)
        self.selection_info_label.setScaledContents(True)
        self.selection_info_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "selection_off.png"))
        )
        self.selection_info_label.setToolTip("Selection: Off")

        self.gesture_status_label = QLabel()
        self.gesture_status_label.setFixedSize(16, 16)
        self.gesture_status_label.setScaledContents(True)
        self.gesture_status_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "gesture_on.png"))
        )
        self.gesture_status_label.setToolTip("Gesture: On")
        self.gesture_status_label.setCursor(Qt.PointingHandCursor)
        self.gesture_status_label.mousePressEvent = self.toggle_gesture_status

        layout.addWidget(self.tool_options_toggle_btn)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.erase_mode_label)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.preserve_alpha_label)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.selection_info_label)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.gesture_status_label)
        layout.addStretch()

        self.setLayout(layout)

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #3a3a3a; margin: 2px 8px; }")
        return separator

    def update_status(self):
        preserve_alpha = self.get_preserve_alpha_status()
        if preserve_alpha != self.is_preserve_alpha:
            self.is_preserve_alpha = preserve_alpha
            icon = (
                "preserve_alpha_on.png" if preserve_alpha else "preserve_alpha_off.png"
            )
            tooltip = "Preserve Alpha: On" if preserve_alpha else "Preserve Alpha: Off"
            self.preserve_alpha_label.setToolTip(tooltip)
            self.preserve_alpha_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, icon))
            )

        erase_mode = self.get_erase_mode_status()
        if erase_mode != self.is_erase_mode:
            self.is_erase_mode = erase_mode
            icon = "erase_mode_on.png" if erase_mode else "erase_mode_off.png"
            tooltip = "Erase Mode: On" if erase_mode else "Erase Mode: Off"
            self.erase_mode_label.setToolTip(tooltip)
            self.erase_mode_label.setPixmap(QPixmap(os.path.join(self.icon_dir, icon)))

        selection_info = self.get_selection_status()
        if selection_info != self.is_selected:
            self.is_selected = selection_info
            icon = "selection_on.png" if selection_info else "selection_off.png"
            tooltip = "Selection: On" if selection_info else "Selection: Off"
            self.selection_info_label.setToolTip(tooltip)
            self.selection_info_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, icon))
            )

        gesture_paused = is_gesture_filter_paused()
        if gesture_paused != self.is_gesture_paused:
            self.is_gesture_paused = gesture_paused
            icon = "gesture_off.png" if gesture_paused else "gesture_on.png"
            tooltip = "Gesture: Off" if gesture_paused else "Gesture: On"
            self.gesture_status_label.setToolTip(tooltip)
            self.gesture_status_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, icon))
            )

    def get_selection_status(self):
        doc = Krita.instance().activeDocument()
        if doc is None:
            return False
        return doc.selection() is not None

    def get_preserve_alpha_status(self):
        action = Krita.instance().action("preserve_alpha")
        return action.isChecked() if action else False

    def toggle_preserve_alpha(self, _event):
        action = Krita.instance().action("preserve_alpha")
        if action:
            action.setChecked(not action.isChecked())
        self.update_status()

    def get_erase_mode_status(self):
        action = Krita.instance().action("erase_action")
        return action.isChecked() if action else False

    def toggle_erase_mode(self, _event):
        action = Krita.instance().action("erase_action")
        if action:
            action.setChecked(not action.isChecked())
        self.update_status()

    def toggle_gesture_status(self, _event):
        if is_gesture_filter_paused():
            resume_gesture_event_filter()
        else:
            pause_gesture_event_filter()
        self.update_status()

    def enableToolOptionsExtension(self):
        """Enable the floating Tool Options extension if not already enabled"""
        window = Krita.instance().activeWindow()

        application = Krita.instance()
        tool_options_in_docker = application.readSetting(
            "", "ToolOptionsInDocker", "false"
        )

        if tool_options_in_docker.lower() == "true":
            if is_tool_options_enabled():
                self.float_tool_options = FloatToolOptions(window)

                start_visible = is_tool_options_start_visible()
                if start_visible:
                    self.float_tool_options.pad.setUserVisible(True)
                    self.tool_options_toggle_btn.setChecked(True)
                    self.tool_options_toggle_btn.setIcon(
                        QIcon(os.path.join(self.icon_dir, "tool_options_on.png"))
                    )
                else:
                    self.float_tool_options.pad.setUserVisible(False)
                    self.tool_options_toggle_btn.setChecked(False)
                    self.tool_options_toggle_btn.setIcon(
                        QIcon(os.path.join(self.icon_dir, "tool_options_off.png"))
                    )
            else:
                self.tool_options_toggle_btn.hide()
        else:
            self.tool_options_toggle_btn.hide()

    def toggle_tool_options_visibility(self):
        if self.float_tool_options:
            is_checked = self.tool_options_toggle_btn.isChecked()
            if is_checked:
                self.float_tool_options.pad.setUserVisible(True)
                self.tool_options_toggle_btn.setIcon(
                    QIcon(os.path.join(self.icon_dir, "tool_options_on.png"))
                )
            else:
                self.float_tool_options.pad.setUserVisible(False)
                self.tool_options_toggle_btn.setIcon(
                    QIcon(os.path.join(self.icon_dir, "tool_options_off.png"))
                )
            set_tool_options_start_visible(is_checked)
