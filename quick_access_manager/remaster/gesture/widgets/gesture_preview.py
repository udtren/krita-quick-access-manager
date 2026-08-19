"""
Gesture preview widget that displays available actions in a 3x3 grid.
"""

import os

from krita import Krita  # type: ignore

from ...compat import QGridLayout, QLabel, QPixmap, Qt, QWidget
from ...infrastructure import AliasRepository, get_default_icons_dir


class GesturePreviewWidget(QWidget):
    """Shows available gesture actions in a 3x3 grid near the cursor."""

    def __init__(self):
        super().__init__(
            None, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setWindowTitle("Gesture Preview")
        self.alias_repository = AliasRepository()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(8, 8, 8, 8)

        try:
            self.preset_dict = Krita.instance().resources("preset")
        except Exception:
            self.preset_dict = {}

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
            self.layout.addWidget(label, row, col)
            self.direction_labels[direction] = label

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(70, 70, 120, 0);
                color: transparent;
                border: 2px solid rgba(119, 119, 255, 0);
            }
        """)

        self.hide()

    def clear_all_labels(self):
        for label in self.direction_labels.values():
            label.clear()
            label.setText("")
            label.setStyleSheet("")

    def show_preview(self, gesture_map, cursor_pos):
        self.clear_all_labels()

        for direction, label in self.direction_labels.items():
            gesture_config = gesture_map.get(direction)
            if not gesture_config:
                label.setStyleSheet(
                    "QLabel { background-color: rgba(0, 0, 0, 0); color: transparent; border: none; }"
                )
                continue

            gesture_type = gesture_config.get("gesture_type", "unknown")
            if gesture_type == "action":
                self._show_alias_or_text(
                    label,
                    gesture_config["parameters"].get("action_id", "unknown"),
                    category="actions",
                    background="#aea152",
                )
            elif gesture_type == "brush":
                self._show_brush(
                    label, gesture_config["parameters"].get("brush_name", "unknown")
                )
            elif gesture_type == "docker_toggle":
                self._show_alias_or_text(
                    label,
                    gesture_config["parameters"].get("docker_name", "unknown"),
                    category="dockers",
                    background="#909090",
                    icon_background="#323232",
                )
            else:
                label.setText("")
                label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(70, 70, 120, 0);
                        color: transparent;
                        border: 2px solid rgba(119, 119, 255, 0);
                        border-radius: 8px;
                        padding: 8px;
                        font-size: 11px;
                    }
                    """)

        self.adjustSize()
        preview_width = self.width()
        preview_height = self.height()
        self.move(
            cursor_pos.x() - preview_width // 2, cursor_pos.y() - preview_height // 2
        )
        self.show()
        self.raise_()

    def _show_alias_or_text(
        self, label, item_id, category, background, icon_background=None
    ):
        alias = self.alias_repository.load().get(category, {}).get(item_id, {})
        icon_path = self.resolve_icon_path(alias.get("icon_name"))
        if icon_path:
            try:
                pixmap = QPixmap(icon_path).scaled(
                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                label.setPixmap(pixmap)
                label.setText("")
                label.setStyleSheet(
                    f"QLabel {{ background-color: {icon_background or background}; border-radius: 8px; border: 2px solid #1c2212; padding: 8px; }}"
                )
                return
            except Exception:
                pass

        display_name = alias.get("custom_name") or item_id
        label.clear()
        label.setText(display_name)
        label.setStyleSheet(
            f"QLabel {{ background-color: {background}; color: #000000; border-radius: 8px; border: 2px solid #1c2212; "
            "padding: 8px; font-size: 18px; font-weight: bold; opacity: 0.7; }"
        )

    def resolve_icon_path(self, icon_name):
        if not icon_name:
            return None
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
        icon_path = os.path.join(get_default_icons_dir(), icon_name)
        return icon_path if os.path.exists(icon_path) else None

    def _show_brush(self, label, brush_name):
        try:
            if brush_name and brush_name in self.preset_dict:
                preset = self.preset_dict[brush_name]
                preset_image = preset.image()
                if preset_image:
                    pixmap = QPixmap.fromImage(preset_image).scaled(
                        64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    label.setPixmap(pixmap)
                    label.setText("")
                    label.setStyleSheet(
                        "QLabel { background-color: #7e7cb8; border-radius: 8px; padding: 8px; }"
                    )
                    return
        except Exception:
            pass

        label.clear()
        label.setText(brush_name)
        label.setStyleSheet(
            "QLabel { background-color: #7e7cb8; color: #000000; border-radius: 8px; border: 2px solid #1c2212; "
            "padding: 4px; font-size: 18px; font-weight: bold; opacity: 0.7; }"
        )

    def hide_preview(self):
        self.clear_all_labels()
        self.hide()
