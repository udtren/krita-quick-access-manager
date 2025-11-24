"""
Gesture preview widget that displays available actions in a 3x3 grid.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout


class GesturePreviewWidget(QWidget):
    """
    Preview widget that shows available gesture actions in a 3x3 grid.
    Displays near the cursor when a gesture key is pressed.
    """

    def __init__(self):
        super().__init__(
            None, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setWindowTitle("Gesture Preview")

        # Create grid layout (3x3)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(8, 8, 8, 8)

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
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(100, 40)
            # label.setStyleSheet(
            #     """
            #     QLabel {
            #         background-color: rgba(50, 50, 50, 200);
            #         color: #888;
            #         border: 1px solid #555;
            #         border-radius: 4px;
            #         padding: 8px;
            #         font-size: 11px;
            #     }
            # """
            # )
            self.layout.addWidget(label, row, col)
            self.direction_labels[direction] = label

        # Style the center differently
        # self.direction_labels["center"].setStyleSheet(
        #     """
        #     QLabel {
        #         background-color: rgba(70, 70, 120, 200);
        #         color: #aaf;
        #         border: 2px solid #77f;
        #         border-radius: 4px;
        #         padding: 8px;
        #         font-size: 11px;
        #         font-weight: bold;
        #     }
        # """
        # )

        # Set window style
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(30, 30, 30, 230);
                border: 2px solid #666;
                border-radius: 6px;
            }
        """
        )

        self.hide()

    def show_preview(self, gesture_map, cursor_pos):
        """
        Show the preview widget with gesture actions.

        Args:
            gesture_map: Dict mapping direction to gesture config
            cursor_pos: QPoint of cursor position
        """
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
                elif gesture_type == "brush":
                    action_name = gesture_config["parameters"].get(
                        "brush_name", "unknown"
                    )
                elif gesture_type == "docker_toggle":
                    action_name = gesture_config["parameters"].get(
                        "docker_name", "unknown"
                    )
                else:
                    action_name = "-"

                label.setText(action_name)

                # Highlight configured actions
                if direction == "center":
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: rgba(70, 120, 70, 220);
                            color: #afa;
                            border: 2px solid #7f7;
                            border-radius: 4px;
                            padding: 8px;
                            font-size: 16px;
                            font-weight: bold;
                            opacity: 0.7;
                        }
                    """
                    )
                else:
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: rgba(70, 70, 70, 220);
                            color: #eee;
                            border: 1px solid #999;
                            border-radius: 4px;
                            padding: 8px;
                            font-size: 16px;
                            font-weight: bold;
                            opacity: 0.7;
                        }
                    """
                    )
            else:
                label.setText("")  # Empty text for unconfigured
                if direction == "center":
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: rgba(70, 70, 120, 0);
                            color: transparent;
                            border: 2px solid rgba(119, 119, 255, 0);
                            border-radius: 4px;
                            padding: 8px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                    """
                    )
                else:
                    label.setStyleSheet(
                        """
                        QLabel {
                            background-color: rgba(70, 70, 120, 0);
                            color: transparent;
                            border: 2px solid rgba(119, 119, 255, 0);
                            border-radius: 4px;
                            padding: 8px;
                            font-size: 11px;
                            font-weight: bold;
                        }
                    """
                    )

        # Position widget near cursor (offset to not block cursor)
        self.adjustSize()
        offset_x = 30
        offset_y = 30
        self.move(cursor_pos.x() + offset_x, cursor_pos.y() + offset_y)

        # Show the widget
        self.show()
        self.raise_()

    def hide_preview(self):
        """Hide the preview widget"""
        self.hide()
