"""Shared item-widget styling/icon-lookup logic for the docker and the popup.

Both `docker.py`'s `QuickAccessPaletteDockerWidget` and `popup.py`'s
`QuickAccessPalettePopup` render the same palette item types with the same
QSS, so this mixin is the single place those rules live. A host class must
provide `self._alias_data` (an `AliasRepository().load()` result), `self.controller`
(a `PaletteController`), and an `item_cell_size()` method returning the
current cell size in pixels.
"""

import os

from ..compat import QIcon, QPixmap, QSize
from ..infrastructure import get_default_icons_dir


class ItemStyleMixin:
    def item_icon_size(self):
        size = max(16, self.item_cell_size() - 4)
        return QSize(size, size)

    def resolve_icon_path(self, icon_name):
        if not icon_name:
            return None
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            return icon_name
        icon_path = os.path.join(get_default_icons_dir(), icon_name)
        if os.path.exists(icon_path):
            return icon_path
        return None

    def alias_entry(self, category, item_id):
        return self._alias_data.get(category, {}).get(item_id, {})

    def _set_brush_pixmap(self, button, preset):
        """Try to set `button`'s icon from `preset`'s image. Returns success."""
        image = preset.image() if preset else None
        if image:
            pixmap = QPixmap.fromImage(image)
            if not pixmap.isNull():
                button.setIcon(QIcon(pixmap))
                button.setIconSize(self.item_icon_size())
                button.setText("")
                button.setStyleSheet(
                    "QPushButton { padding: 0px; border: 1px solid #555; background: #2f2f2f; }"
                )
                return True
        return False

    def apply_action_style(
        self, button, alias, has_icon=False, default_bg="#3a263f", default_fg="#ffffff"
    ):
        bg = alias.get("background_color") or default_bg
        fg = alias.get("font_color") or default_fg
        size = alias.get("font_size") or "18"
        padding = "0px" if has_icon else "2px 6px"
        button.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {fg}; font-size: {size}px; border: 1px solid #6b4a73; border-radius: 4px; padding: {padding}; }}"
        )

    def apply_label_style(self, label, item):
        bg = item.payload.get("backgroundColor", "transparent")
        fg = item.payload.get("fontColor", "#4FC3F7")
        size = item.payload.get("fontSize", "18")
        background_rule = (
            f"background: {bg};" if bg != "transparent" else "background: transparent;"
        )
        label.setStyleSheet(
            f"QLabel {{ {background_rule} color: {fg}; font-size: {size}px; font-weight: bold; padding: 0px 4px; }}"
        )

    def apply_brush_size_style(self, button, item):
        bg = item.payload.get("backgroundColor", "#3a263f")
        fg = item.payload.get("fontColor", "#ffffff")
        size = item.payload.get("fontSize", "18")
        button.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {fg}; font-size: {size}px; font-weight: bold; border: 1px solid #6b4a73; border-radius: 4px; }}"
        )

    def apply_brush_blend_mode_style(self, button, item):
        bg = item.payload.get("backgroundColor", "#263a3a")
        fg = item.payload.get("fontColor", "#ffffff")
        size = item.payload.get("fontSize", "18")
        button.setStyleSheet(
            f"QPushButton {{ background: {bg}; color: {fg}; font-size: {size}px; font-weight: bold; border: 1px solid #4a8b8b; border-radius: 4px; padding: 0px 4px; }}"
        )

    def tab_bar_stylesheet(self):
        style = self.controller.tab_bar_settings()
        return (
            "QTabBar::tab {"
            f" background: {style['inactive_background_color']};"
            f" color: {style['inactive_font_color']};"
            f" font-size: {style['inactive_font_size']}px;"
            " padding: 4px 10px;"
            " }"
            "QTabBar::tab:selected {"
            f" background: {style['active_background_color']};"
            f" color: {style['active_font_color']};"
            f" font-size: {style['active_font_size']}px;"
            " }"
        )
