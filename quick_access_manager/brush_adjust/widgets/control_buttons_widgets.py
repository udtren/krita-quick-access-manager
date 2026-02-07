import os
from krita import *
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QIcon
from ...gesture.gesture_main import (
    pause_gesture_event_filter,
    resume_gesture_event_filter,
    is_gesture_filter_paused,
)
from ..floating_widgets.tool_options import FloatToolOptions
from ..floating_widgets.floating_rotation import FloatRotation
from ..floating_widgets.specific_color_selector import FloatSpecificColorSelector
from ...config.quick_adjust_docker_loader import (
    is_tool_options_enabled,
    is_tool_options_start_visible,
    set_tool_options_start_visible,
    is_color_selector_enabled,
    is_color_selector_start_visible,
    set_color_selector_start_visible,
)


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
        self.is_preserve_alpha = False
        self.is_erase_mode = False
        self.float_rotation = None

        self.init_ui()
        self.update_status()

        # Timer to periodically update status
        self.status_update_timer = QTimer()
        self.status_update_timer.timeout.connect(self.update_status)
        self.status_update_timer.start(1000)  # Update every second

    def init_ui(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ============================================
        # Setup tool options extension initialization
        application = Krita.instance()
        appNotifier = application.notifier()
        appNotifier.windowCreated.connect(self.enableToolOptionsExtension)

        # Add Tool Options toggle button
        self.tool_options_toggle_btn = QPushButton()
        self.tool_options_toggle_btn.setFixedSize(16, 16)
        self.tool_options_toggle_btn.setToolTip("Toggle Tool Options")
        self.tool_options_toggle_btn.setIcon(
            (QIcon(os.path.join(self.icon_dir, "tool_options_on.png")))
        )
        self.tool_options_toggle_btn.setCheckable(True)
        self.tool_options_toggle_btn.setChecked(False)  # Start hidden
        self.tool_options_toggle_btn.clicked.connect(
            self.toggle_tool_options_visibility
        )

        # Add Rotation Widget toggle button
        self.rotation_toggle_btn = QPushButton()
        self.rotation_toggle_btn.setFixedSize(16, 16)
        self.rotation_toggle_btn.setToolTip("Toggle Floating Rotation Widget")
        self.rotation_toggle_btn.setIcon(
            (QIcon(os.path.join(self.icon_dir, "rotate-on.png")))  # Reuse icon for now
        )
        self.rotation_toggle_btn.setCheckable(True)
        self.rotation_toggle_btn.setChecked(
            False
        )  # Will be enabled after window creation
        self.rotation_toggle_btn.clicked.connect(self.toggle_rotation_visibility)

        # Add Specific Color Selector toggle button
        self.color_selector_toggle_btn = QPushButton()
        self.color_selector_toggle_btn.setFixedSize(16, 16)
        self.color_selector_toggle_btn.setToolTip("Toggle Specific Color Selector")
        self.color_selector_toggle_btn.setIcon(
            QIcon(os.path.join(self.icon_dir, "tool_options_off.png"))
        )
        self.color_selector_toggle_btn.setCheckable(True)
        self.color_selector_toggle_btn.setChecked(False)
        self.color_selector_toggle_btn.clicked.connect(
            self.toggle_color_selector_visibility
        )
        self.float_color_selector = None
        # ============================================

        # Create labels with fixed size for icons
        # Preserve Alpha status label
        self.preserve_alpha_label = QLabel()
        self.preserve_alpha_label.setFixedSize(16, 16)
        self.preserve_alpha_label.setScaledContents(True)
        self.preserve_alpha_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "preserve_alpha_off.png"))
        )
        self.preserve_alpha_label.setToolTip("Preserve Alpha: Off")
        self.preserve_alpha_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preserve_alpha_label.mousePressEvent = self.toggle_preserve_alpha

        # Erase Mode status label
        self.erase_mode_label = QLabel()
        self.erase_mode_label.setFixedSize(16, 16)
        self.erase_mode_label.setScaledContents(True)
        self.erase_mode_label.setPixmap(
            QPixmap(os.path.join(self.icon_dir, "erase_mode_off.png"))
        )
        self.erase_mode_label.setToolTip("Erase Mode: Off")
        self.erase_mode_label.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.gesture_status_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gesture_status_label.mousePressEvent = self.toggle_gesture_status

        layout.addWidget(self.tool_options_toggle_btn)
        layout.addWidget(self.color_selector_toggle_btn)
        layout.addWidget(self._create_separator())
        layout.addWidget(self.rotation_toggle_btn)
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
        """Create a vertical separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
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
        # Update preserve alpha icon only if status changed
        preserve_alpha = self.get_preserve_alpha_status()
        if preserve_alpha != self.is_preserve_alpha:
            self.is_preserve_alpha = preserve_alpha
            preserve_alpha_icon = (
                "preserve_alpha_on.png" if preserve_alpha else "preserve_alpha_off.png"
            )
            preserve_alpha_tooltip = (
                "Preserve Alpha: On" if preserve_alpha else "Preserve Alpha: Off"
            )
            self.preserve_alpha_label.setToolTip(preserve_alpha_tooltip)
            self.preserve_alpha_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, preserve_alpha_icon))
            )

        # Update erase mode icon only if status changed
        erase_mode = self.get_erase_mode_status()
        if erase_mode != self.is_erase_mode:
            self.is_erase_mode = erase_mode
            erase_mode_icon = (
                "erase_mode_on.png" if erase_mode else "erase_mode_off.png"
            )
            erase_mode_tooltip = "Erase Mode: On" if erase_mode else "Erase Mode: Off"
            self.erase_mode_label.setToolTip(erase_mode_tooltip)
            self.erase_mode_label.setPixmap(
                QPixmap(os.path.join(self.icon_dir, erase_mode_icon))
            )

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

    def get_preserve_alpha_status(self):
        """Get the current preserve alpha status from Krita"""
        app = Krita.instance()
        action = app.action("preserve_alpha")
        if action:
            return action.isChecked()
        return False

    def toggle_preserve_alpha(self, _event):
        """Toggle preserve alpha on/off when clicking the icon"""
        app = Krita.instance()
        action = app.action("preserve_alpha")
        if action:
            new_state = not action.isChecked()
            action.setChecked(new_state)
        # Force immediate update of the icon
        self.update_status()

    def get_erase_mode_status(self):
        """Get the current erase mode status from Krita"""
        app = Krita.instance()
        action = app.action("erase_action")
        if action:
            return action.isChecked()
        return False

    def toggle_erase_mode(self, _event):
        """Toggle erase mode on/off when clicking the icon"""
        app = Krita.instance()
        action = app.action("erase_action")
        if action:
            new_state = not action.isChecked()
            action.setChecked(new_state)
        # Force immediate update of the icon
        self.update_status()

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

        # Check if ToolOptionsInDocker is True (tool options is in docker)
        # The floating widget only works when Tool Options is in Docker mode, not in Toolbar
        application = Krita.instance()
        tool_options_in_docker = application.readSetting(
            "", "ToolOptionsInDocker", "false"
        )

        # Only enable floating tool options if it IS in docker mode (not in toolbar)
        if tool_options_in_docker.lower() == "true":
            # Check if tool options floating widget is enabled in config
            if is_tool_options_enabled():
                self.float_tool_options = FloatToolOptions(window)

                # Check if Tool Options should start visible
                start_visible = is_tool_options_start_visible()
                if start_visible:
                    self.float_tool_options.pad.setUserVisible(True)
                    self.tool_options_toggle_btn.setChecked(True)
                    self.tool_options_toggle_btn.setIcon(
                        (QIcon(os.path.join(self.icon_dir, "tool_options_on.png")))
                    )
                else:
                    # Hide the pad if not starting visible
                    self.float_tool_options.pad.setUserVisible(False)
                    self.tool_options_toggle_btn.setChecked(False)
                    self.tool_options_toggle_btn.setIcon(
                        (QIcon(os.path.join(self.icon_dir, "tool_options_off.png")))
                    )
            else:
                # Hide the tool options button if disabled in config
                self.tool_options_toggle_btn.hide()
        else:
            # Tool options is in toolbar mode, hide the toggle button
            self.tool_options_toggle_btn.hide()

        # Enable floating rotation widget (always enabled, start hidden)
        self.enableRotationExtension()

        # Enable floating color selector widget (start hidden)
        self.enableColorSelectorExtension()

    def toggle_tool_options_visibility(self):
        """Toggle the visibility of the Tool Options floating widget"""
        if hasattr(self, "float_tool_options") and self.float_tool_options:
            is_checked = self.tool_options_toggle_btn.isChecked()
            if is_checked:
                self.float_tool_options.pad.setUserVisible(True)
                self.tool_options_toggle_btn.setIcon(
                    (QIcon(os.path.join(self.icon_dir, "tool_options_on.png")))
                )
            else:
                self.float_tool_options.pad.setUserVisible(False)
                self.tool_options_toggle_btn.setIcon(
                    (QIcon(os.path.join(self.icon_dir, "tool_options_off.png")))
                )
            set_tool_options_start_visible(is_checked)

    def enableColorSelectorExtension(self):
        """Enable the floating Specific Color Selector extension"""
        window = Krita.instance().activeWindow()
        if not window:
            return

        # Check if color selector floating widget is enabled in config
        if not is_color_selector_enabled():
            # Hide the color selector button if disabled in config
            self.color_selector_toggle_btn.hide()
            return

        try:
            self.float_color_selector = FloatSpecificColorSelector(window)

            # Check if Color Selector should start visible
            start_visible = is_color_selector_start_visible()
            if start_visible:
                self.float_color_selector.pad.setUserVisible(True)
                self.color_selector_toggle_btn.setChecked(True)
                self.color_selector_toggle_btn.setIcon(
                    QIcon(os.path.join(self.icon_dir, "specific_color_selector_on.png"))
                )
            else:
                # Hide the pad if not starting visible
                self.float_color_selector.pad.setUserVisible(False)
                self.color_selector_toggle_btn.setChecked(False)
                self.color_selector_toggle_btn.setIcon(
                    QIcon(
                        os.path.join(self.icon_dir, "specific_color_selector_off.png")
                    )
                )
        except Exception:
            # Docker not found, hide the button
            self.color_selector_toggle_btn.hide()

    def toggle_color_selector_visibility(self):
        """Toggle the visibility of the Specific Color Selector floating widget"""
        if not self.float_color_selector:
            return

        is_checked = self.color_selector_toggle_btn.isChecked()
        if is_checked:
            self.float_color_selector.pad.setUserVisible(True)
            self.color_selector_toggle_btn.setIcon(
                QIcon(os.path.join(self.icon_dir, "specific_color_selector_on.png"))
            )
        else:
            self.float_color_selector.pad.setUserVisible(False)
            self.color_selector_toggle_btn.setIcon(
                QIcon(os.path.join(self.icon_dir, "specific_color_selector_off.png"))
            )
        set_color_selector_start_visible(is_checked)

    def toggle_rotation_visibility(self):
        """Toggle the visibility of the floating rotation widget"""
        if not hasattr(self, "float_rotation") or not self.float_rotation:
            return

        is_checked = self.rotation_toggle_btn.isChecked()

        if is_checked:
            # Show container, pad, and child widgets
            self.float_rotation.container.show()
            self.float_rotation.rotation_widget.show()
            self.float_rotation.rotation_label.show()
            self.float_rotation.pad.show()
            # Force position update immediately
            self.float_rotation.pad.adjustToView()
            self.rotation_toggle_btn.setIcon(
                (QIcon(os.path.join(self.icon_dir, "rotate-on.png")))
            )
        else:
            # Hide pad, container, and child widgets
            self.float_rotation.pad.hide()
            self.float_rotation.container.hide()
            self.float_rotation.rotation_widget.hide()
            self.float_rotation.rotation_label.hide()
            self.rotation_toggle_btn.setIcon(
                (QIcon(os.path.join(self.icon_dir, "rotate-off.png")))
            )

    def enableRotationExtension(self):
        """Enable the floating rotation widget extension"""
        window = Krita.instance().activeWindow()
        if not window:
            return

        # Get rotation widget and label from parent adjustment widget
        adjustment_widget = self.parent()
        if (
            hasattr(adjustment_widget, "rotation_widget")
            and adjustment_widget.rotation_widget
        ):
            rotation_widget = adjustment_widget.rotation_widget
            rotation_label = adjustment_widget.rotation_value_label

            # Create floating widget first
            self.float_rotation = FloatRotation(window, rotation_widget, rotation_label)

            # Reparent widgets to the floating container
            rotation_widget.setParent(self.float_rotation.container)
            rotation_label.setParent(self.float_rotation.container)

            # Start with rotation widget hidden (including pad, container, and child widgets)
            self.float_rotation.pad.hide()
            self.float_rotation.container.hide()
            rotation_widget.hide()
            rotation_label.hide()
            self.rotation_toggle_btn.setChecked(False)
            self.rotation_toggle_btn.setIcon(
                (QIcon(os.path.join(self.icon_dir, "rotate-off.png")))
            )
