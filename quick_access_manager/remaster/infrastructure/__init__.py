"""Infrastructure helpers for the remastered palette."""

try:
    from .krita_actions import ActionManager
except ModuleNotFoundError as exc:
    if exc.name != "krita":
        raise
    ActionManager = None

from .palette_repository import DEFAULT_COLUMNS, PaletteRepository
from .paths import (
    get_default_icons_dir,
    get_palette_config_path,
    get_remaster_config_dir,
    get_system_icons_dir,
)

__all__ = [
    "ActionManager",
    "DEFAULT_COLUMNS",
    "PaletteRepository",
    "get_default_icons_dir",
    "get_palette_config_path",
    "get_remaster_config_dir",
    "get_system_icons_dir",
]