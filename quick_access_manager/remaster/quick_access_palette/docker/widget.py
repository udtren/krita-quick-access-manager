"""QuickAccessPaletteDockerWidget: composes the docker's mixins.

Behavior lives in the mixins (see each file's docstring for what it owns);
this module is only construction, teardown, and the mixin resolution order.
"""

from ...compat import QDockWidget, QWidget
from ...infrastructure import AliasRepository
from ..controller import PaletteController
from ..item_style_mixin import ItemStyleMixin
from .activation_mixin import ActivationMixin
from .alias_bridge_mixin import AliasBridgeMixin
from .drag_filter import GridItemDragFilter
from .item_actions_mixin import ItemActionsMixin
from .item_rendering_mixin import ItemRenderingMixin
from .ui_builder_mixin import UIBuilderMixin


class QuickAccessPaletteDockerWidget(
    QDockWidget,
    ItemStyleMixin,
    UIBuilderMixin,
    ItemRenderingMixin,
    ItemActionsMixin,
    ActivationMixin,
    AliasBridgeMixin,
):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Access Palette")
        self.setObjectName("quick_access_palette_docker")
        self.controller = PaletteController()
        # Krita's action table is only needed when a button is actually pressed,
        # so it is discovered lazily instead of walking the widget tree at startup.
        self._action_map = None
        self._alias_data = AliasRepository().load()
        self.issue_map = {}
        # One filter shared by every item widget; item widgets are rebuilt on
        # each reload, so per-widget filter objects would just churn.
        self.drag_filter = GridItemDragFilter(self)
        self.root_widget = QWidget()
        self.setWidget(self.root_widget)
        self.setMinimumWidth(160)
        self.setMinimumHeight(120)
        self.build_ui()

    def reload_ui(self):
        self.controller = PaletteController()
        old_widget = self.widget()
        self.root_widget = QWidget()
        self.setWidget(self.root_widget)
        self.build_ui()
        if old_widget:
            old_widget.deleteLater()
