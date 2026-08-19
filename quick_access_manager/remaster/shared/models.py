"""Data models for the remastered Quick Access Palette.

These classes intentionally avoid Krita and Qt dependencies so they can be used
by the Docker, popup, config repository, and tests.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


BRUSH_ITEM = "brush"
ACTION_ITEM = "action"
LABEL_ITEM = "label"
SEPARATOR_ITEM = "separator"

ITEM_TYPES = {BRUSH_ITEM, ACTION_ITEM, LABEL_ITEM, SEPARATOR_ITEM}
DEFAULT_ACTION_COL_SPAN = 2
DEFAULT_ROW_SPAN = 1
DEFAULT_COL_SPAN = 1


@dataclass
class PaletteItem:
    """One item placed on a free-layout palette grid."""

    id: str
    type: str
    row: int
    col: int
    row_span: int = DEFAULT_ROW_SPAN
    col_span: int = DEFAULT_COL_SPAN
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.type not in ITEM_TYPES:
            raise ValueError("Unsupported palette item type: {0}".format(self.type))
        self.row = int(self.row)
        self.col = int(self.col)
        self.row_span = max(1, int(self.row_span))
        self.col_span = max(1, int(self.col_span))
        if self.type == BRUSH_ITEM:
            self.row_span = 1
            self.col_span = 1
        elif self.type == ACTION_ITEM and "col_span" not in self.payload:
            self.col_span = max(1, self.col_span)

    @classmethod
    def create_brush(cls, item_id: str, brush_name: str, row: int = 0, col: int = 0):
        return cls(
            id=item_id,
            type=BRUSH_ITEM,
            row=row,
            col=col,
            row_span=1,
            col_span=1,
            payload={"brush_name": brush_name},
        )

    @classmethod
    def create_action(
        cls,
        item_id: str,
        action_id: str,
        row: int = 0,
        col: int = 0,
        col_span: int = DEFAULT_ACTION_COL_SPAN,
        row_span: int = DEFAULT_ROW_SPAN,
        config: Optional[Dict[str, Any]] = None,
    ):
        payload = {"action_id": action_id}
        if config:
            payload.update(config)
        return cls(
            id=item_id,
            type=ACTION_ITEM,
            row=row,
            col=col,
            row_span=row_span,
            col_span=col_span,
            payload=payload,
        )

    @classmethod
    def create_label(
        cls,
        item_id: str,
        text: str,
        row: int = 0,
        col: int = 0,
        col_span: int = DEFAULT_ACTION_COL_SPAN,
    ):
        return cls(
            id=item_id,
            type=LABEL_ITEM,
            row=row,
            col=col,
            row_span=1,
            col_span=col_span,
            payload={"text": text},
        )

    @classmethod
    def create_separator(
        cls,
        item_id: str,
        row: int = 0,
        col: int = 0,
        col_span: int = DEFAULT_ACTION_COL_SPAN,
    ):
        return cls(
            id=item_id,
            type=SEPARATOR_ITEM,
            row=row,
            col=col,
            row_span=1,
            col_span=col_span,
        )

    @property
    def right(self) -> int:
        return self.col + self.col_span

    @property
    def bottom(self) -> int:
        return self.row + self.row_span

    def cells(self) -> Iterable[Tuple[int, int]]:
        for row in range(self.row, self.bottom):
            for col in range(self.col, self.right):
                yield row, col

    def copy_with(self, **changes: Any):
        data = self.to_dict()
        data.update(changes)
        return PaletteItem.from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "row": self.row,
            "col": self.col,
            "row_span": self.row_span,
            "col_span": self.col_span,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            row=int(data.get("row", 0)),
            col=int(data.get("col", 0)),
            row_span=int(data.get("row_span", DEFAULT_ROW_SPAN)),
            col_span=int(data.get("col_span", DEFAULT_COL_SPAN)),
            payload=dict(data.get("payload", {})),
        )


@dataclass
class PaletteGrid:
    id: str
    name: str
    columns: int
    items: List[PaletteItem] = field(default_factory=list)

    def __post_init__(self):
        self.columns = max(1, int(self.columns))

    def get_item(self, item_id: str) -> Optional[PaletteItem]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "columns": self.columns,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", "Grid")),
            columns=int(data.get("columns", 8)),
            items=[PaletteItem.from_dict(item) for item in data.get("items", [])],
        )


@dataclass
class PaletteTab:
    id: str
    name: str
    grids: List[PaletteGrid] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "grids": [grid.to_dict() for grid in self.grids],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", "Tab")),
            grids=[PaletteGrid.from_dict(grid) for grid in data.get("grids", [])],
        )


@dataclass
class PaletteDocument:
    tabs: List[PaletteTab] = field(default_factory=list)
    active_tab_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "active_tab_id": self.active_tab_id,
            "settings": dict(self.settings),
            "tabs": [tab.to_dict() for tab in self.tabs],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            active_tab_id=data.get("active_tab_id"),
            settings=dict(data.get("settings", {})),
            tabs=[PaletteTab.from_dict(tab) for tab in data.get("tabs", [])],
        )



