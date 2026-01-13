import os
from krita import *
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
from ...gesture.gesture_main import (
    pause_gesture_event_filter,
    resume_gesture_event_filter,
    is_gesture_filter_paused,
)
from ..floating_widgets.tool_options import ntToolOptions


class ControlButtonWidget(QWidget):
    """Status bar widget to display document information"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_dir = os.path.join(os.path.dirname(__file__), "icon")

        # Initialize tracking variables before UI setup
        self.is_selected = False
        self.is_alphalock = False
        self.is_inherit_alpha = False
        self.is_gesture_paused = False

        self.init_ui()
        self.update_status()

        # Timer to periodically update status
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(1000)  # Update every second

    def init_ui(self):

        # Setup tool options extension initialization
        application = Krita.instance()
        appNotifier = application.notifier()
        appNotifier.windowCreated.connect(self.enableToolOptionsExtension)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignTop)

        # Add Tool Options toggle button
        self.tool_options_toggle_btn = QPushButton()
        self.tool_options_toggle_btn.setFixedSize(16, 16)
        self.tool_options_toggle_btn.setToolTip("Toggle Tool Options")
        self.tool_options_toggle_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border: 1px solid #888888;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:checked {
                background-color: #6a9fb5;
                border: 1px solid #4a7f95;
            }
            """
        )
        self.tool_options_toggle_btn.setCheckable(True)
        self.tool_options_toggle_btn.setChecked(False)  # Start hidden
        self.tool_options_toggle_btn.clicked.connect(
            self.toggle_tool_options_visibility
        )

        # Create labels with fixed size for icons
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
        layout.addWidget(self.selection_info_label)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.gesture_status_label)
        layout.addStretch()

        self.setLayout(layout)

    def _create_separator(self):
        """Create a vertical separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(
            """
            QFrame {
                color: #3a3a3a;
                margin: 2px 8px;
            }
            """
        )
        return separator

    def update_status(self):
        # Update selection icon only if status changed
        selection_info = self.get_selection_status()
        if selection_info != self.is_selected:
            self.is_selected = selection_info
            selection_icon = (
                "selection_on.png" if selection_info else "selection_off.png"
            )
            selection_tooltip = "Selection: On" if selection_info else "Selection: Off"
            self.selection_info_label.setToolTip(selection_tooltip)
            self.selection_info_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, selection_icon))
            )

        # Update gesture status icon only if status changed
        gesture_paused = is_gesture_filter_paused()
        if gesture_paused != self.is_gesture_paused:
            self.is_gesture_paused = gesture_paused
            gesture_icon = "gesture_off.png" if gesture_paused else "gesture_on.png"
            gesture_tooltip = "Gesture: Off" if gesture_paused else "Gesture: On"
            self.gesture_status_label.setToolTip(gesture_tooltip)
            self.gesture_status_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, gesture_icon))
            )

    def get_selection_status(self):
        doc = Krita.instance().activeDocument()
        if doc is None:
            return False
        selection = doc.selection()
        if selection is None:
            return False
        return True

    def toggle_gesture_status(self, _event):
        """Toggle gesture system on/off when clicking the icon"""
        if is_gesture_filter_paused():
            resume_gesture_event_filter()
        else:
            pause_gesture_event_filter()
        # Force immediate update of the icon
        self.update_status()

    def enableToolOptionsExtension(self):
        """Enable the floating Tool Options extension if not already enabled"""
        window = Krita.instance().activeWindow()
        self.ntTO = ntToolOptions(window)

        self.ntTO.pad.show()
        self.tool_options_toggle_btn.setChecked(True)

    def toggle_tool_options_visibility(self):
        """Toggle the visibility of the Tool Options floating widget"""
        if hasattr(self, "ntTO") and self.ntTO:
            is_checked = self.tool_options_toggle_btn.isChecked()
            if is_checked:
                self.ntTO.pad.show()
            else:
                self.ntTO.pad.hide()
