from krita import DockWidgetFactory, DockWidgetFactoryBase
from PyQt5.QtWidgets import QDockWidget
from .brush_adjustment import BrushAdjustmentWidget

class BrushSettingDockerFactory(DockWidgetFactoryBase):
    """Factory for creating the Brush Settings Docker"""
    
    def __init__(self):
        super().__init__("brush_setting_docker", DockWidgetFactory.DockRight)
    
    def createDockWidget(self):
        """Create and return the brush settings dock widget"""
        return BrushSettingDockerWidget()

class BrushSettingDockerWidget(QDockWidget):
    """Docker widget for brush settings adjustments"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Brush Settings")
        self.setObjectName("QuickBrushSettingDocker")
        
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
