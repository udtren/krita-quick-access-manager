from PyQt6.QtWidgets import QMdiArea, QDockWidget, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from .base_tools.adjust_to_subwindow_filter import ntAdjustToSubwindowFilter
from .base_tools.widget_pad import ntWidgetPad, WidgetPadPosition
from ..widgets import CircularRotationWidget


class FloatRotation:
    """Floating rotation widget positioned at the top-right of the brush_adjust_docker"""

    def __init__(self, window, rotation_widget, rotation_label):
        """
        Initialize floating rotation widget.

        Args:
            window: The Krita window instance
            rotation_widget: The CircularRotationWidget instance to display in the pad
            rotation_label: The rotation value label to display alongside the widget
        """
        qWin = window.qwindow()
        mdiArea = qWin.findChild(QMdiArea)

        # Create position configuration: Position at the TOP of the brush_adjust_docker,
        # aligned to the RIGHT
        position_config = WidgetPadPosition(
            reference_docker_name="brush_adjust_docker",
            side=WidgetPadPosition.TOP,
            alignment=WidgetPadPosition.ALIGN_RIGHT,
            gap=5,
            fallback_to_canvas_edge=True,
        )

        # Create "pad" with the position configuration
        self.pad = ntWidgetPad(mdiArea, position_config)
        self.pad.setObjectName("rotationPad")

        # Create a container widget to hold the rotation widget and label
        self.container = QWidget()
        self.container.setStyleSheet(
            """
            background-color: #323232;
            font-weight: bold;
            """
        )
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(6)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add rotation widget and label to container
        container_layout.addWidget(rotation_widget)
        container_layout.addWidget(rotation_label)
        self.container.setLayout(container_layout)

        # Manually add the container to the pad and set up sizing
        self.pad.widget = self.container
        self.pad.layout().addWidget(self.container)

        # Force the container to show and adjust size
        self.container.show()
        self.container.adjustSize()

        # Store references
        self.rotation_widget = rotation_widget
        self.rotation_label = rotation_label

        # Create and install event filter
        self.adjustFilter = ntAdjustToSubwindowFilter(mdiArea)
        self.adjustFilter.setTargetWidget(self.pad)
        mdiArea.subWindowActivated.connect(self.ensureFilterIsInstalled)
        qWin.installEventFilter(self.adjustFilter)

    def ensureFilterIsInstalled(self, subWin):
        """Ensure that the current SubWindow has the filter installed,
        and immediately move the widget pad to current View."""
        if subWin:
            subWin.installEventFilter(self.adjustFilter)
            self.pad.adjustToView()

    def close(self):
        """Close the floating widget and return widgets to original parent"""
        return self.pad.close()
