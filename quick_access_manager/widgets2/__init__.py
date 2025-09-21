from .color_history_widget import ColorHistoryWidget
from .circular_rotation_widget import CircularRotationWidget
from .brush_history_widget import BrushHistoryWidget

BRUSH_ADJUSTMENT_FONT_SIZE = "12px"
BRUSH_ADJUSTMENT_NUMBER_SIZE = "16px"
COLOR_HISTORY_NUMBER = 20
BRUSH_HISTORY_NUMBER = 20
COLOR_HISTORY_ICON_SIZE = 34
BRUSH_HISTORY_ICON_SIZE = 40
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
    'COLOR_HISTORY_ICON_SIZE',
    'BRUSH_HISTORY_ICON_SIZE',
    'BLENDE_MODES'
]
