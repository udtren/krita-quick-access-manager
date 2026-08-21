# WidgetPad Position Configuration Examples

The `ntWidgetPad` class now supports flexible positioning relative to any Krita docker or canvas edge using the `WidgetPadPosition` configuration class.

## Basic Usage

```python
from .base_tools.widget_pad import ntWidgetPad, WidgetPadPosition

# Create a position configuration
position_config = WidgetPadPosition(
    reference_docker_name="brush_adjust_docker",
    side=WidgetPadPosition.LEFT,
    alignment=WidgetPadPosition.ALIGN_TOP,
    gap=5,
    fallback_to_canvas_edge=True
)

# Create the widget pad with the configuration
pad = ntWidgetPad(parent_widget, position_config)
```

## Configuration Parameters

### `reference_docker_name` (str or None)
- The `objectName()` of the docker to position relative to
- Examples: `"brush_adjust_docker"`, `"sharedtooldocker"`, `"KisLayerBox"`
- Set to `None` to position relative to canvas edges only

### `side` (str)
Which side of the reference docker to position on:
- `WidgetPadPosition.LEFT` - Position to the left of the docker
- `WidgetPadPosition.RIGHT` - Position to the right of the docker
- `WidgetPadPosition.TOP` - Position above the docker
- `WidgetPadPosition.BOTTOM` - Position below the docker

### `alignment` (str)
Alignment along the perpendicular axis:

**For LEFT/RIGHT sides (vertical alignment):**
- `WidgetPadPosition.ALIGN_TOP` - Align top edges
- `WidgetPadPosition.ALIGN_BOTTOM` - Align bottom edges

**For TOP/BOTTOM sides (horizontal alignment):**
- `WidgetPadPosition.ALIGN_LEFT` - Align left edges
- `WidgetPadPosition.ALIGN_RIGHT` - Align right edges

### `gap` (int)
- Gap in pixels between the widget pad and reference docker
- Default: `5`

### `fallback_to_canvas_edge` (bool)
- If `True` and docker not found/visible, fall back to canvas edge positioning
- If `False` and docker not found/visible, widget stays at current position
- Default: `True`

## Example Configurations

### 1. Tool Options to the Left of Brush Adjust Docker

```python
position_config = WidgetPadPosition(
    reference_docker_name="brush_adjust_docker",
    side=WidgetPadPosition.LEFT,
    alignment=WidgetPadPosition.ALIGN_TOP,
    gap=5,
    fallback_to_canvas_edge=True
)
```

**Result:** Tool Options appears to the left of the Brush Adjust docker, with top edges aligned and a 5px gap.

### 2. Widget Below Layers Docker (Left Aligned)

```python
position_config = WidgetPadPosition(
    reference_docker_name="KisLayerBox",
    side=WidgetPadPosition.BOTTOM,
    alignment=WidgetPadPosition.ALIGN_LEFT,
    gap=10,
    fallback_to_canvas_edge=True
)
```

**Result:** Widget appears below the Layers docker, with left edges aligned and a 10px gap.

### 3. Widget Above Brush Presets (Right Aligned)

```python
position_config = WidgetPadPosition(
    reference_docker_name="KisPresetChooser",
    side=WidgetPadPosition.TOP,
    alignment=WidgetPadPosition.ALIGN_RIGHT,
    gap=8,
    fallback_to_canvas_edge=False
)
```

**Result:** Widget appears above the Brush Presets docker, with right edges aligned and an 8px gap. If docker not found, widget stays at current position.

### 4. Widget to the Right of Color Selector (Bottom Aligned)

```python
position_config = WidgetPadPosition(
    reference_docker_name="KisColorSelector",
    side=WidgetPadPosition.RIGHT,
    alignment=WidgetPadPosition.ALIGN_BOTTOM,
    gap=5,
    fallback_to_canvas_edge=True
)
```

**Result:** Widget appears to the right of the Color Selector docker, with bottom edges aligned and a 5px gap.

### 5. Canvas Edge Positioning (No Docker Reference)

```python
# Left edge of canvas
position_config = WidgetPadPosition(
    reference_docker_name=None,
    side=WidgetPadPosition.LEFT,
    alignment=WidgetPadPosition.ALIGN_TOP,  # Ignored for canvas edge
    gap=0
)

# Right edge of canvas
position_config = WidgetPadPosition(
    reference_docker_name=None,
    side=WidgetPadPosition.RIGHT,
    alignment=WidgetPadPosition.ALIGN_TOP,  # Ignored for canvas edge
    gap=0
)

# Top-right corner of canvas
position_config = WidgetPadPosition(
    reference_docker_name=None,
    side=WidgetPadPosition.TOP,
    alignment=WidgetPadPosition.ALIGN_RIGHT,
    gap=0
)

# Bottom-left corner of canvas
position_config = WidgetPadPosition(
    reference_docker_name=None,
    side=WidgetPadPosition.BOTTOM,
    alignment=WidgetPadPosition.ALIGN_LEFT,
    gap=0
)
```

## Complete Example: Creating a Floating Palette

```python
from PyQt5.QtWidgets import QMdiArea, QDockWidget
from .base_tools.widget_pad import ntWidgetPad, WidgetPadPosition
from .base_tools.adjust_to_subwindow_filter import ntAdjustToSubwindowFilter

class FloatingPalette:
    def __init__(self, window, docker_name):
        qWin = window.qwindow()
        mdiArea = qWin.findChild(QMdiArea)
        target_docker = qWin.findChild(QDockWidget, docker_name)

        # Position to the right of the Brush Adjust docker, aligned to top
        position_config = WidgetPadPosition(
            reference_docker_name="brush_adjust_docker",
            side=WidgetPadPosition.RIGHT,
            alignment=WidgetPadPosition.ALIGN_TOP,
            gap=5,
            fallback_to_canvas_edge=True
        )

        # Create floating widget
        self.pad = ntWidgetPad(mdiArea, position_config)
        self.pad.setObjectName("myFloatingPalette")
        self.pad.borrowDocker(target_docker)

        # Install event filter for responsive positioning
        self.adjustFilter = ntAdjustToSubwindowFilter(mdiArea)
        self.adjustFilter.setTargetWidget(self.pad)
        mdiArea.subWindowActivated.connect(self.ensureFilterIsInstalled)
        qWin.installEventFilter(self.adjustFilter)

    def ensureFilterIsInstalled(self, subWin):
        if subWin:
            subWin.installEventFilter(self.adjustFilter)
            self.pad.adjustToView()
```

## Common Docker Object Names in Krita

Here are some common docker object names you can use:

- `"brush_adjust_docker"` - Quick Brush Adjustments (custom)
- `"sharedtooldocker"` - Tool Options
- `"KisLayerBox"` - Layers
- `"KisPresetChooser"` - Brush Presets
- `"KisColorSelector"` - Advanced Color Selector
- `"KisPaletteDocker"` - Palette
- `"KritaShape/KisToolDynamicsOptionWidget"` - Brush Editor
- `"HistoryDocker"` - Undo History

To find the object name of any docker:
```python
from krita import Krita

app = Krita.instance()
if app.activeWindow():
    for docker in app.activeWindow().dockers():
        print(f"{docker.windowTitle()}: {docker.objectName()}")
```

## Debugging

Enable debug logging to see positioning calculations:
```python
# In widget_pad.py
DEBUG_POSITIONING = True
```

This will print detailed information about docker detection, positioning calculations, and event handling.
