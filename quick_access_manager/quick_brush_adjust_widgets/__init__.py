# Quick Brush Setting Widgets Package
# This package contains the individual widget components for the brush settings docker

from .color_history_widget import ColorHistoryWidget
from .circular_rotation_widget import CircularRotationWidget
from .brush_history_widget import BrushHistoryWidget

# Font size for brush adjustment labels (easily adjustable)
BRUSH_ADJUSTMENT_FONT_SIZE = "12px"
BRUSH_ADJUSTMENT_NUMBER_SIZE = "16px"
COLOR_HISTORY_NUMBER = 20
BRUSH_HISTORY_NUMBER = 20
BRUSH_HISTORY_ICON_SIZE = 30  # Size of brush history buttons and icons
BLENDE_MODES = [
    "normal", "multiply", "screen", "overlay", "soft_light_svg", 
    "hard_light", "dodge", "burn", "darken", "lighten",
    "hue", "saturation", "color"
]

__all__ = [
    'ColorHistoryWidget',
    'CircularRotationWidget', 
    'BrushHistoryWidget',
    'BRUSH_ADJUSTMENT_FONT_SIZE',
    'BRUSH_ADJUSTMENT_NUMBER_SIZE',
    'COLOR_HISTORY_NUMBER',
    'BRUSH_HISTORY_NUMBER',
    'BRUSH_HISTORY_ICON_SIZE',
    'BLENDE_MODES'
]
