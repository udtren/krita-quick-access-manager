"""Free-layout grid logic for Quick Access Palette.

The engine owns placement rules only. UI code should translate mouse/drag events
into add, move, or resize operations and then render the returned items and
validation state.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .models import PaletteGrid, PaletteItem


@dataclass(frozen=True)
class PlacementIssue:
    item_id: str
    code: str
    message: str


@dataclass
class LayoutResult:
    items: List[PaletteItem]
    issues: List[PlacementIssue] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.issues

    def issues_by_item(self) -> Dict[str, List[PlacementIssue]]:
        grouped: Dict[str, List[PlacementIssue]] = {}
        for issue in self.issues:
            grouped.setdefault(issue.item_id, []).append(issue)
        return grouped


class FreeGridLayoutEngine:
    """Places variable-span palette items in a bounded-column free grid."""

    def __init__(self, columns: int):
        self.columns = max(1, int(columns))

    def add_item(self, items: Sequence[PaletteItem], new_item: PaletteItem) -> LayoutResult:
        if any(item.id == new_item.id for item in items):
            raise ValueError("Duplicate palette item id: {0}".format(new_item.id))
        return self._place_with_push(list(items), new_item)

    def move_item(
        self, items: Sequence[PaletteItem], item_id: str, row: int, col: int
    ) -> LayoutResult:
        moving = self._find_required(items, item_id).copy_with(row=row, col=col)
        rest = [item for item in items if item.id != item_id]
        return self._place_with_push(rest, moving)

    def resize_item(
        self,
        items: Sequence[PaletteItem],
        item_id: str,
        row_span: Optional[int] = None,
        col_span: Optional[int] = None,
    ) -> LayoutResult:
        current = self._find_required(items, item_id)
        changes = {}
        if row_span is not None:
            changes["row_span"] = max(1, int(row_span))
        if col_span is not None:
            changes["col_span"] = max(1, int(col_span))
        resized = current.copy_with(**changes)
        rest = [item for item in items if item.id != item_id]
        return self._place_with_push(rest, resized)

    def validate(self, items: Sequence[PaletteItem]) -> LayoutResult:
        issues: List[PlacementIssue] = []
        for item in items:
            issues.extend(self._bounds_issues(item))
        for index, item in enumerate(items):
            for other in items[index + 1 :]:
                if self._overlaps(item, other):
                    issues.append(
                        PlacementIssue(
                            item.id,
                            "overlap",
                            "Item overlaps with {0}.".format(other.id),
                        )
                    )
                    issues.append(
                        PlacementIssue(
                            other.id,
                            "overlap",
                            "Item overlaps with {0}.".format(item.id),
                        )
                    )
        return LayoutResult(list(items), issues)

    def compact(self, items: Sequence[PaletteItem]) -> LayoutResult:
        """Pack items left-to-right without holes, preserving visual order."""
        placed: List[PaletteItem] = []
        for item in self._stable_order(items):
            candidate = item.copy_with(row=0, col=0)
            if candidate.col_span > self.columns:
                placed.append(candidate)
                continue
            candidate = self._first_free_position(candidate, placed)
            placed.append(candidate)
        return self.validate(placed)
    def change_columns(self, items: Sequence[PaletteItem], columns: int) -> LayoutResult:
        """Return validation for a different column count without moving data."""
        return FreeGridLayoutEngine(columns).validate(items)

    def normalize_grid(self, grid: PaletteGrid) -> LayoutResult:
        """Validate the current stored grid without changing item positions."""
        return FreeGridLayoutEngine(grid.columns).validate(grid.items)

    def _place_with_push(
        self, existing_items: List[PaletteItem], active_item: PaletteItem
    ) -> LayoutResult:
        active_item = active_item.copy_with(row=max(0, active_item.row), col=max(0, active_item.col))

        if active_item.col_span > self.columns:
            items = [active_item] + list(existing_items)
            return LayoutResult(items, self.validate(items).issues)

        placed: List[PaletteItem] = [active_item]
        for item in self._stable_order(existing_items):
            candidate = item.copy_with(row=max(0, item.row), col=max(0, item.col))
            if candidate.col_span > self.columns:
                placed.append(candidate)
                continue
            if self._needs_reposition(candidate, placed):
                candidate = self._first_free_position(candidate, placed)
            placed.append(candidate)
        return self.validate(placed)

    def _first_free_position(
        self, item: PaletteItem, placed: Sequence[PaletteItem]
    ) -> PaletteItem:
        cursor = self._linear_index(item.row, item.col)
        while True:
            row, col = self._row_col(cursor)
            if col + item.col_span <= self.columns:
                candidate = item.copy_with(row=row, col=col)
                if not self._needs_reposition(candidate, placed):
                    return candidate
            cursor += 1

    def _needs_reposition(
        self, item: PaletteItem, placed: Sequence[PaletteItem]
    ) -> bool:
        if self._bounds_issues(item):
            return True
        return any(self._overlaps(item, other) for other in placed)

    def _bounds_issues(self, item: PaletteItem) -> List[PlacementIssue]:
        issues: List[PlacementIssue] = []
        if item.row < 0 or item.col < 0:
            issues.append(
                PlacementIssue(item.id, "negative_position", "Item has a negative position.")
            )
        if item.col_span > self.columns:
            issues.append(
                PlacementIssue(
                    item.id,
                    "too_wide",
                    "Item width exceeds the configured column count.",
                )
            )
        elif item.col + item.col_span > self.columns:
            issues.append(
                PlacementIssue(
                    item.id,
                    "overflow",
                    "Item extends beyond the configured column count.",
                )
            )
        return issues

    def occupied_cells(self, items: Iterable[PaletteItem]) -> Dict[Tuple[int, int], str]:
        occupied: Dict[Tuple[int, int], str] = {}
        for item in items:
            if self._bounds_issues(item):
                continue
            for cell in item.cells():
                occupied[cell] = item.id
        return occupied

    def _overlaps(self, item: PaletteItem, other: PaletteItem) -> bool:
        return not (
            item.right <= other.col
            or other.right <= item.col
            or item.bottom <= other.row
            or other.bottom <= item.row
        )

    def _stable_order(self, items: Sequence[PaletteItem]) -> List[PaletteItem]:
        return sorted(
            items,
            key=lambda item: (self._linear_index(max(0, item.row), max(0, item.col)), item.id),
        )

    def _linear_index(self, row: int, col: int) -> int:
        return max(0, int(row)) * self.columns + max(0, int(col))

    def _row_col(self, index: int) -> Tuple[int, int]:
        return index // self.columns, index % self.columns

    def _find_required(self, items: Sequence[PaletteItem], item_id: str) -> PaletteItem:
        for item in items:
            if item.id == item_id:
                return item
        raise ValueError("Palette item not found: {0}".format(item_id))
