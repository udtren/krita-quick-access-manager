from .color_history_widget import ColorHistoryWidget
from .circular_rotation_widget import CircularRotationWidget
from .brush_history_widget import BrushHistoryWidget

BRUSH_ADJUSTMENT_FONT_SIZE = "12px"
BRUSH_ADJUSTMENT_NUMBER_SIZE = "12px"
COLOR_HISTORY_NUMBER = 20
BRUSH_HISTORY_NUMBER = 20
COLOR_HISTORY_ICON_SIZE = 30
BRUSH_HISTORY_ICON_SIZE = 34
BLENDE_MODES = [
    "normal",
    "multiply",
    "screen",
    "dodge",
    "overlay",
    "soft_light_svg",
    "hard_light",
    "darken",
    "lighten",
    "greater",
]

__all__ = [
    "ColorHistoryWidget",
    "CircularRotationWidget",
    "BrushHistoryWidget",
    "BRUSH_ADJUSTMENT_FONT_SIZE",
    "BRUSH_ADJUSTMENT_NUMBER_SIZE",
    "COLOR_HISTORY_NUMBER",
    "BRUSH_HISTORY_NUMBER",
    "COLOR_HISTORY_ICON_SIZE",
    "BRUSH_HISTORY_ICON_SIZE",
    "BLENDE_MODES",
]
