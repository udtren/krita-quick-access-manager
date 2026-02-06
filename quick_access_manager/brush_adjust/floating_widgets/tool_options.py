from PyQt6.QtWidgets import QMdiArea, QDockWidget
from .base_tools.adjust_to_subwindow_filter import ntAdjustToSubwindowFilter
from .base_tools.widget_pad import ntWidgetPad, WidgetPadPosition
from ...config.quick_adjust_docker_loader import get_tool_options_position


class FloatToolOptions:

    def __init__(self, window):
        qWin = window.qwindow()
        mdiArea = qWin.findChild(QMdiArea)
        self.toolOptions = qWin.findChild(QDockWidget, "sharedtooldocker")

        # Get position from config
        position_setting = get_tool_options_position()
        if position_setting == "right_align_top":
            side = WidgetPadPosition.RIGHT
        else:
            side = WidgetPadPosition.LEFT

        # Create position configuration
        position_config = WidgetPadPosition(
            reference_docker_name="brush_adjust_docker",
            side=side,
            alignment=WidgetPadPosition.ALIGN_TOP,
            gap=5,
            fallback_to_canvas_edge=True,
        )

        # Create "pad" with the position configuration
        self.pad = ntWidgetPad(mdiArea, position_config)
        self.pad.setObjectName("toolOptionsPad")
        self.pad.borrowDocker(self.toolOptions)

        # Create and install event filter
        self.adjustFilter = ntAdjustToSubwindowFilter(mdiArea)
        self.adjustFilter.setTargetWidget(self.pad)
        mdiArea.subWindowActivated.connect(self.ensureFilterIsInstalled)
        qWin.installEventFilter(self.adjustFilter)

        # Disable the related QDockWidget
        self.dockerAction = (
            window.qwindow()
            .findChild(QDockWidget, "sharedtooldocker")
            .toggleViewAction()
        )
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
        if self.pad.borrowDocker(self.toolOptions):
            self.pad.show()
            self.pad.adjustToView()

    def close(self):
        self.dockerAction.setEnabled(True)
        return self.pad.close()
