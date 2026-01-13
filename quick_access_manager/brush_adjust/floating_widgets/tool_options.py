from PyQt5.QtWidgets import QMdiArea, QDockWidget
from .base_tools.adjust_to_subwindow_filter import ntAdjustToSubwindowFilter
from .base_tools.widget_pad import ntWidgetPad, WidgetPadPosition


class ntToolOptions:

    def __init__(self, window):
        qWin = window.qwindow()
        mdiArea = qWin.findChild(QMdiArea)
        toolOptions = qWin.findChild(QDockWidget, "sharedtooldocker")

        # Create position configuration: Position to the LEFT of the brush_adjust_docker,
        # aligned to the TOP
        position_config = WidgetPadPosition(
            reference_docker_name="brush_adjust_docker",
            side=WidgetPadPosition.LEFT,
            alignment=WidgetPadPosition.ALIGN_TOP,
            gap=5,
            fallback_to_canvas_edge=True,
        )

        # Create "pad" with the position configuration
        self.pad = ntWidgetPad(mdiArea, position_config)
        self.pad.setObjectName("toolOptionsPad")
        self.pad.borrowDocker(toolOptions)

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
            self.updateStyleSheet()

    def findDockerAction(self, window, text):
        dockerMenu = None

        for m in window.qwindow().actions():
            if m.objectName() == "settings_dockers_menu":
                dockerMenu = m

                for a in dockerMenu.menu().actions():
                    if a.text().replace("&", "") == text:
                        return a

        return False

    def updateStyleSheet(self):
        # variables.setColors()
        # self.pad.setStyleSheet(variables.nu_tool_options_style)
        return

    def close(self):
        self.dockerAction.setEnabled(True)
        return self.pad.close()
