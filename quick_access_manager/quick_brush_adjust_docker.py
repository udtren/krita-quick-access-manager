from krita import DockWidgetFactory, DockWidgetFactoryBase
from PyQt5.QtWidgets import QDockWidget
from .quick_brush_adjust import BrushAdjustmentWidget

class BrushAdjustDockerFactory(DockWidgetFactoryBase):
    """Factory for creating the Brush Adjustments Docker"""

    def __init__(self):
        super().__init__("brush_adjust_docker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        """Create and return the brush adjustments dock widget"""
        return BrushAdjustDockerWidget()

class BrushAdjustDockerWidget(QDockWidget):
    """Docker widget for brush adjustments"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Brush Adjustments")
        self.setObjectName("QuickBrushAdjustmentsDocker")
        
        # Create the brush adjustment widget
        self.brush_adjustment_section = BrushAdjustmentWidget(self)
        self.setWidget(self.brush_adjustment_section)
        
        # Set minimum size to ensure usability
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
    
    def refresh_styles(self):
        """Refresh styles when settings change"""
        if hasattr(self, 'brush_adjustment_section'):
            self.brush_adjustment_section.refresh_styles()
    
    def force_update_brush(self):
        """Force update brush settings - can be called externally"""
        if hasattr(self, 'brush_adjustment_section'):
            self.brush_adjustment_section.force_update()
