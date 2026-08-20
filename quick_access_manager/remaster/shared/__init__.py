"""Shared model and layout logic for the remastered palette."""

from .layout_engine import FreeGridLayoutEngine, LayoutResult, PlacementIssue
from .models import (
    ACTION_ITEM,
    BRUSH_ITEM,
    COLOR_ITEM,
    COLOR_SWATCH_BORDER_COLOR,
    COLOR_SWATCH_BORDER_WIDTH,
    DEFAULT_ACTION_COL_SPAN,
    DEFAULT_COL_SPAN,
    DOCKER_TOGGLE_ITEM,
    LABEL_ITEM,
    SCRIPT_ITEM,
    SEPARATOR_ITEM,
    PaletteDocument,
    PaletteGrid,
    PaletteItem,
    PaletteTab,
)

__all__ = [
    "ACTION_ITEM",
    "BRUSH_ITEM",
    "COLOR_ITEM",
    "COLOR_SWATCH_BORDER_COLOR",
    "COLOR_SWATCH_BORDER_WIDTH",
    "DEFAULT_ACTION_COL_SPAN",
    "DEFAULT_COL_SPAN",
    "DOCKER_TOGGLE_ITEM",
    "LABEL_ITEM",
    "SCRIPT_ITEM",
    "SEPARATOR_ITEM",
    "FreeGridLayoutEngine",
    "LayoutResult",
    "PaletteDocument",
    "PaletteGrid",
    "PaletteItem",
    "PaletteTab",
    "PlacementIssue",
]
