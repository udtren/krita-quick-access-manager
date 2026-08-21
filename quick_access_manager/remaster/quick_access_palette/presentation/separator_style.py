"""Shared rendering constants/helpers for palette separator items."""

SEPARATOR_EDGE_MARGIN = 5


def separator_stylesheet(color, thickness):
    radius = max(1, int(thickness) // 2)
    return f"background-color: {color}; border-radius: {radius}px;"
