"""Controller for Quick Access Palette document mutations."""

from typing import Optional
from uuid import uuid4

from ...infrastructure import PaletteRepository
from ...shared import ACTION_ITEM, LABEL_ITEM, FreeGridLayoutEngine, LayoutResult, PaletteDocument, PaletteGrid, PaletteItem


class PaletteController:
    """Owns palette document state and applies layout mutations."""

    def __init__(self, repository: Optional[PaletteRepository] = None):
        self.repository = repository or PaletteRepository()
        self.document = self.repository.load()
        self.normalize_action_spans()

    def normalize_action_spans(self):
        changed = False
        for tab in self.document.tabs:
            for grid in tab.grids:
                for index, item in enumerate(grid.items):
                    if item.type != ACTION_ITEM:
                        continue
                    expected_col_span = 1 if item.payload.get("icon_name") else max(2, item.col_span)
                    if item.col_span != expected_col_span:
                        grid.items[index] = item.copy_with(col_span=expected_col_span)
                        changed = True
        if changed:
            self.save()
    @property
    def active_tab_id(self) -> Optional[str]:
        return self.document.active_tab_id

    def save(self):
        self.repository.save(self.document)

    def active_tab(self):
        if self.document.active_tab_id:
            for tab in self.document.tabs:
                if tab.id == self.document.active_tab_id:
                    return tab
        if self.document.tabs:
            self.document.active_tab_id = self.document.tabs[0].id
            return self.document.tabs[0]
        return None

    def active_grid(self) -> Optional[PaletteGrid]:
        tab = self.active_tab()
        if not tab or not tab.grids:
            return None
        return tab.grids[0]

    def set_active_tab(self, tab_id: str):
        if any(tab.id == tab_id for tab in self.document.tabs):
            self.document.active_tab_id = tab_id
            self.save()

    def add_tab(self, name: str):
        tab_id = self._new_id("tab")
        grid = PaletteGrid(id=self._new_id("grid"), name="Main", columns=8, items=[])
        from ...shared import PaletteTab

        tab = PaletteTab(id=tab_id, name=name, grids=[grid])
        self.document.tabs.append(tab)
        self.document.active_tab_id = tab_id
        self.save()
        return tab

    def add_brush(self, brush_name: str, row: int = 0, col: int = 0) -> LayoutResult:
        grid = self._require_active_grid()
        item = PaletteItem.create_brush(self._new_id("brush"), brush_name, row=row, col=col)
        return self._apply_result(grid, FreeGridLayoutEngine(grid.columns).add_item(grid.items, item))

    def add_action(self, action_id: str, config=None, row: int = 0, col: int = 0) -> LayoutResult:
        grid = self._require_active_grid()
        item_config = config or {}
        item = PaletteItem.create_action(
            self._new_id("action"),
            action_id,
            row=row,
            col=col,
            col_span=1 if item_config.get("icon_name") else 2,
            config=item_config,
        )
        return self._apply_result(grid, FreeGridLayoutEngine(grid.columns).add_item(grid.items, item))

    def add_label(self, text: str, row: int = 0, col: int = 0) -> LayoutResult:
        grid = self._require_active_grid()
        item = PaletteItem.create_label(self._new_id("label"), text, row=row, col=col)
        return self._apply_result(grid, FreeGridLayoutEngine(grid.columns).add_item(grid.items, item))

    def add_separator(self, row: int = 0, col: int = 0) -> LayoutResult:
        grid = self._require_active_grid()
        item = PaletteItem.create_separator(self._new_id("separator"), row=row, col=col)
        return self._apply_result(grid, FreeGridLayoutEngine(grid.columns).add_item(grid.items, item))

    def remove_item(self, item_id: str) -> LayoutResult:
        grid = self._require_active_grid()
        grid.items = [item for item in grid.items if item.id != item_id]
        result = FreeGridLayoutEngine(grid.columns).compact(grid.items)
        return self._apply_result(grid, result)

    def update_action_item(self, item_id: str, config) -> LayoutResult:
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != ACTION_ITEM:
                    raise ValueError("Palette item is not an action: {0}".format(item_id))
                payload = dict(item.payload)
                payload.update(config)
                col_span = 1 if payload.get("icon_name") else max(2, item.col_span)
                grid.items[index] = item.copy_with(payload=payload, col_span=col_span)
                result = FreeGridLayoutEngine(grid.columns).compact(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError("Palette item not found: {0}".format(item_id))

    def update_label_item(self, item_id: str, config) -> LayoutResult:
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != LABEL_ITEM:
                    raise ValueError("Palette item is not a label: {0}".format(item_id))
                payload = dict(item.payload)
                payload.update(config)
                grid.items[index] = item.copy_with(payload=payload)
                result = FreeGridLayoutEngine(grid.columns).compact(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError("Palette item not found: {0}".format(item_id))
    def compact_active_grid(self) -> LayoutResult:
        grid = self._require_active_grid()
        return self._apply_result(grid, FreeGridLayoutEngine(grid.columns).compact(grid.items), compact=False)

    def move_item(self, item_id: str, row: int, col: int) -> LayoutResult:
        grid = self._require_active_grid()
        return self._apply_result(
            grid, FreeGridLayoutEngine(grid.columns).move_item(grid.items, item_id, row, col)
        )

    def resize_item(self, item_id: str, row_span=None, col_span=None) -> LayoutResult:
        grid = self._require_active_grid()
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).resize_item(
                grid.items, item_id, row_span=row_span, col_span=col_span
            ),
        )

    def replace_active_grid_items(self, items, compact: bool = False) -> LayoutResult:
        grid = self._require_active_grid()
        result = FreeGridLayoutEngine(grid.columns).validate(items)
        return self._apply_result(grid, result, compact=compact)
    def set_columns(self, columns: int) -> LayoutResult:
        grid = self._require_active_grid()
        grid.columns = max(1, int(columns))
        result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
        self.save()
        return result

    def validate_active_grid(self) -> LayoutResult:
        grid = self._require_active_grid()
        return FreeGridLayoutEngine(grid.columns).validate(grid.items)

    def _apply_result(self, grid: PaletteGrid, result: LayoutResult, compact: bool = True) -> LayoutResult:
        if compact:
            result = FreeGridLayoutEngine(grid.columns).compact(result.items)
        grid.items = result.items
        self.save()
        return result

    def _require_active_grid(self) -> PaletteGrid:
        grid = self.active_grid()
        if grid is None:
            raise ValueError("Quick Access Palette has no active grid.")
        return grid

    def _new_id(self, prefix: str) -> str:
        return "{0}-{1}".format(prefix, uuid4().hex[:12])
