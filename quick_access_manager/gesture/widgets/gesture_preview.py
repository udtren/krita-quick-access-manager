"""
Gesture preview widget that displays available actions in a 3x3 grid.
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt6.QtGui import QPixmap
from krita import Krita  # type: ignore
from quick_access_manager.utils.logs import write_log
from quick_access_manager.utils.config_utils import get_gesture_data_dir


class GesturePreviewWidget(QWidget):
    """
    Preview widget that shows available gesture actions in a 3x3 grid.
    Displays near the cursor when a gesture key is pressed.
    """

    def __init__(self, gesture_alias):
        super().__init__(
            None, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle("Gesture Preview")
        self.gesture_alias = gesture_alias
        write_log(f"Gesture alias loaded: {self.gesture_alias}")

        # Get icon directory path
        self.icon_dir = os.path.join(get_gesture_data_dir(), "icon")

        # Create grid layout (3x3)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(8, 8, 8, 8)

        try:
            self.preset_dict = Krita.instance().resources("preset")
        except:
            self.preset_dict = {}

        # Create labels for each direction (3x3 grid)
        # Positions: (row, col)
        # 0,0=left_up  0,1=up  0,2=right_up
        # 1,0=left     1,1=center  1,2=right
        # 2,0=left_down  2,1=down  2,2=right_down
        self.direction_labels = {}
        direction_positions = {
            "left_up": (0, 0),
            "up": (0, 1),
            "right_up": (0, 2),
            "left": (1, 0),
            "center": (1, 1),
            "right": (1, 2),
            "left_down": (2, 0),
            "down": (2, 1),
            "right_down": (2, 2),
        }

        for direction, (row, col) in direction_positions.items():
            label = QLabel("none")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumSize(100, 40)
            self.layout.addWidget(label, row, col)
            self.direction_labels[direction] = label

        # Set window style
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(70, 70, 120, 0);
                color: transparent;
                border: 2px solid rgba(119, 119, 255, 0);
            }
        """
        )

        self.hide()

    def clear_all_labels(self):
        """Clear all labels (text, pixmap, and styles)"""
        for label in self.direction_labels.values():
            label.clear()  # Clears both text and pixmap
            label.setText("")
            label.setStyleSheet("")  # Reset style

    def show_preview(self, gesture_map, cursor_pos):
        """
        Show the preview widget with gesture actions.

        Args:
            gesture_map: Dict mapping direction to gesture config
            cursor_pos: QPoint of cursor position
        """
        # First, clear all labels to remove old content (text/pixmaps)
        self.clear_all_labels()

        # Update labels with action names
        for direction, label in self.direction_labels.items():
            if direction in gesture_map:
                gesture_config = gesture_map[direction]
                action_name = None
                gesture_type = gesture_config.get("gesture_type", "unknown")
                if gesture_type == "action":
                    action_name = gesture_config["parameters"].get(
                        "action_id", "unknown"
                    )
                    # Check for alias icon
                    if (
                        action_name in self.gesture_alias
                        and "icon_name" in self.gesture_alias[action_name]
                    ):
                        icon_name = self.gesture_alias[action_name]["icon_name"]
                        try:
                            icon_path = os.path.join(self.icon_dir, icon_name)
                            pixmap = QPixmap(icon_path).scaled(
                                32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                            )
                            label.setPixmap(pixmap)
                            label.setText("")  # Clear text when showing pixmap
                            label.setStyleSheet(
                                """
                                QLabel {
                                    background-color: #aea152;
                                    border-radius: 8px;
                                    border: 2px solid #1c2212;
                                    padding: 8px;
                                }
                                """
                            )
                            continue  # Skip to next direction after setting pixmap
                        except:
                            pass  # If loading icon fails, fallback to text

                    # Check for alias name
                    if (
                        action_name in self.gesture_alias
                        and "alias_name" in self.gesture_alias[action_name]
                    ):
                        action_name = self.gesture_alias[action_name]["alias_name"]

                    label.clear()  # Clear any previous pixmap
                    label.setText(action_name)
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: #aea152;
                            color: #000000;
                            border-radius: 8px;
                            border: 2px solid #1c2212;
                            padding: 4px;
                            font-size: 18px;
                            font-weight: bold;
                            opacity: 0.7;
                        }
                    """
                    )
                elif gesture_type == "brush":
                    action_name = gesture_config["parameters"].get(
                        "brush_name", "unknown"
                    )
                    brush_set_successfully = False
                    try:
                        if action_name and action_name in self.preset_dict:
                            preset = self.preset_dict[action_name]
                            preset_image = preset.image()
                            if preset_image:
                                pixmap = QPixmap.fromImage(preset_image).scaled(
                                    64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                                )
                                label.setPixmap(pixmap)
                                label.setText("")  # Clear text when showing pixmap
                                label.setStyleSheet(
                                    """
                                    QLabel {
                                        background-color: #7e7cb8;
                                        border-radius: 8px;
                                        padding: 8px;
                                    }
                                    """
                                )
                                brush_set_successfully = True
                    except:
                        pass

                    # Fallback to text if pixmap failed
                    if not brush_set_successfully:
                        label.clear()  # Clear any pixmap
                        label.setText(action_name)
                        label.setStyleSheet(
                            """
                            QLabel {
                                background-color: #7e7cb8;
                                color: #000000;
                                border-radius: 8px;
                                border: 2px solid #1c2212;
                                padding: 4px;
                                font-size: 18px;
                                font-weight: bold;
                                opacity: 0.7;
                            }
                            """
                        )

                elif gesture_type == "docker_toggle":
                    action_name = gesture_config["parameters"].get(
                        "docker_name", "unknown"
                    )
                    # Check for alias icon
                    if (
                        action_name in self.gesture_alias
                        and "icon_name" in self.gesture_alias[action_name]
                    ):
                        icon_name = self.gesture_alias[action_name]["icon_name"]
                        try:
                            icon_path = os.path.join(self.icon_dir, icon_name)
                            pixmap = QPixmap(icon_path).scaled(
                                32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                            )
                            label.setPixmap(pixmap)
                            label.setText("")  # Clear text when showing pixmap
                            label.setStyleSheet(
                                """
                                QLabel {
                                    background-color: #323232;
                                    border-radius: 8px;
                                    border: 2px solid #1c2212;
                                    padding: 8px;
                                }
                                """
                            )
                            continue  # Skip to next direction after setting pixmap
                        except:
                            pass  # If loading icon fails, fallback to text
                    # Check for alias name
                    if (
                        action_name in self.gesture_alias
                        and "alias_name" in self.gesture_alias[action_name]
                    ):
                        action_name = self.gesture_alias[action_name]["alias_name"]
                    label.clear()  # Clear any previous pixmap
                    label.setText(action_name)
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: #909090;
                            color: #000000;
                            border-radius: 8px;
                            border: 2px solid #1c2212;
                            padding: 8px;
                            font-size: 18px;
                            font-weight: bold;
                            opacity: 0.7;
                        }
                    """
                    )
                else:
                    # Unknown gesture type - make transparent
                    label.clear()  # Clear any previous pixmap
                    label.setText("")
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: rgba(70, 70, 120, 0);
                            color: transparent;
                            border: 2px solid rgba(119, 119, 255, 0);
                            border-radius: 8px;
                            padding: 8px;
                            font-size: 11px;
                        }
                    """
                    )
            else:
                # No gesture configured for this direction - make transparent
                label.clear()  # Clear any previous pixmap
                label.setText("")
                label.setStyleSheet(
                    """
                    QLabel {
                        background-color: rgba(0, 0, 0, 0);
                        color: transparent;
                        border: none;
                    }
                    """
                )

        # Position widget at cursor position, centered
        self.adjustSize()
        preview_width = self.width()
        preview_height = self.height()
        self.move(
            cursor_pos.x() - preview_width // 2, cursor_pos.y() - preview_height // 2
        )

        # Show the widget
        self.show()
        self.raise_()

    def update_gesture_alias(self, gesture_alias):
        """Update the gesture alias dictionary"""
        self.gesture_alias = gesture_alias
        write_log(f"Preview widget gesture alias updated: {self.gesture_alias}")

    def hide_preview(self):
        """Hide the preview widget and clear all labels"""
        self.clear_all_labels()  # Clear pixmaps and text before hiding
        self.hide()
