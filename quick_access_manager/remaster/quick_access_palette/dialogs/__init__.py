"""Quick Access Palette dialogs, split by responsibility:

- item_config_dialogs: the seven per-item-type config dialogs
  (Action/Label/BrushSize/BrushBlendMode/DockerToggle/Color/Script).
- palette_settings_dialog: the Settings dialog (PaletteConfigDialog).
- grid_edit: the Grid Edit feature (canvas, item button, dialog).

Everything is re-exported here so callers keep importing from
`quick_access_palette.dialogs` unchanged.
"""

from .item_config_dialogs import (
    ActionItemConfigDialog,
    BrushBlendModeItemConfigDialog,
    BrushSizeItemConfigDialog,
    ColorItemConfigDialog,
    DockerToggleItemConfigDialog,
    LabelItemConfigDialog,
    ScriptItemConfigDialog,
    SeparatorItemConfigDialog,
)
from .palette_settings_dialog import PaletteConfigDialog
from .grid_edit import (
    GridEditCanvas,
    GridEditItemButton,
    GridEditDialog,
    RESIZE_HANDLE_WIDTH,
)

__all__ = [
    "ActionItemConfigDialog",
    "BrushBlendModeItemConfigDialog",
    "BrushSizeItemConfigDialog",
    "ColorItemConfigDialog",
    "DockerToggleItemConfigDialog",
    "LabelItemConfigDialog",
    "ScriptItemConfigDialog",
    "SeparatorItemConfigDialog",
    "PaletteConfigDialog",
    "GridEditCanvas",
    "GridEditItemButton",
    "GridEditDialog",
    "RESIZE_HANDLE_WIDTH",
]
