"""
Docker factory and wrapper classes for the remastered Quick Adjust Docker.
"""

from krita import DockWidgetFactory, DockWidgetFactoryBase  # type: ignore

from ..compat import QDockWidget
from .adjustment_widget import BrushAdjustmentWidget

DOCKER_ID = "brush_adjust_docker"


class QuickAdjustDockerFactory(DockWidgetFactoryBase):
    """Factory for creating the Quick Adjust Docker"""

    def __init__(self):
        try:
            dock_pos = DockWidgetFactory.DockRight
        except AttributeError:
            dock_pos = DockWidgetFactory.DockPosition.DockRight
        super().__init__(DOCKER_ID, dock_pos)

    def createDockWidget(self):
        return QuickAdjustDockerWidget()


class QuickAdjustDockerWidget(QDockWidget):
    """Docker widget for brush/layer adjustments"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Brush Adjustments")
        self.setObjectName(DOCKER_ID)

        self.brush_adjustment_section = BrushAdjustmentWidget(self)
        self.setWidget(self.brush_adjustment_section)

        self.setMinimumWidth(100)
        self.setMinimumHeight(100)
