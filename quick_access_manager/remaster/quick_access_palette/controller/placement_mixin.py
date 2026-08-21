"""New-item placement and icon/text sizing normalization."""

from ...shared import (
    ACTION_ITEM,
    DEFAULT_ACTION_COL_SPAN,
    DEFAULT_COL_SPAN,
    DOCKER_TOGGLE_ITEM,
    SCRIPT_ITEM,
    LayoutResult,
    PaletteGrid,
)


class PlacementMixin:
    """Requires `self.document`, `self.save()`, and `self.alias_repository`
    from the composed controller."""

    # ------------------------------------------------------------------
    # Sequential placement (Resources dialog)
    # ------------------------------------------------------------------
    def begin_sequential_placement(self):
        """Pin the grid's first empty row as the start of a fill sequence.

        Header menu adds keep dropping every new item on the current last
        empty row, but the Resources dialog can add many items in one sitting:
        there the items should fill that one row left-to-right and only then
        wrap to the next row, instead of every Add pushing the previous item
        down a row. The cursor is captured when the dialog opens and released
        by end_sequential_placement() when it closes.
        """
        grid = self.active_grid()
        if grid is None:
            self._sequential_cursor = None
            return
        self._sequential_cursor = {
            "grid_id": grid.id,
            "row": max((item.bottom for item in grid.items), default=0),
            "col": 0,
        }

    def end_sequential_placement(self):
        self._sequential_cursor = None

    def _active_cursor(self, grid: PaletteGrid):
        """The sequential cursor, but only while it belongs to `grid`."""
        cursor = self._sequential_cursor
        if cursor is not None and cursor.get("grid_id") == grid.id:
            return cursor
        return None

    def _advance_sequential_cursor(
        self, grid: PaletteGrid, result: LayoutResult, item_id: str
    ):
        """Park the cursor just right of where the item actually landed."""
        cursor = self._active_cursor(grid)
        if cursor is None:
            return
        placed = next((item for item in result.items if item.id == item_id), None)
        if placed is None:
            return
        row, col = placed.row, placed.col + placed.col_span
        if col >= grid.columns:
            row, col = placed.row + placed.row_span, 0
        cursor["row"], cursor["col"] = row, col

    # ------------------------------------------------------------------
    # Icon/text item col_span normalization
    # ------------------------------------------------------------------
    def normalize_action_spans(self):
        changed = False
        # Load the alias config once instead of once per item.
        alias_data = self.alias_repository.load()
        action_aliases = alias_data.get("actions", {})
        docker_aliases = alias_data.get("dockers", {})
        for tab in self.document.tabs:
            for grid in tab.grids:
                for index, item in enumerate(grid.items):
                    expected_col_span = self._icon_text_col_span(
                        item, action_aliases=action_aliases, docker_aliases=docker_aliases
                    )
                    if expected_col_span is None:
                        continue
                    if item.row_span != 1 or item.col_span != expected_col_span:
                        grid.items[index] = item.copy_with(
                            row_span=1, col_span=expected_col_span
                        )
                        changed = True
        if changed:
            self.save()

    def _action_col_span(
        self,
        action_id: str,
        min_col_span: int = DEFAULT_ACTION_COL_SPAN,
        aliases: dict | None = None,
    ) -> int:
        if aliases is None:
            aliases = self.alias_repository.load().get("actions", {})
        alias = aliases.get(action_id, {})
        if alias.get("icon_name"):
            return 1
        return max(1, min_col_span)

    def _docker_toggle_col_span(
        self,
        docker_id: str,
        min_col_span: int = DEFAULT_ACTION_COL_SPAN,
        aliases: dict | None = None,
    ) -> int:
        if aliases is None:
            aliases = self.alias_repository.load().get("dockers", {})
        alias = aliases.get(docker_id, {})
        if alias.get("icon_name"):
            return 1
        return max(1, min_col_span)

    def _script_col_span(
        self,
        config: dict | None = None,
        min_col_span: int = DEFAULT_ACTION_COL_SPAN,
    ) -> int:
        if config and config.get("icon_name"):
            return 1
        return max(1, min_col_span)

    def _icon_text_col_span(
        self,
        item,
        action_aliases: dict | None = None,
        docker_aliases: dict | None = None,
    ) -> int | None:
        if item.type == ACTION_ITEM:
            return self._action_col_span(
                item.payload.get("action_id", ""),
                min_col_span=item.col_span,
                aliases=action_aliases,
            )
        if item.type == DOCKER_TOGGLE_ITEM:
            return self._docker_toggle_col_span(
                item.payload.get("docker_id", ""),
                min_col_span=item.col_span,
                aliases=docker_aliases,
            )
        if item.type == SCRIPT_ITEM:
            return self._script_col_span(item.payload, min_col_span=item.col_span)
        return None

    # ------------------------------------------------------------------
    # New-item position resolution
    # ------------------------------------------------------------------
    def _resolve_position(
        self,
        grid: PaletteGrid,
        row: int | None,
        col: int | None,
        col_span: int = DEFAULT_COL_SPAN,
    ) -> tuple[int, int]:
        """Default an unspecified position to the row right below the last item.

        While a sequential placement session is open the default is the
        session cursor instead, so consecutive adds fill one row left-to-right
        and wrap to the next row once the item no longer fits.
        """
        if row is None and col is None:
            cursor = self._active_cursor(grid)
            if cursor is not None:
                if cursor["col"] + max(1, int(col_span)) > grid.columns:
                    cursor["row"], cursor["col"] = cursor["row"] + 1, 0
                return cursor["row"], cursor["col"]
        if row is None:
            row = max((item.bottom for item in grid.items), default=0)
        if col is None:
            col = 0
        return row, col
