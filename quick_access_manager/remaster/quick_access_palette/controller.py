"""Controller for Quick Access Palette document mutations."""

from uuid import uuid4

from ..infrastructure import AliasRepository, PaletteRepository
from ..shared import (
    ACTION_ITEM,
    COLOR_ITEM,
    DEFAULT_ACTION_COL_SPAN,
    DOCKER_TOGGLE_ITEM,
    LABEL_ITEM,
    SCRIPT_ITEM,
    FreeGridLayoutEngine,
    LayoutResult,
    PaletteGrid,
    PaletteItem,
)

DEFAULT_SETTINGS = {
    "default": {
        "docker_icon_size": 42,
        "config_dialog_width": 340,
        "config_dialog_height": 480,
        "huesvc_enabled": True,
        "quick_adjust_enabled": True,
    },
    "popup": {"popup_icon_size": 42},
    "huesvc": {
        "value_font_size": 10,
        "poll_interval": 250,
        "rgb_display_mode": "percentage",
        "popup_width": 350,
        "popup_height": 550,
    },
    "quick_adjust": {
        "font_size": "12px",
        "size_slider_enabled": True,
        "opacity_slider_enabled": True,
        "flow_slider_enabled": True,
        "layer_opacity_slider_enabled": True,
        "color_history_enabled": True,
        "color_history_total": 14,
        "color_history_icon_size": 30,
        "brush_history_enabled": True,
        "brush_history_total": 14,
        "brush_history_icon_size": 34,
        "alt_erase_key": "",
        "preserve_alpha_key": "",
        "select_outline_key": "",
        "tool_options_enabled": False,
        "tool_options_start_visible": True,
        "tool_options_position": "left_align_top",
        "temp_brush_sets": [],
    },
}


class PaletteController:
    """Owns palette document state and applies layout mutations."""

    def __init__(self, repository: PaletteRepository | None = None):
        self.repository = repository or PaletteRepository()
        self.document = self.repository.load()
        self.normalize_action_spans()

    def normalize_action_spans(self):
        changed = False
        # Load the alias config once instead of once per action item.
        aliases = AliasRepository().load().get("actions", {})
        for tab in self.document.tabs:
            for grid in tab.grids:
                for index, item in enumerate(grid.items):
                    if item.type != ACTION_ITEM:
                        continue
                    expected_col_span = self._action_col_span(
                        item.payload.get("action_id", ""),
                        min_col_span=item.col_span,
                        aliases=aliases,
                    )
                    if item.col_span != expected_col_span:
                        grid.items[index] = item.copy_with(col_span=expected_col_span)
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
            aliases = AliasRepository().load().get("actions", {})
        alias = aliases.get(action_id, {})
        if alias.get("icon_name"):
            return 1
        return max(DEFAULT_ACTION_COL_SPAN, min_col_span)

    @property
    def active_tab_id(self) -> str | None:
        return self.document.active_tab_id

    def save(self):
        self.repository.save(self.document)

    def settings(self):
        merged = {
            "default": dict(DEFAULT_SETTINGS["default"]),
            "popup": dict(DEFAULT_SETTINGS["popup"]),
            "huesvc": dict(DEFAULT_SETTINGS["huesvc"]),
            "quick_adjust": dict(DEFAULT_SETTINGS["quick_adjust"]),
        }
        for section, values in self.document.settings.items():
            if isinstance(values, dict):
                merged.setdefault(section, {}).update(values)
        return merged

    def docker_icon_size(self):
        return self._bounded_icon_size(
            self.settings()["default"].get("docker_icon_size", 42)
        )

    def popup_icon_size(self):
        return self._bounded_icon_size(
            self.settings()["popup"].get("popup_icon_size", 42)
        )

    def config_dialog_size(self):
        default = self.settings()["default"]
        return (
            int(default.get("config_dialog_width", 340)),
            int(default.get("config_dialog_height", 480)),
        )

    def is_huesvc_enabled(self):
        return bool(self.settings()["default"].get("huesvc_enabled", True))

    def is_quick_adjust_enabled(self):
        return bool(self.settings()["default"].get("quick_adjust_enabled", True))

    def update_settings(
        self,
        docker_icon_size=None,
        popup_icon_size=None,
        config_dialog_width=None,
        config_dialog_height=None,
        huesvc_enabled=None,
        quick_adjust_enabled=None,
    ):
        settings = self.settings()
        if docker_icon_size is not None:
            settings["default"]["docker_icon_size"] = self._bounded_icon_size(
                docker_icon_size
            )
        if popup_icon_size is not None:
            settings["popup"]["popup_icon_size"] = self._bounded_icon_size(
                popup_icon_size
            )
        if config_dialog_width is not None:
            settings["default"]["config_dialog_width"] = int(config_dialog_width)
        if config_dialog_height is not None:
            settings["default"]["config_dialog_height"] = int(config_dialog_height)
        if huesvc_enabled is not None:
            settings["default"]["huesvc_enabled"] = bool(huesvc_enabled)
        if quick_adjust_enabled is not None:
            settings["default"]["quick_adjust_enabled"] = bool(quick_adjust_enabled)
        self.document.settings = settings
        self.save()

    def huesvc_settings(self):
        return self.settings()["huesvc"]

    def update_huesvc_settings(
        self,
        value_font_size=None,
        poll_interval=None,
        rgb_display_mode=None,
        popup_width=None,
        popup_height=None,
    ):
        settings = self.settings()
        if value_font_size is not None:
            settings["huesvc"]["value_font_size"] = int(value_font_size)
        if poll_interval is not None:
            settings["huesvc"]["poll_interval"] = int(poll_interval)
        if rgb_display_mode is not None:
            settings["huesvc"]["rgb_display_mode"] = rgb_display_mode
        if popup_width is not None:
            settings["huesvc"]["popup_width"] = int(popup_width)
        if popup_height is not None:
            settings["huesvc"]["popup_height"] = int(popup_height)
        self.document.settings = settings
        self.save()

    def quick_adjust_settings(self):
        return self.settings()["quick_adjust"]

    def update_quick_adjust_settings(self, **kwargs):
        settings = self.settings()
        settings["quick_adjust"].update(kwargs)
        self.document.settings = settings
        self.save()

    def _bounded_icon_size(self, value):
        try:
            return max(24, min(96, int(value)))
        except Exception:
            return 42

    def active_tab(self):
        if self.document.active_tab_id:
            for tab in self.document.tabs:
                if tab.id == self.document.active_tab_id:
                    return tab
        if self.document.tabs:
            self.document.active_tab_id = self.document.tabs[0].id
            return self.document.tabs[0]
        return None

    def active_grid(self) -> PaletteGrid | None:
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
        from ..shared import PaletteTab

        tab = PaletteTab(id=tab_id, name=name, grids=[grid])
        self.document.tabs.append(tab)
        self.document.active_tab_id = tab_id
        self.save()
        return tab

    def rename_tab(self, tab_id: str, name: str):
        for tab in self.document.tabs:
            if tab.id == tab_id:
                tab.name = name
                self.save()
                return tab
        raise ValueError(f"Palette tab not found: {tab_id}")

    def remove_tab(self, tab_id: str):
        if len(self.document.tabs) <= 1:
            return False
        self.document.tabs = [tab for tab in self.document.tabs if tab.id != tab_id]
        if self.document.active_tab_id == tab_id:
            self.document.active_tab_id = (
                self.document.tabs[0].id if self.document.tabs else None
            )
        self.save()
        return True

    def add_brush(
        self, brush_name: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_brush(
            self._new_id("brush"), brush_name, row=row, col=col
        )
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

    def add_action(
        self, action_id: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_action(
            self._new_id("action"),
            action_id,
            row=row,
            col=col,
            col_span=self._action_col_span(action_id),
        )
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

    def add_label(
        self, text: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_label(self._new_id("label"), text, row=row, col=col)
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

    def add_separator(
        self, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_separator(self._new_id("separator"), row=row, col=col)
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

    def add_docker_toggle(
        self, docker_id: str, row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_docker_toggle(
            self._new_id("docker_toggle"), docker_id, row=row, col=col
        )
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

    def add_color(
        self, color: str = "#ffffff", row: int | None = None, col: int | None = None
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_color(self._new_id("color"), color, row=row, col=col)
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

    def add_script(
        self,
        script_path: str,
        config=None,
        row: int | None = None,
        col: int | None = None,
    ) -> LayoutResult:
        grid = self._require_active_grid()
        row, col = self._resolve_position(grid, row, col)
        item = PaletteItem.create_script(
            self._new_id("script"), script_path, row=row, col=col, config=config
        )
        return self._apply_result(
            grid,
            FreeGridLayoutEngine(grid.columns).add_item(grid.items, item),
            compact=False,
        )

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
                col_span = self._action_col_span(
                    item.payload.get("action_id", ""), min_col_span=item.col_span
                )
                if col_span != item.col_span:
                    grid.items[index] = item.copy_with(col_span=col_span)
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
                grid.items[index] = item.copy_with(payload={"docker_id": docker_id})
                result = FreeGridLayoutEngine(grid.columns).validate(grid.items)
                return self._apply_result(grid, result, compact=False)
        raise ValueError(f"Palette item not found: {item_id}")

    def update_color_item(self, item_id: str, config) -> LayoutResult:
        return self._update_payload(item_id, COLOR_ITEM, config)

    def update_script_item(self, item_id: str, config) -> LayoutResult:
        return self._update_payload(item_id, SCRIPT_ITEM, config)

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

    def _resolve_position(
        self, grid: PaletteGrid, row: int | None, col: int | None
    ) -> tuple[int, int]:
        """Default an unspecified position to the row right below the last item."""
        if row is None:
            row = max((item.bottom for item in grid.items), default=0)
        if col is None:
            col = 0
        return row, col

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"
