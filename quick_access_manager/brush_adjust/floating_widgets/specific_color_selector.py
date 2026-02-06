from PyQt6.QtWidgets import QMdiArea, QDockWidget
from PyQt6.QtGui import QPalette, QColor
from .base_tools.adjust_to_subwindow_filter import ntAdjustToSubwindowFilter
from .base_tools.widget_pad import ntWidgetPad, WidgetPadPosition


class FloatSpecificColorSelector:

    def __init__(self, window):
        qWin = window.qwindow()
        mdiArea = qWin.findChild(QMdiArea)
        self.colorSelector = qWin.findChild(QDockWidget, "SpecificColorSelector")

        # Create position configuration - bottom align left
        position_config = WidgetPadPosition(
            reference_docker_name="brush_adjust_docker",
            side=WidgetPadPosition.BOTTOM,
            alignment=WidgetPadPosition.ALIGN_LEFT,
            gap=5,
            fallback_to_canvas_edge=True,
        )

        # Create "pad" with the position configuration
        self.pad = ntWidgetPad(mdiArea, position_config)
        self.pad.setObjectName("SpecificColorSelectorPad")

        # Set background color using palette
        self.pad.setAutoFillBackground(True)
        palette = self.pad.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#323232"))
        self.pad.setPalette(palette)

        self.pad.borrowDocker(self.colorSelector)

        # Create and install event filter
        self.adjustFilter = ntAdjustToSubwindowFilter(mdiArea)
        self.adjustFilter.setTargetWidget(self.pad)
        mdiArea.subWindowActivated.connect(self.ensureFilterIsInstalled)
        qWin.installEventFilter(self.adjustFilter)

        # Disable the related QDockWidget
        self.dockerAction = self.colorSelector.toggleViewAction()
        self.dockerAction.setEnabled(False)

    def ensureFilterIsInstalled(self, subWin):
        """Ensure that the current SubWindow has the filter installed,
        and immediately move the Toolbox to current View."""
        if subWin:
            subWin.installEventFilter(self.adjustFilter)
            self.pad.adjustToView()

    def returnDocker(self):
        """Return the borrowed docker to its original location"""
        self.pad.returnDocker()
        self.pad.hide()

    def reborrowDocker(self):
        """Reborrow the docker and show the pad"""
        if self.pad.borrowDocker(self.colorSelector):
            self.pad.show()
            self.pad.adjustToView()

    def close(self):
        self.dockerAction.setEnabled(True)
        return self.pad.close()
