"""JSON repository for Quick Access Palette remaster data."""

import json
import os
from typing import Optional

from ..shared import PaletteDocument, PaletteGrid, PaletteTab
from .paths import get_palette_config_path


DEFAULT_COLUMNS = 8


class PaletteRepository:
    """Load and save the remastered palette config."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or get_palette_config_path()

    def load(self) -> PaletteDocument:
        if not os.path.exists(self.path):
            document = self.create_default_document()
            self.save(document)
            return document

        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return PaletteDocument.from_dict(json.load(handle))
        except Exception:
            backup_path = self.path + ".broken"
            try:
                os.replace(self.path, backup_path)
            except Exception:
                pass
            document = self.create_default_document()
            self.save(document)
            return document

    def save(self, document: PaletteDocument):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(document.to_dict(), handle, indent=2, ensure_ascii=False)

    def create_default_document(self) -> PaletteDocument:
        grid = PaletteGrid(id="main-grid", name="Main", columns=DEFAULT_COLUMNS, items=[])
        tab = PaletteTab(id="main-tab", name="Main", grids=[grid])
        return PaletteDocument(tabs=[tab], active_tab_id=tab.id)
