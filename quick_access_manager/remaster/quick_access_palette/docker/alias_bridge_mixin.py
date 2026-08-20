"""Shared Alias Config read/write bridge (single reference for Action/Docker
custom name, colors, font size, and icon) plus the Brush item's icon
lookup, which goes through Krita's preset resources rather than an alias."""

from krita import Krita  # type: ignore

from ...infrastructure import AliasRepository


class AliasBridgeMixin:
    """Requires `self._alias_data` (maintained by reload_tabs) and
    `self._set_brush_pixmap()`/`self.alias_entry()` from ItemStyleMixin."""

    def save_alias_entry(self, category, item_id, updates):
        if not item_id:
            return
        repository = AliasRepository()
        data = repository.load()
        entry = dict(data.get(category, {}).get(item_id, {}))
        entry.update(updates)
        data.setdefault(category, {})[item_id] = entry
        repository.save(data)
        self._alias_data = data

    def action_alias_dialog_config(self, action_id):
        alias = self.alias_entry("actions", action_id)
        return {
            "customName": alias.get("custom_name") or action_id,
            "fontSize": alias.get("font_size") or "18",
            "backgroundColor": alias.get("background_color") or "#3a263f",
            "fontColor": alias.get("font_color") or "#ffffff",
            "icon_name": alias.get("icon_name", ""),
        }

    def save_action_alias(self, action_id, dialog_config):
        self.save_alias_entry(
            "actions",
            action_id,
            {
                "custom_name": dialog_config.get("customName", ""),
                "font_size": dialog_config.get("fontSize", ""),
                "background_color": dialog_config.get("backgroundColor", ""),
                "font_color": dialog_config.get("fontColor", ""),
                "icon_name": dialog_config.get("icon_name", ""),
            },
        )

    def docker_alias_dialog_config(self, docker_id):
        alias = self.alias_entry("dockers", docker_id)
        return {
            "docker_id": docker_id,
            "customName": alias.get("custom_name") or docker_id,
            "icon_name": alias.get("icon_name", ""),
        }

    def save_docker_alias(self, docker_id, dialog_config):
        self.save_alias_entry(
            "dockers",
            docker_id,
            {
                "custom_name": dialog_config.get("customName", ""),
                "icon_name": dialog_config.get("icon_name", ""),
            },
        )

    def apply_brush_icon(self, button, brush_name):
        if not brush_name:
            return
        try:
            preset = Krita.instance().resources("preset").get(brush_name)
            if not preset:
                button.setText("?")
                return
            if self._set_brush_pixmap(button, preset):
                return
        except Exception as exc:
            print(f"Quick Access Palette brush icon error: {exc}")
        button.setText(brush_name[:1] if brush_name else "?")
