from PyQt5.QtWidgets import (
    QWidget,
    QToolButton,
    QDockWidget,
    QVBoxLayout,
    QSizePolicy,
    QScrollArea,
)
from PyQt5.QtCore import Qt, QSize, QPoint, QEvent
from .scrollarea_container import ntScrollAreaContainer
from krita import Krita
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import logging utility
try:
    from ....utils.logs import write_log
except ImportError:
    # Fallback if logging utility not available
    def write_log(message):
        print(message)


# Debug flag - set to False to reduce logging
DEBUG_POSITIONING = False


class WidgetPadPosition:
    """Configuration class for positioning a widget pad relative to a reference docker"""

    # Side constants
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

    # Alignment constants for horizontal sides (top/bottom)
    ALIGN_LEFT = "align_left"
    ALIGN_RIGHT = "align_right"

    # Alignment constants for vertical sides (left/right)
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
        """
        Initialize position configuration.

        Args:
            reference_docker_name: Object name of the docker to position relative to (e.g., "brush_adjust_docker")
                                   If None, positions relative to canvas edges
            side: Which side of the reference docker to position on (LEFT, RIGHT, TOP, BOTTOM)
            alignment: Alignment along the perpendicular axis:
                      - For LEFT/RIGHT sides: ALIGN_TOP or ALIGN_BOTTOM
                      - For TOP/BOTTOM sides: ALIGN_LEFT or ALIGN_RIGHT
            gap: Gap in pixels between the widget pad and reference docker
            fallback_to_canvas_edge: If True and docker not found/visible, fall back to canvas edge positioning
        """
        self.reference_docker_name = reference_docker_name
        self.side = side
        self.alignment = alignment
        self.gap = gap
        self.fallback_to_canvas_edge = fallback_to_canvas_edge

        # Validate configuration
        self._validate()

    def _validate(self):
        """Validate the configuration"""
        valid_sides = [self.LEFT, self.RIGHT, self.TOP, self.BOTTOM]
        if self.side not in valid_sides:
            raise ValueError(
                f"Invalid side '{self.side}'. Must be one of: {valid_sides}"
            )

        # Validate alignment based on side
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

    def is_horizontal_side(self):
        """Returns True if side is TOP or BOTTOM"""
        return self.side in [self.TOP, self.BOTTOM]

    def is_vertical_side(self):
        """Returns True if side is LEFT or RIGHT"""
        return self.side in [self.LEFT, self.RIGHT]


class ntWidgetPad(QWidget):
    def __init__(self, parent, position_config=None):
        """
        Initialize the widget pad.

        Args:
            parent: Parent widget
            position_config: WidgetPadPosition object for positioning configuration.
                           If None, defaults to left alignment on canvas edge.
        """
        super(ntWidgetPad, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(4, 4, 4, 4)

        # Store position configuration
        if position_config is None:
            # Default: left side of canvas
            position_config = WidgetPadPosition(
                reference_docker_name=None, side=WidgetPadPosition.LEFT
            )
        self.position_config = position_config

        # Legacy alignment property (for backward compatibility with old toggle button logic)
        # Maps to the side where the pad is positioned
        self.alignment = (
            "left"
            if position_config.side == WidgetPadPosition.LEFT
            else "right" if position_config.side == WidgetPadPosition.RIGHT else "left"
        )  # Default to left for top/bottom

        # Members to hold a borrowed widget and it's original parent docker for returning
        self.widget = None
        self.widgetDocker = None

        # Track the reference docker for positioning
        self.referenceDocker = None
        self.dockerEventFilter = None

    def activeView(self):
        """
        Get the View widget of the active subwindow."""
        if not self.parentWidget():
            return None

        subWin = self.parentWidget().activeSubWindow()

        if not subWin:
            return None

        for child in subWin.children():
            if (
                "view" in child.objectName()
            ):  # Grab the View from the active tab/sub-window
                return child

        return None

    def adjustToView(self):
        """
        Adjust the position and size of the Pad to that of the active View."""
        view = self.activeView()
        if view:
            self.resizeToView()

            globalTargetPos = None

            # Check if we should position relative to a docker
            if self.position_config.reference_docker_name:
                reference_docker = self.findReferenceDocker()
                if reference_docker and reference_docker.isVisible():
                    globalTargetPos = self._calculateDockerRelativePosition(
                        reference_docker
                    )
                    # Install event filter on docker if not already installed
                    self.installDockerEventFilter(reference_docker)
                    # Show the pad if it was hidden
                    if not self.isVisible():
                        self.show()
                else:
                    # Reference docker is not visible - just hide the pad (keep docker borrowed)
                    if DEBUG_POSITIONING:
                        write_log(
                            f"[ntWidgetPad] Reference docker not visible, hiding pad"
                        )
                    self.hide()
                    return

            # Fallback to canvas edge positioning if no docker position calculated
            if globalTargetPos is None:
                globalTargetPos = self._calculateCanvasEdgePosition(view)

            local_pos = self.parentWidget().mapFromGlobal(globalTargetPos)
            if DEBUG_POSITIONING:
                write_log(f"[ntWidgetPad] Final local position: {local_pos}")
            self.move(local_pos)

    def _calculateDockerRelativePosition(self, docker):
        """Calculate position relative to a reference docker"""
        if DEBUG_POSITIONING:
            write_log(
                f"[ntWidgetPad] Positioning relative to docker: {docker.objectName()}"
            )

        docker_frame_geometry = docker.frameGeometry()
        docker_x = docker_frame_geometry.x()
        docker_y = docker_frame_geometry.y()
        docker_width = docker_frame_geometry.width()
        docker_height = docker_frame_geometry.height()

        if DEBUG_POSITIONING:
            write_log(
                f"[ntWidgetPad] Docker position: ({docker_x}, {docker_y}), size: ({docker_width}x{docker_height})"
            )
            write_log(f"[ntWidgetPad] Pad size: ({self.width()}x{self.height()})")

        config = self.position_config
        gap = config.gap

        # Calculate position based on side
        if config.side == WidgetPadPosition.LEFT:
            # Position to the left of docker
            x = docker_x - self.width() - gap
            # Alignment along vertical axis
            if config.alignment == WidgetPadPosition.ALIGN_TOP:
                y = docker_y
            else:  # ALIGN_BOTTOM
                y = docker_y + docker_height - self.height()

        elif config.side == WidgetPadPosition.RIGHT:
            # Position to the right of docker
            x = docker_x + docker_width + gap
            # Alignment along vertical axis
            if config.alignment == WidgetPadPosition.ALIGN_TOP:
                y = docker_y
            else:  # ALIGN_BOTTOM
                y = docker_y + docker_height - self.height()

        elif config.side == WidgetPadPosition.TOP:
            # Position above docker
            y = docker_y - self.height() - gap
            # Alignment along horizontal axis
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = docker_x
            else:  # ALIGN_RIGHT
                x = docker_x + docker_width - self.width()

        elif config.side == WidgetPadPosition.BOTTOM:
            # Position below docker
            y = docker_y + docker_height + gap
            # Alignment along horizontal axis
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = docker_x
            else:  # ALIGN_RIGHT
                x = docker_x + docker_width - self.width()

        globalTargetPos = QPoint(x, y)
        if DEBUG_POSITIONING:
            write_log(
                f"[ntWidgetPad] Calculated docker-relative position: {globalTargetPos}"
            )

        return globalTargetPos

    def _calculateCanvasEdgePosition(self, view):
        """Calculate position at canvas edge based on configuration side"""
        if DEBUG_POSITIONING:
            write_log(
                f"[ntWidgetPad] Using canvas edge positioning, side: {self.position_config.side}"
            )

        config = self.position_config

        if config.side == WidgetPadPosition.LEFT:
            # Left edge of canvas
            return view.mapToGlobal(QPoint(self.rulerMargin(), 0))

        elif config.side == WidgetPadPosition.RIGHT:
            # Right edge of canvas
            return view.mapToGlobal(
                QPoint(view.width() - self.width() - self.scrollBarMargin(), 0)
            )

        elif config.side == WidgetPadPosition.TOP:
            # Top edge of canvas
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = self.rulerMargin()
            else:  # ALIGN_RIGHT
                x = view.width() - self.width() - self.scrollBarMargin()
            return view.mapToGlobal(QPoint(x, 0))

        elif config.side == WidgetPadPosition.BOTTOM:
            # Bottom edge of canvas
            if config.alignment == WidgetPadPosition.ALIGN_LEFT:
                x = self.rulerMargin()
            else:  # ALIGN_RIGHT
                x = view.width() - self.width() - self.scrollBarMargin()
            return view.mapToGlobal(
                QPoint(x, view.height() - self.height() - self.scrollBarMargin())
            )

        # Default fallback to left
        return view.mapToGlobal(QPoint(self.rulerMargin(), 0))

    def borrowDocker(self, docker):
        """
        Borrow a docker widget from Krita's existing list of dockers and
        returns True. Returns False if invalid widget was passed."""

        # Does requested widget exist?
        if isinstance(docker, QDockWidget) and docker.widget():
            # Return any previous widget to its original docker
            self.returnDocker()

            self.widgetDocker = docker

            if isinstance(docker.widget(), QScrollArea):
                self.widget = ntScrollAreaContainer(docker.widget())
            else:
                self.widget = docker.widget()

            self.layout().addWidget(self.widget)
            # Force layout to recalculate
            self.layout().invalidate()
            self.layout().activate()
            self.adjustToView()
            self.widgetDocker.hide()

            return True

        return False

    def closeEvent(self, e):
        """
        Since the plugins works by borrowing the actual docker
        widget we need to ensure its returned upon closing the pad"""
        # Remove docker event filter if installed
        self.removeDockerEventFilter()
        self.returnDocker()
        return super().closeEvent(e)

    def paintEvent(self, e):
        """
        Needed to resize the Pad if the user decides to
        change the icon size of the toolbox"""
        self.adjustToView()
        return super().paintEvent(e)

    def resizeToView(self):
        """
        Resize the Pad to an appropriate size that fits within the subwindow."""
        view = self.activeView()

        if view:
            if isinstance(self.widget, ntScrollAreaContainer):
                containerSize = self.widget.sizeHint()

                if view.height() < containerSize.height() + 14 + self.scrollBarMargin():
                    containerSize.setHeight(view.height() - 14 - self.scrollBarMargin())

                if view.width() < containerSize.width() + 8 + self.scrollBarMargin():
                    containerSize.setWidth(view.width() - 8 - self.scrollBarMargin())

                self.widget.setFixedSize(containerSize)

            newSize = self.sizeHint()
            if view.height() < newSize.height():
                newSize.setHeight(view.height())

            if view.width() < newSize.width():
                newSize.setWidth(view.width())

            self.resize(newSize)

    def returnDocker(self):
        """
        Return the borrowed docker to it's original QDockWidget"""
        # Ensure there's a widget and docker to return
        if self.widget and self.widgetDocker:
            # Remove the widget from the pad's layout first
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
            return 20  # Canvas ruler pixel width on Windows
        return 0

    def scrollBarMargin(self):
        if Krita.instance().readSetting("", "hideScrollbars", "false") == "true":
            return 0

        return 14  # Canvas crollbar pixel width/height on Windows

    def getViewAlignment(self):
        return self.alignment

    def findReferenceDocker(self):
        """Find the reference docker specified in position configuration"""
        if not self.position_config.reference_docker_name:
            return None

        try:
            app = Krita.instance()
            if app.activeWindow():
                dockers = app.activeWindow().dockers()
                docker_name_to_find = self.position_config.reference_docker_name

                if DEBUG_POSITIONING:
                    write_log(
                        f"[ntWidgetPad] Searching for {docker_name_to_find} among {len(dockers)} dockers"
                    )

                for docker in dockers:
                    docker_name = docker.objectName()
                    if DEBUG_POSITIONING:
                        write_log(f"[ntWidgetPad] Found docker: {docker_name}")

                    if docker_name == docker_name_to_find:
                        if DEBUG_POSITIONING:
                            write_log(f"[ntWidgetPad] ✅ Found {docker_name_to_find}!")
                            write_log(
                                f"[ntWidgetPad] Docker visible: {docker.isVisible()}"
                            )
                            write_log(
                                f"[ntWidgetPad] Docker geometry: {docker.geometry()}"
                            )
                            write_log(f"[ntWidgetPad] Docker position: {docker.pos()}")
                        return docker

                if DEBUG_POSITIONING:
                    write_log(
                        f"[ntWidgetPad] ❌ {docker_name_to_find} not found in docker list"
                    )
        except Exception as e:
            write_log(
                f"[ntWidgetPad] Error finding {self.position_config.reference_docker_name}: {e}"
            )  # Always log errors
        return None

    def installDockerEventFilter(self, docker):
        """Install event filter on docker to track its movement and visibility changes"""
        if docker and docker != self.referenceDocker:
            # Remove old filter if exists
            self.removeDockerEventFilter()

            # Store reference and install new filter
            self.referenceDocker = docker
            self.dockerEventFilter = DockerEventFilter(self)
            docker.installEventFilter(self.dockerEventFilter)

    def removeDockerEventFilter(self):
        """Remove event filter from docker"""
        if self.referenceDocker and self.dockerEventFilter:
            try:
                self.referenceDocker.removeEventFilter(self.dockerEventFilter)
            except:
                pass
            self.referenceDocker = None
            self.dockerEventFilter = None


class DockerEventFilter(QWidget):
    """Event filter to track docker movement, resize, and visibility changes"""

    def __init__(self, pad):
        super().__init__()
        self.pad = pad

    def eventFilter(self, obj, event):
        """Monitor docker events and adjust pad position accordingly"""
        if event.type() in [
            QEvent.Move,
            QEvent.Resize,
            QEvent.Show,
            QEvent.Hide,
            QEvent.WindowActivate,
            QEvent.WindowDeactivate,
        ]:
            # Adjust pad position when docker moves, resizes, or visibility changes
            if hasattr(self.pad, "adjustToView"):
                self.pad.adjustToView()

        return super().eventFilter(obj, event)
