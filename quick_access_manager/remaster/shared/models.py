"""Data models for the remastered Quick Access Palette.

These classes intentionally avoid Krita and Qt dependencies so they can be used
by the Docker, popup, config repository, and tests.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

BRUSH_ITEM = "brush"
ACTION_ITEM = "action"
LABEL_ITEM = "label"
SEPARATOR_ITEM = "separator"
DOCKER_TOGGLE_ITEM = "docker_toggle"
COLOR_ITEM = "color"
SCRIPT_ITEM = "script"
BRUSH_SIZE_ITEM = "brush_size"
BRUSH_BLEND_MODE_ITEM = "brush_blend_mode"

ITEM_TYPES = {
    BRUSH_ITEM,
    ACTION_ITEM,
    LABEL_ITEM,
    SEPARATOR_ITEM,
    DOCKER_TOGGLE_ITEM,
    COLOR_ITEM,
    SCRIPT_ITEM,
    BRUSH_SIZE_ITEM,
    BRUSH_BLEND_MODE_ITEM,
}
DEFAULT_ACTION_COL_SPAN = 2
DEFAULT_ROW_SPAN = 1
DEFAULT_COL_SPAN = 1
# Default height (in rows) for a newly-added vertical Separator - mirrors
# DEFAULT_ACTION_COL_SPAN's role for the horizontal one, just tall enough to
# read as a divider without the user needing to resize it immediately.
DEFAULT_V_SEPARATOR_ROW_SPAN = 3

SEPARATOR_ORIENTATION_HORIZONTAL = "horizontal"
SEPARATOR_ORIENTATION_VERTICAL = "vertical"

# A neutral mid-gray frame around a Color Swatch item's fill, so the swatch
# isn't rendered edge-to-edge against its neighbors - simultaneous contrast
# (a color looking different depending on what's next to it) makes an
# adjacent-color read unreliable without a neutral buffer between them.
COLOR_SWATCH_BORDER_COLOR = "#808080"
COLOR_SWATCH_BORDER_WIDTH = 3


@dataclass
class PaletteItem:
    """One item placed on a free-layout palette grid."""

    id: str
    type: str
    row: int
    col: int
    row_span: int = DEFAULT_ROW_SPAN
    col_span: int = DEFAULT_COL_SPAN
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.type not in ITEM_TYPES:
            raise ValueError(f"Unsupported palette item type: {self.type}")
        self.row = int(self.row)
        self.col = int(self.col)
        self.row_span = max(1, int(self.row_span))
        self.col_span = max(1, int(self.col_span))
        if self.type == BRUSH_ITEM:
            self.row_span = 1
            self.col_span = 1

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
        config: dict[str, Any] | None = None,
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
        col_span: int | None = None,
        row_span: int | None = None,
        orientation: str = SEPARATOR_ORIENTATION_HORIZONTAL,
    ):
        """A horizontal separator resizes by col_span (row_span pinned to 1);
        a vertical one resizes by row_span (col_span pinned to 1) - the two
        orientations grow along different axes, never both."""
        vertical = orientation == SEPARATOR_ORIENTATION_VERTICAL
        return cls(
            id=item_id,
            type=SEPARATOR_ITEM,
            row=row,
            col=col,
            row_span=(
                row_span if row_span is not None else DEFAULT_V_SEPARATOR_ROW_SPAN
            )
            if vertical
            else 1,
            col_span=1 if vertical else (col_span if col_span is not None else DEFAULT_ACTION_COL_SPAN),
            payload={"orientation": orientation},
        )

    @classmethod
    def create_docker_toggle(
        cls,
        item_id: str,
        docker_id: str,
        row: int = 0,
        col: int = 0,
        col_span: int = DEFAULT_ACTION_COL_SPAN,
        row_span: int = DEFAULT_ROW_SPAN,
        config: dict[str, Any] | None = None,
    ):
        payload = {"docker_id": docker_id}
        if config:
            payload.update(config)
        if payload.get("icon_name"):
            row_span = 1
            col_span = 1
        return cls(
            id=item_id,
            type=DOCKER_TOGGLE_ITEM,
            row=row,
            col=col,
            row_span=row_span,
            col_span=col_span,
            payload=payload,
        )

    @classmethod
    def create_color(
        cls,
        item_id: str,
        color: str = "#ffffff",
        row: int = 0,
        col: int = 0,
    ):
        return cls(
            id=item_id,
            type=COLOR_ITEM,
            row=row,
            col=col,
            row_span=1,
            col_span=1,
            payload={"color": color},
        )

    @classmethod
    def create_script(
        cls,
        item_id: str,
        script_path: str,
        row: int = 0,
        col: int = 0,
        col_span: int = DEFAULT_ACTION_COL_SPAN,
        row_span: int = DEFAULT_ROW_SPAN,
        config: dict[str, Any] | None = None,
    ):
        payload = {"script_path": script_path}
        if config:
            payload.update(config)
        if payload.get("icon_name"):
            row_span = 1
            col_span = 1
        return cls(
            id=item_id,
            type=SCRIPT_ITEM,
            row=row,
            col=col,
            row_span=row_span,
            col_span=col_span,
            payload=payload,
        )

    @classmethod
    def create_brush_size(
        cls,
        item_id: str,
        text: str,
        row: int = 0,
        col: int = 0,
        config: dict[str, Any] | None = None,
    ):
        """A 1x1 button that sets the active brush's size to `text` (digits
        only - validated by the config dialogs, not enforced here) when
        clicked."""
        payload = {"text": text}
        if config:
            payload.update(config)
        return cls(
            id=item_id,
            type=BRUSH_SIZE_ITEM,
            row=row,
            col=col,
            row_span=1,
            col_span=1,
            payload=payload,
        )

    @classmethod
    def create_brush_blend_mode(
        cls,
        item_id: str,
        text: str,
        row: int = 0,
        col: int = 0,
        config: dict[str, Any] | None = None,
    ):
        """A 2x1 button that sets the active brush's blend mode to `text`
        (a Krita blend mode id, e.g. "multiply" - free text, not validated
        here) when clicked, via view.setCurrentBlendingMode()."""
        payload = {"text": text}
        if config:
            payload.update(config)
        return cls(
            id=item_id,
            type=BRUSH_BLEND_MODE_ITEM,
            row=row,
            col=col,
            row_span=1,
            col_span=2,
            payload=payload,
        )

    @property
    def right(self) -> int:
        return self.col + self.col_span

    @property
    def bottom(self) -> int:
        return self.row + self.row_span

    def cells(self) -> Iterable[tuple[int, int]]:
        for row in range(self.row, self.bottom):
            for col in range(self.col, self.right):
                yield row, col

    def copy_with(self, **changes: Any):
        data = self.to_dict()
        data.update(changes)
        return PaletteItem.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]):
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
    items: list[PaletteItem] = field(default_factory=list)

    def __post_init__(self):
        self.columns = max(1, int(self.columns))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "columns": self.columns,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
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
    grids: list[PaletteGrid] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "grids": [grid.to_dict() for grid in self.grids],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", "Tab")),
            grids=[PaletteGrid.from_dict(grid) for grid in data.get("grids", [])],
        )


@dataclass
class PaletteDocument:
    tabs: list[PaletteTab] = field(default_factory=list)
    active_tab_id: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "active_tab_id": self.active_tab_id,
            "settings": dict(self.settings),
            "tabs": [tab.to_dict() for tab in self.tabs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(
            active_tab_id=data.get("active_tab_id"),
            settings=dict(data.get("settings", {})),
            tabs=[PaletteTab.from_dict(tab) for tab in data.get("tabs", [])],
        )
