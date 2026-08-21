"""
Utility functions for brush size conversions and other helpers.
"""


def brush_size_to_slider(size):
    """Convert brush size (1-1000) to slider value (0-100) with non-linear scaling."""
    if size <= 100:
        return int((size - 1) * 70 / 100)
    return int(70 + (size - 100) * 30 / 900)


def slider_to_brush_size(slider_value):
    """Convert slider value (0-100) to brush size (1-1000) with non-linear scaling."""
    if slider_value <= 70:
        return int(1 + slider_value * 100 / 70)
    return int(100 + (slider_value - 70) * 900 / 30)
