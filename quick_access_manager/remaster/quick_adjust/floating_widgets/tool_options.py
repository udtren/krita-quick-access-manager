from ...compat import QDockWidget, QMdiArea
from ..settings import get_tool_options_position
from .base_tools.adjust_to_subwindow_filter import ntAdjustToSubwindowFilter
from .base_tools.widget_pad import WidgetPadPosition, ntWidgetPad


class FloatToolOptions:

    def __init__(self, window):
        qWin = window.qwindow()
        mdiArea = qWin.findChild(QMdiArea)
        self.toolOptions = qWin.findChild(QDockWidget, "sharedtooldocker")

        position_setting = get_tool_options_position()
        if position_setting == "right_align_top":
            side = WidgetPadPosition.RIGHT
            alignment = WidgetPadPosition.ALIGN_TOP
        elif position_setting == "bottom_left":
            side = WidgetPadPosition.BOTTOM
            alignment = WidgetPadPosition.ALIGN_LEFT
        else:
            side = WidgetPadPosition.LEFT
            alignment = WidgetPadPosition.ALIGN_TOP

        position_config = WidgetPadPosition(
            reference_docker_name="brush_adjust_docker",
            side=side,
            alignment=alignment,
            gap=5,
            fallback_to_canvas_edge=True,
        )

        self.pad = ntWidgetPad(mdiArea, position_config)
        self.pad.setObjectName("toolOptionsPad")
        self.pad.borrowDocker(self.toolOptions)

        self.adjustFilter = ntAdjustToSubwindowFilter(mdiArea)
        self.adjustFilter.setTargetWidget(self.pad)
        mdiArea.subWindowActivated.connect(self.ensureFilterIsInstalled)
        qWin.installEventFilter(self.adjustFilter)

        self.dockerAction = (
            window.qwindow()
            .findChild(QDockWidget, "sharedtooldocker")
            .toggleViewAction()
        )
        self.dockerAction.setEnabled(False)

    def ensureFilterIsInstalled(self, subWin):
        """Ensure the current SubWindow has the filter installed, and
        immediately move the Toolbox to the current View."""
        if subWin:
            subWin.installEventFilter(self.adjustFilter)
            self.pad.adjustToView()

    def returnDocker(self):
        """Return the borrowed docker to its original location"""
        self.pad.returnDocker()
        self.pad.hide()

    def close(self):
        self.dockerAction.setEnabled(True)
        return self.pad.close()
