"""Item add/update/remove/move/resize and grid-level layout operations."""

from ...shared import (
    ACTION_ITEM,
    BRUSH_BLEND_MODE_ITEM,
    BRUSH_SIZE_ITEM,
    COLOR_ITEM,
    DEFAULT_ACTION_COL_SPAN,
    DOCKER_TOGGLE_ITEM,
    LABEL_ITEM,
    SCRIPT_ITEM,
    SEPARATOR_ITEM,
    SEPARATOR_ORIENTATION_HORIZONTAL,
    SEPARATOR_ORIENTATION_VERTICAL,
    FreeGridLayoutEngine,
    LayoutResult,
    PaletteGrid,
    PaletteItem,
)


class ItemCrudMixin:
    """Requires `self.document`, `self.save()`, `self._new_id()`,
    `self.active_grid()`, `self._resolve_position()`, item span helpers, and
    `self._advance_sequential_cursor()` from the composed controller."""

    def add_brush(
        self, brush_name: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_brush(
            self._new_id("brush"), brush_name, row=row, col=col
        )
        return self._add_new_item(grid, item)

    def add_action(
        self, action_id: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        col_span = self._action_col_span(action_id)
        row, col = self._resolve_position(grid, row, col, col_span=col_span)
        item = PaletteItem.create_action(
            self._new_id("action"),
            action_id,
            row=row,
            col=col,
            col_span=col_span,
        )
        return self._add_new_item(grid, item)

    def add_label(
        self, text: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(
            grid, row, col, col_span=DEFAULT_ACTION_COL_SPAN
        )
        item = PaletteItem.create_label(self._new_id("label"), text, row=row, col=col)
        return self._add_new_item(grid, item)

    def add_separator(
        self,
        row: int | None = None,
        col: int | None = None,
        orientation: str = SEPARATOR_ORIENTATION_HORIZONTAL,
    ) -> LayoutResult:
        grid = self._require_active_grid()
        col_span = 1 if orientation == SEPARATOR_ORIENTATION_VERTICAL else DEFAULT_ACTION_COL_SPAN
        row, col = self._resolve_position(grid, row, col, col_span=col_span)
        item = PaletteItem.create_separator(
            self._new_id("separator"), row=row, col=col, orientation=orientation
        )
        return self._add_new_item(grid, item)

    def add_docker_toggle(
        self, docker_id: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        col_span = self._docker_toggle_col_span(docker_id)
        row, col = self._resolve_position(grid, row, col, col_span=col_span)
        item = PaletteItem.create_docker_toggle(
            self._new_id("docker_toggle"),
            docker_id,
            row=row,
            col=col,
            col_span=col_span,
        )
        return self._add_new_item(grid, item)

    def add_color(
        self, color: str = "#ffffff", row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_color(self._new_id("color"), color, row=row, col=col)
        return self._add_new_item(grid, item)

    def add_script(
        self,
        script_path: str,
        config=None,
        row: int | None = None,
        col: int | None = None,
    ) -> LayoutResult:
        grid = self._require_active_grid()
        col_span = self._script_col_span(config)
        row, col = self._resolve_position(grid, row, col, col_span=col_span)
        item = PaletteItem.create_script(
            self._new_id("script"),
            script_path,
            row=row,
            col=col,
            col_span=col_span,
            config=config,
        )
        return self._add_new_item(grid, item)

    def add_brush_size(
        self,
        text: str,
        config=None,
        row: int | None = None,
        col: int | None = None,
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_brush_size(
            self._new_id("brush_size"), text, row=row, col=col, config=config
        )
        return self._add_new_item(grid, item)

    def add_brush_blend_mode(
        self,
        text: str,
        config=None,
        row: int | None = None,
        col: int | None = None,
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col, col_span=2)
        item = PaletteItem.create_brush_blend_mode(
            self._new_id("brush_blend_mode"), text, row=row, col=col, config=config
        )
        return self._add_new_item(grid, item)

    def _add_new_item(self, grid: PaletteGrid, item: PaletteItem) -> LayoutResult:
        result = self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )
        self._advance_sequential_cursor(grid, result, item.id)
        return result

    def remove_item(self, item_id: str) -> LayoutResult:
        grid = self._require_active_grid()
        grid.items = [item for item in grid.items if item.id != item_id]
        result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
        return self._apply_result(grid, result, compact=False)

    def update_action_item(self, item_id: str) -> LayoutResult:
        """Recompute an Action item's col_span from the shared Alias Config."""
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != ACTION_ITEM:
                    raise ValueError(f"Palette item is not an action: {item_id}")
                col_span = self._icon_text_col_span(
                    item, action_aliases=self.alias_repository.load().get("actions", {})
                )
                if col_span != item.col_span or item.row_span != 1:
                    grid.items[index] = item.copy_with(row_span=1, col_span=col_span)
                result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError(f"Palette item not found: {item_id}")

    def update_label_item(self, item_id: str, config) -> LayoutResult:
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != LABEL_ITEM:
                    raise ValueError(f"Palette item is not a label: {item_id}")
                payload = dict(item.payload)
                payload.update(config)
                grid.items[index] = item.copy_with(payload=payload)
                result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError(f"Palette item not found: {item_id}")

    def update_docker_toggle_item(self, item_id: str, docker_id: str) -> LayoutResult:
        """Point an existing Docker Toggle item at a (possibly different) docker."""
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != DOCKER_TOGGLE_ITEM:
                    raise ValueError(f"Palette item is not a docker toggle: {item_id}")
                payload = {"docker_id": docker_id}
                col_span = self._docker_toggle_col_span(
                    docker_id, min_col_span=item.col_span
                )
                grid.items[index] = item.copy_with(
                    row_span=1, col_span=col_span, payload=payload
                )
                result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError(f"Palette item not found: {item_id}")

    def update_color_item(self, item_id: str, config) -> LayoutResult:
        return self._update_payload(item_id, COLOR_ITEM, config)

    def update_script_item(self, item_id: str, config) -> LayoutResult:
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != SCRIPT_ITEM:
                    raise ValueError(f"Palette item is not a script: {item_id}")
                payload = dict(item.payload)
                payload.update(config)
                col_span = self._script_col_span(payload, min_col_span=item.col_span)
                grid.items[index] = item.copy_with(
                    row_span=1, col_span=col_span, payload=payload
                )
                result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError(f"Palette item not found: {item_id}")

    def update_brush_size_item(self, item_id: str, config) -> LayoutResult:
        return self._update_payload(item_id, BRUSH_SIZE_ITEM, config)

    def update_brush_blend_mode_item(self, item_id: str, config) -> LayoutResult:
        return self._update_payload(item_id, BRUSH_BLEND_MODE_ITEM, config)

    def update_separator_item(self, item_id: str, config) -> LayoutResult:
        return self._update_payload(item_id, SEPARATOR_ITEM, config)

    def _update_payload(self, item_id: str, expected_type: str, config) -> LayoutResult:
        grid = self._require_active_grid()
        for index, item in enumerate(grid.items):
            if item.id == item_id:
                if item.type != expected_type:
                    raise ValueError(
                        f"Palette item is not a {expected_type}: {item_id}"
                    )
                payload = dict(item.payload)
                payload.update(config)
                grid.items[index] = item.copy_with(payload=payload)
                result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError(f"Palette item not found: {item_id}")

    def compact_active_grid(self) -> LayoutResult:
        grid = self._require_active_grid()
        return self._apply_result(
            grid, FreeGridLayoutEngine(grid.columns).compact(grid.items), compact=False
        )

    def move_item(self, item_id: str, row: int, col: int) -> LayoutResult:
        grid = self._require_active_grid()
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).move_item(grid.items, item_id, row, col),
            compact=False,
        )

    def resize_item(self, item_id: str, row_span=None, col_span=None) -> LayoutResult:
        grid = self._require_active_grid()
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).resize_item(
                grid.items, item_id, row_span=row_span, col_span=col_span
            ),
            compact=False,
        )

    def replace_active_grid_items(self, items, compact: bool = False) -> LayoutResult:
        grid = self._require_active_grid()
        result = FreeGridLayoutEngine(grid.columns).validate(items)
        return self._apply_result(grid, result, compact=compact)

    def replace_tab_grid_items(
        self, tab_id: str, items, compact: bool = False
    ) -> LayoutResult:
        """Replace the items of a specific tab's grid (used by the multi-tab Grid Edit dialog)."""
        for tab in self.document.tabs:
            if tab.id == tab_id and tab.grids:
                grid = tab.grids[0]
                result = FreeGridLayoutEngine(grid.columns).validate(items)
                return self._apply_result(grid, result, compact=compact)
        raise ValueError(f"Palette tab not found: {tab_id}")

    def set_columns(self, columns: int) -> LayoutResult:
        grid = self._require_active_grid()
        grid.columns = max(1, int(columns))
        result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
        self.save()
        return result

    def validate_active_grid(self) -> LayoutResult:
        grid = self._require_active_grid()
        return FreeGridLayoutEngine(grid.columns).validate(grid.items)

    def _apply_result(
        self, grid: PaletteGrid, result: LayoutResult, compact: bool = True
    ) -> LayoutResult:
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
