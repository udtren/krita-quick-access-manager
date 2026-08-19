"""Infrastructure helpers for the remastered palette."""

try:
    from .krita_actions import ActionManager
except ModuleNotFoundError as exc:
    if exc.name != "krita":
        raise
    ActionManager = None

try:
    from .docker_manager import DockerManager
except ModuleNotFoundError as exc:
    if exc.name != "krita":
        raise
    DockerManager = None

from .alias_repository import AliasRepository
from .palette_repository import DEFAULT_COLUMNS, PaletteRepository
from .paths import (
    get_default_icons_dir,
    get_gesture_data_dir,
    get_gesture_images_dir,
    get_palette_config_path,
    get_remaster_config_dir,
    get_system_icons_dir,
)

__all__ = [
    "DEFAULT_COLUMNS",
    "ActionManager",
    "AliasRepository",
    "DockerManager",
    "PaletteRepository",
    "get_default_icons_dir",
    "get_gesture_data_dir",
    "get_gesture_images_dir",
    "get_palette_config_path",
    "get_remaster_config_dir",
    "get_system_icons_dir",
]
