"""
Docker factory and wrapper classes for the Brush Adjust Docker.
"""

from ..compat import QDockWidget
from krita import DockWidgetFactory, DockWidgetFactoryBase  # type: ignore

from .adjustment_widget import BrushAdjustmentWidget


class BrushAdjustDockerFactory(DockWidgetFactoryBase):
    """Factory for creating the Brush Adjustments Docker"""

    def __init__(self):
        try:
            dock_pos = DockWidgetFactory.DockRight
        except AttributeError:
            dock_pos = DockWidgetFactory.DockPosition.DockRight  # Krita 6
        super().__init__("brush_adjust_docker", dock_pos)

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
        self.setMinimumWidth(100)
        self.setMinimumHeight(100)

    def reload_ui(self):
        """Recreate BrushAdjustmentWidget from config, preserving history data."""
        old_section = self.brush_adjustment_section

        # Snapshot history from the current widget before destroying it
        saved_colors = []
        saved_brushes = []
        if old_section is not None:
            if (
                hasattr(old_section, "color_history_widget")
                and old_section.color_history_widget is not None
            ):
                saved_colors = list(old_section.color_history_widget.color_history)
            if (
                hasattr(old_section, "brush_history_widget")
                and old_section.brush_history_widget is not None
            ):
                saved_brushes = list(old_section.brush_history_widget.brush_history)

        # Create the new widget (reads fresh config in __init__)
        new_section = BrushAdjustmentWidget(self)
        self.brush_adjustment_section = new_section
        self.setWidget(new_section)

        # Restore color history if the widget is still enabled
        if saved_colors and new_section.color_history_widget is not None:
            new_section.color_history_widget.color_history = saved_colors
            new_section.color_history_widget.update_color_buttons()

        # Restore brush history if the widget is still enabled
        if saved_brushes and new_section.brush_history_widget is not None:
            new_section.brush_history_widget.brush_history = saved_brushes
            new_section.brush_history_widget.update_brush_buttons()

        # Schedule old widget deletion
        if old_section is not None:
            old_section.deleteLater()

    def refresh_styles(self):
        """Refresh styles when settings change"""
        if hasattr(self, "brush_adjustment_section"):
            self.brush_adjustment_section.refresh_styles()

    def force_update_brush(self):
        """Force update brush settings - can be called externally"""
        if hasattr(self, "brush_adjustment_section"):
            self.brush_adjustment_section.force_update()
