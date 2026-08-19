"""Shared model and layout logic for the remastered palette."""

from .layout_engine import FreeGridLayoutEngine, LayoutResult, PlacementIssue
from .models import (
    ACTION_ITEM,
    BRUSH_ITEM,
    LABEL_ITEM,
    SEPARATOR_ITEM,
    DEFAULT_ACTION_COL_SPAN,
    PaletteDocument,
    PaletteGrid,
    PaletteItem,
    PaletteTab,
)

__all__ = [
    "ACTION_ITEM",
    "BRUSH_ITEM",
    "LABEL_ITEM",
    "SEPARATOR_ITEM",
    "DEFAULT_ACTION_COL_SPAN",
    "FreeGridLayoutEngine",
    "LayoutResult",
    "PlacementIssue",
    "PaletteDocument",
    "PaletteGrid",
    "PaletteItem",
    "PaletteTab",
]
