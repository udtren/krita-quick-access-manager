"""Controller for Quick Access Palette document mutations, split by
responsibility:

- settings_mixin: DEFAULT_SETTINGS + docker/popup/HueSVC/Quick Adjust
  settings storage.
- tab_mixin: tab lookup/selection/add/rename/remove.
- placement_mixin: sequential placement cursor (Resources dialog) and
  Action item col_span normalization.
- item_crud_mixin: item add/update/remove/move/resize and grid-level
  layout operations.
- base: PaletteController itself, composing the four mixins above plus
  construction/persistence.

Everything is re-exported here so callers keep importing
`from .controller import PaletteController` (or DEFAULT_SETTINGS) unchanged.
"""

from .base import PaletteController
from .settings_mixin import DEFAULT_SETTINGS

__all__ = ["PaletteController", "DEFAULT_SETTINGS"]
