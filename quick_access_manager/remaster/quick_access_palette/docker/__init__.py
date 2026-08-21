"""Quick Access Palette docker, split by responsibility:

- drag_filter: GridItemDragFilter (Ctrl + left-drag move) and the
  GRID_CELL_SPACING both it and the UI builder lay geometry out with.
- ui_builder_mixin: header/menu/tab-widget scaffolding.
- item_rendering_mixin: per-item-type widget construction and the
  right-click Property dialogs.
- item_actions_mixin: header-menu "Add" handlers and the Grid
  Edit/Gesture/Resources/Settings dialogs.
- activation_mixin: click-time execution (run action, set brush/color/
  blend mode, run script).
- alias_bridge_mixin: shared Alias Config read/write bridge.
- widget: QuickAccessPaletteDockerWidget, composing the mixins above.
- factory: QuickAccessPaletteDockerFactory.

Everything is re-exported here so callers keep importing from
`quick_access_palette.docker` unchanged.
"""

from .drag_filter import GRID_CELL_SPACING, GridItemDragFilter
from .factory import QuickAccessPaletteDockerFactory
from .widget import QuickAccessPaletteDockerWidget

__all__ = [
    "GridItemDragFilter",
    "GRID_CELL_SPACING",
    "QuickAccessPaletteDockerFactory",
    "QuickAccessPaletteDockerWidget",
]
