import os
import json
import re

from krita import Krita, Preset  # type: ignore
from ..compat import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QShortcut,
    Qt,
    QCursor,
)
from ..utils.config_utils import get_presets_config_dir
from ..config.popup_loader import PopupConfigLoader


def _sanitize_filename(name):
    """Replace characters that are invalid in Windows filenames."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)


class PresetSwitchManager:
    """Manages saving, switching, and deleting brush preset XML configs."""

    def __init__(self, parent_docker):
        self.parent_docker = parent_docker
        self._popup = None
        self._shortcut = None

    def setup_shortcut(self):
        """Register the popup shortcut from popup.json (empty = disabled)."""
        loader = PopupConfigLoader()
        key_seq = loader.get_preset_switch_popup_shortcut()
        if not key_seq:
            return
        try:
            app = Krita.instance()
            parent = None
            if app.activeWindow():
                parent = app.activeWindow().qwindow()
            parent = parent or self.parent_docker
            self._shortcut = QShortcut(key_seq, parent)
            self._shortcut.setContext(Qt.ApplicationShortcut)
            self._shortcut.activated.connect(self.show_preset_switch_popup)
        except Exception as e:
            print(f"PresetSwitch: error setting up shortcut: {e}")

    def show_preset_switch_popup(self):
        """Show a popup listing saved configs for the current brush.

        Called by a keyboard key (key binding left empty for now).
        Mouse leaving the popup closes it.
        """
        app = Krita.instance()
        win = app.activeWindow()
        if not win:
            return
        view = win.activeView()
        if not view:
            return

        resource = view.currentBrushPreset()
        if not resource:
            return

        brush_name = resource.name()
        presets_dir = get_presets_config_dir()
        filename = _sanitize_filename(brush_name) + ".json"
        filepath = os.path.join(presets_dir, filename)

        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        if not data:
            return

        if self._popup is not None:
            try:
                if self._popup.isVisible():
                    self._popup.close()
            except RuntimeError:
                pass
            self._popup = None

        popup = _PresetSwitchPopup(data, resource, view, self.parent_docker)
        cursor_pos = QCursor.pos()
        popup.move(
            cursor_pos.x() - popup.width() // 2,
            cursor_pos.y() - popup.height() // 3,
        )
        popup.show()
        self._popup = popup


# ---------------------------------------------------------------------------
# Popup widget for Function 2
# ---------------------------------------------------------------------------
class _PresetSwitchPopup(QWidget):
    def __init__(self, data, resource, view, parent=None):
        super().__init__(
            parent,
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint,
        )
        self._resource = resource
        self._view = view
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        title = QLabel(resource.name())
        title.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(title)

        for config_name, xml in sorted(data.items()):
            btn = QPushButton(config_name)
            btn.setStyleSheet("text-align: left; padding: 4px 8px;")
            btn.clicked.connect(lambda _checked=False, x=xml: self._apply(x))
            layout.addWidget(btn)

        self.setLayout(layout)
        self.adjustSize()

    def _apply(self, xml):
        try:
            preset = Preset(self._resource)
            preset.fromXML(xml)
            self._view.setCurrentBrushPreset(self._resource)
        except Exception as e:
            print(f"PresetSwitch: error applying config: {e}")
        self.close()

    def leaveEvent(self, event):
        self.close()
        super().leaveEvent(event)
