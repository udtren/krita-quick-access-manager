"""PaletteController: owns palette document state and applies layout
mutations. The actual behavior is split across four mixins by
responsibility - this module only wires them together and owns
construction/persistence."""

from uuid import uuid4

from ...infrastructure import AliasRepository, PaletteRepository
from .item_crud_mixin import ItemCrudMixin
from .placement_mixin import PlacementMixin
from .settings_mixin import SettingsMixin
from .tab_mixin import TabMixin


class PaletteController(SettingsMixin, TabMixin, PlacementMixin, ItemCrudMixin):
    """Owns palette document state and applies layout mutations."""

    def __init__(
        self,
        repository: PaletteRepository | None = None,
        alias_repository: AliasRepository | None = None,
    ):
        self.repository = repository or PaletteRepository()
        self.alias_repository = alias_repository or AliasRepository()
        self.document = self.repository.load()
        # Set while a Resources-style "add many items in a row" session is
        # open; see begin_sequential_placement().
        self._sequential_cursor = None
        self.normalize_action_spans()

    def save(self):
        self.repository.save(self.document)

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"
