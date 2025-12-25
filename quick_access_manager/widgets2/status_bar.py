import os
from krita import *
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap
from ..gesture.gesture_main import (
    pause_gesture_event_filter,
    resume_gesture_event_filter,
    is_gesture_filter_paused,
)


class StatusBarWidget(QWidget):
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
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(3)

        # Create labels with fixed size for icons
        self.selection_info_label = QLabel()
        self.selection_info_label.setFixedSize(18, 18)
        self.selection_info_label.setScaledContents(True)
        self.selection_info_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "selection_off.png"))
        )
        self.selection_info_label.setToolTip("Selection: Off")

        self.inherit_alpha_info_label = QLabel()
        self.inherit_alpha_info_label.setFixedSize(18, 18)
        self.inherit_alpha_info_label.setScaledContents(True)
        self.inherit_alpha_info_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "inherit_alpha_off.png"))
        )
        self.inherit_alpha_info_label.setToolTip("Inherit Alpha: Off")

        self.alphalock_info_label = QLabel()
        self.alphalock_info_label.setFixedSize(18, 18)
        self.alphalock_info_label.setScaledContents(True)
        self.alphalock_info_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "alpha_lock_off.png"))
        )
        self.alphalock_info_label.setToolTip("Alpha Lock: Off")

        self.gesture_status_label = QLabel()
        self.gesture_status_label.setFixedSize(18, 18)
        self.gesture_status_label.setScaledContents(True)
        self.gesture_status_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "gesture_on.png"))
        )
        self.gesture_status_label.setToolTip("Gesture: On")
        self.gesture_status_label.setCursor(Qt.PointingHandCursor)
        self.gesture_status_label.mousePressEvent = self.toggle_gesture_status

        layout.addWidget(self.selection_info_label)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.inherit_alpha_info_label)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.alphalock_info_label)
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

        # Update alpha lock icon only if status changed
        alphalock_info = self.get_alphalock_status()
        if alphalock_info != self.is_alphalock:
            self.is_alphalock = alphalock_info
            alphalock_icon = (
                "alpha_lock_on.png" if alphalock_info else "alpha_lock_off.png"
            )
            alphalock_tooltip = (
                "Alpha Lock: On" if alphalock_info else "Alpha Lock: Off"
            )
            self.alphalock_info_label.setToolTip(alphalock_tooltip)
            self.alphalock_info_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, alphalock_icon))
            )

        # Update inherit alpha icon only if status changed
        inherit_alpha_info = self.get_inherit_alpha_status()
        if inherit_alpha_info != self.is_inherit_alpha:
            self.is_inherit_alpha = inherit_alpha_info
            inherit_alpha_icon = (
                "inherit_alpha_on.png"
                if inherit_alpha_info
                else "inherit_alpha_off.png"
            )
            inherit_alpha_tooltip = (
                "Inherit Alpha: On" if inherit_alpha_info else "Inherit Alpha: Off"
            )
            self.inherit_alpha_info_label.setToolTip(inherit_alpha_tooltip)
            self.inherit_alpha_info_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, inherit_alpha_icon))
            )

        # Update gesture status icon only if status changed
        gesture_paused = is_gesture_filter_paused()
        if gesture_paused != self.is_gesture_paused:
            self.is_gesture_paused = gesture_paused
            gesture_icon = (
                "gesture_off.png" if gesture_paused else "gesture_on.png"
            )
            gesture_tooltip = (
                "Gesture: Off" if gesture_paused else "Gesture: On"
            )
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

    def get_alphalock_status(self):
        doc = Krita.instance().activeDocument()
        if doc is None:
            return False
        active_node = doc.activeNode()
        if active_node is None:
            return False
        return active_node.alphaLocked()

    def get_inherit_alpha_status(self):
        doc = Krita.instance().activeDocument()
        if doc is None:
            return False
        active_node = doc.activeNode()
        if active_node is None:
            return False
        return active_node.inheritAlpha()

    def toggle_gesture_status(self, _event):
        """Toggle gesture system on/off when clicking the icon"""
        if is_gesture_filter_paused():
            resume_gesture_event_filter()
        else:
            pause_gesture_event_filter()
        # Force immediate update of the icon
        self.update_status()
