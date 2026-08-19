"""JSON repository for Quick Access Palette remaster data."""

import os

from ..shared import PaletteDocument, PaletteGrid, PaletteTab
from .json_cache import read_json, write_json
from .paths import get_palette_config_path, get_palette_settings_path

DEFAULT_COLUMNS = 8


class PaletteRepository:
    """Load and save the remastered palette config.

    Grid/tab data lives in `quick_access_palette.json`; settings (docker icon
    size, HueSVC, Quick Adjust, etc.) live in a separate `settings.json` so
    the two can evolve independently.
    """

    def __init__(self, path: str | None = None, settings_path: str | None = None):
        self.path = path or get_palette_config_path()
        self.settings_path = settings_path or get_palette_settings_path()

    def load(self) -> PaletteDocument:
        if not os.path.exists(self.path):
            document = self.create_default_document()
            self.save(document)
            return document

        try:
            data = read_json(self.path, default={})
        except Exception:
            backup_path = self.path + ".broken"
            try:
                os.replace(self.path, backup_path)
            except Exception:
                pass
            document = self.create_default_document()
            self.save(document)
            return document

        document = PaletteDocument.from_dict(data)
        settings = self._load_settings()
        if not settings and isinstance(data.get("settings"), dict):
            # One-time migration from the old combined file.
            settings = data["settings"]
            self._save_settings(settings)
        document.settings = settings
        return document

    def save(self, document: PaletteDocument):
        grid_data = document.to_dict()
        grid_data.pop("settings", None)
        write_json(self.path, grid_data)
        self._save_settings(document.settings)

    def _load_settings(self) -> dict:
        try:
            return read_json(self.settings_path, default={}) or {}
        except Exception:
            return {}

    def _save_settings(self, settings: dict):
        write_json(self.settings_path, settings)

    def create_default_document(self) -> PaletteDocument:
        grid = PaletteGrid(
            id="main-grid", name="Main", columns=DEFAULT_COLUMNS, items=[]
        )
        tab = PaletteTab(id="main-tab", name="Main", grids=[grid])
        return PaletteDocument(
            tabs=[tab],
            active_tab_id=tab.id,
            settings={
                "default": {"docker_icon_size": 42},
                "popup": {"popup_icon_size": 42},
            },
        )
