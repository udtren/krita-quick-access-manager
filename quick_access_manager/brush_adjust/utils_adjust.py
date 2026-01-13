"""
Utility functions for brush size conversions and other helpers.
"""


def brush_size_to_slider(size):
    """
    Convert brush size (1-1000) to slider value (0-100) with non-linear scaling.

    Args:
        size: Brush size (1-1000)

    Returns:
        int: Slider value (0-100)
    """
    if size <= 100:
        # Linear mapping for 1-100: maps to slider 0-70 (70% of slider range)
        return int((size - 1) * 70 / 100)
    else:
        # Linear mapping for 101-1000: maps to slider 71-100 (30% of slider range)
        return int(70 + (size - 100) * 30 / 900)


def slider_to_brush_size(slider_value):
    """
    Convert slider value (0-100) to brush size (1-1000) with non-linear scaling.

    Args:
        slider_value: Slider value (0-100)

    Returns:
        int: Brush size (1-1000)
    """
    if slider_value <= 70:
        # Map slider 0-70 to brush size 1-100
        return int(1 + slider_value * 100 / 70)
    else:
        # Map slider 71-100 to brush size 100-1000
        return int(100 + (slider_value - 70) * 900 / 30)
