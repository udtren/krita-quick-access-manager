from krita import Krita  # type: ignore

from ....compat import (
    QDockWidget,
    QEvent,
    QPoint,
    QScrollArea,
    Qt,
    QVBoxLayout,
    QWidget,
)
from .scrollarea_container import ntScrollAreaContainer


class WidgetPadPosition:
    """Configuration class for positioning a widget pad relative to a reference docker"""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

    ALIGN_LEFT = "align_left"
    ALIGN_RIGHT = "align_right"

    ALIGN_TOP = "align_top"
    ALIGN_BOTTOM = "align_bottom"

    def __init__(
        self,
        reference_docker_name=None,
        side=RIGHT,
        alignment=ALIGN_TOP,
        gap=5,
        fallback_to_canvas_edge=True,
    ):
        self.reference_docker_name = reference_docker_name
        self.side = side
        self.alignment = alignment
        self.gap = gap
        self.fallback_to_canvas_edge = fallback_to_canvas_edge

        self._validate()

    def _validate(self):
        valid_sides = [self.LEFT, self.RIGHT, self.TOP, self.BOTTOM]
        if self.side not in valid_sides:
            raise ValueError(
                f"Invalid side '{self.side}'. Must be one of: {valid_sides}"
            )

        if self.side in [self.LEFT, self.RIGHT]:
            valid_alignments = [self.ALIGN_TOP, self.ALIGN_BOTTOM]
            if self.alignment not in valid_alignments:
                raise ValueError(
                    f"For LEFT/RIGHT side, alignment must be one of: {valid_alignments}"
                )
        elif self.side in [self.TOP, self.BOTTOM]:
            valid_alignments = [self.ALIGN_LEFT, self.ALIGN_RIGHT]
            if self.alignment not in valid_alignments:
                raise ValueError(
                    f"For TOP/BOTTOM side, alignment must be one of: {valid_alignments}"
                )

class ntWidgetPad(QWidget):
    def __init__(self, parent, position_config=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(4, 4, 4, 4)

        if position_config is None:
            position_config = WidgetPadPosition(
                reference_docker_name=None, side=WidgetPadPosition.LEFT
            )
        self.position_config = position_config

        self.alignment = (
            "left"
            if position_config.side == WidgetPadPosition.LEFT
            else "right" if position_config.side == WidgetPadPosition.RIGHT else "left"
        )

        self.widget = None
        self.widgetDocker = None

        self.referenceDocker = None
        self.dockerEventFilter = None

        self.user_visible = True
        self._adjusting = False

    def activeView(self):
        """Get the View widget of the active subwindow."""
        if not self.parentWidget():
            return None

        subWin = self.parentWidget().activeSubWindow()
        if not subWin:
            return None

        for child in subWin.children():
            if "view" in child.objectName():
                return child

        return None

    def adjustToView(self):
        """Adjust the position and size of the Pad to that of the active View."""
        if self._adjusting:
            return
        self._adjusting = True
        try:
            self._adjustToView()
        finally:
            self._adjusting = False

    def _adjustToView(self):
        view = self.activeView()
        if view:
            self.resizeToView()

            globalTargetPos = None

            if self.position_config.reference_docker_name:
                reference_docker = self.findReferenceDocker()
                if reference_docker and reference_docker.isVisible():
                    globalTargetPos = self._calculateDockerRelativePosition(
                        reference_docker
                    )
                    self.installDockerEventFilter(reference_docker)
                    if not self.isVisible() and self.user_visible:
                        self.show()
                else:
                    self.hide()
                    return

            if globalTargetPos is None:
                globalTargetPos = self._calculateCanvasEdgePosition(view)

            local_pos = self.parentWidget().mapFromGlobal(globalTargetPos)
            # Only move when it actually changes: move()/resize() inside a paint
            # pass schedules another paint, which would spin forever.
            if local_pos != self.pos():
                self.move(local_pos)

    def _calculateDockerRelativePosition(self, docker):
        docker_frame_geometry = docker.frameGeometry()
        docker_x = docker_frame_geometry.x()
        docker_y = docker_frame_geometry.y()
        docker_width = docker_frame_geometry.width()
        docker_height = docker_frame_geometry.height()

        config = self.position_config
        gap = config.gap

        if config.side == WidgetPadPosition.LEFT:
            x = docker_x - self.width() - gap
            if config.alignment == WidgetPadPosition.ALIGN_TOP:
                y = docker_y
            else:
                y = docker_y + docker_height - self.height()

        elif config.side == WidgetPadPosition.RIGHT:
            x = docker_x + docker_width + gap
            if config.alignment == WidgetPadPosition.ALIGN_TOP:
                y = docker_y
            else:
                y = docker_y + docker_height - self.height()

        elif config.side == WidgetPadPosition.TOP:
            y = docker_y - self.height() - gap
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = docker_x
            else:
                x = docker_x + docker_width - self.width()

        elif config.side == WidgetPadPosition.BOTTOM:
            y = docker_y + docker_height + gap
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = docker_x
            else:
                x = docker_x + docker_width - self.width()

        return QPoint(x, y)

    def _calculateCanvasEdgePosition(self, view):
        config = self.position_config

        if config.side == WidgetPadPosition.LEFT:
            return view.mapToGlobal(QPoint(self.rulerMargin(), 0))

        elif config.side == WidgetPadPosition.RIGHT:
            return view.mapToGlobal(
                QPoint(view.width() - self.width() - self.scrollBarMargin(), 0)
            )

        elif config.side == WidgetPadPosition.TOP:
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = self.rulerMargin()
            else:
                x = view.width() - self.width() - self.scrollBarMargin()
            return view.mapToGlobal(QPoint(x, 0))

        elif config.side == WidgetPadPosition.BOTTOM:
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = self.rulerMargin()
            else:
                x = view.width() - self.width() - self.scrollBarMargin()
            return view.mapToGlobal(
                QPoint(x, view.height() - self.height() - self.scrollBarMargin())
            )

        return view.mapToGlobal(QPoint(self.rulerMargin(), 0))

    def borrowDocker(self, docker):
        """Borrow a docker widget from Krita's existing docker list.

        Returns True on success, False if an invalid widget was passed.
        """
        if isinstance(docker, QDockWidget) and docker.widget():
            self.returnDocker()

            self.widgetDocker = docker

            if isinstance(docker.widget(), QScrollArea):
                self.widget = ntScrollAreaContainer(docker.widget())
            else:
                self.widget = docker.widget()

            self.layout().addWidget(self.widget)
            self.layout().invalidate()
            self.layout().activate()
            self.adjustToView()
            self.widgetDocker.hide()

            return True

        return False

    def closeEvent(self, e):
        """The pad borrows the actual docker widget, so it must be returned on close."""
        self.removeDockerEventFilter()
        self.returnDocker()
        return super().closeEvent(e)

    def paintEvent(self, e):
        """Needed to resize the Pad if the user changes the toolbox icon size."""
        self.adjustToView()
        return super().paintEvent(e)

    def resizeToView(self):
        """Resize the Pad to fit within the subwindow."""
        view = self.activeView()

        if view:
            if isinstance(self.widget, ntScrollAreaContainer):
                containerSize = self.widget.sizeHint()

                if view.height() < containerSize.height() + 14 + self.scrollBarMargin():
                    containerSize.setHeight(view.height() - 14 - self.scrollBarMargin())

                if view.width() < containerSize.width() + 8 + self.scrollBarMargin():
                    containerSize.setWidth(view.width() - 8 - self.scrollBarMargin())

                if containerSize != self.widget.size():
                    self.widget.setFixedSize(containerSize)

            newSize = self.sizeHint()
            if view.height() < newSize.height():
                newSize.setHeight(view.height())

            if view.width() < newSize.width():
                newSize.setWidth(view.width())

            if newSize != self.size():
                self.resize(newSize)

    def returnDocker(self):
        """Return the borrowed docker to its original QDockWidget"""
        if self.widget and self.widgetDocker:
            self.layout().removeWidget(self.widget)

            if isinstance(self.widget, ntScrollAreaContainer):
                self.widgetDocker.setWidget(self.widget.scrollArea())
            else:
                self.widgetDocker.setWidget(self.widget)

            self.widgetDocker.show()
            self.widget = None
            self.widgetDocker = None

    def rulerMargin(self):
        if Krita.instance().readSetting("", "showrulers", "true") == "true":
            return 20
        return 0

    def scrollBarMargin(self):
        if Krita.instance().readSetting("", "hideScrollbars", "false") == "true":
            return 0
        return 14

    def setUserVisible(self, visible):
        """Set user's visibility preference and show/hide accordingly"""
        self.user_visible = visible
        if visible:
            self.show()
            self.adjustToView()
        else:
            self.hide()

    def findReferenceDocker(self):
        """Find the reference docker specified in position configuration"""
        if not self.position_config.reference_docker_name:
            return None

        try:
            app = Krita.instance()
            if app.activeWindow():
                dockers = app.activeWindow().dockers()
                docker_name_to_find = self.position_config.reference_docker_name

                for docker in dockers:
                    if docker.objectName() == docker_name_to_find:
                        return docker
        except Exception:
            pass

        return None

    def installDockerEventFilter(self, docker):
        """Install event filter on docker to track its movement and visibility changes"""
        if docker and docker != self.referenceDocker:
            self.removeDockerEventFilter()
            self.referenceDocker = docker
            self.dockerEventFilter = DockerEventFilter(self)
            docker.installEventFilter(self.dockerEventFilter)

    def removeDockerEventFilter(self):
        """Remove event filter from docker"""
        if self.referenceDocker and self.dockerEventFilter:
            try:
                self.referenceDocker.removeEventFilter(self.dockerEventFilter)
            except Exception:
                pass
            self.referenceDocker = None
            self.dockerEventFilter = None


class DockerEventFilter(QWidget):
    """Event filter to track docker movement, resize, and visibility changes"""

    def __init__(self, pad):
        super().__init__()
        self.pad = pad

    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.Move,
            QEvent.Resize,
            QEvent.Show,
            QEvent.Hide,
            QEvent.WindowActivate,
            QEvent.WindowDeactivate,
        ):
            if hasattr(self.pad, "adjustToView"):
                self.pad.adjustToView()

        return super().eventFilter(obj, event)
