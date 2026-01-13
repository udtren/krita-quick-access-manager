"""
Plugin for Krita UI Redesign, Copyright (C) 2020 Kapyia, Pedro Reis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

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
from .togglevisible_button import ntToggleVisibleButton
from krita import Krita
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.logs import write_log

# Debug flag - set to False to reduce logging
DEBUG_POSITIONING = False


class ntWidgetPad(QWidget):
    """
    An on-canvas toolbox widget. I'm dubbing widgets that 'float'
    on top of the canvas '(lily) pads' for the time being :)"""

    def __init__(self, parent):
        super(ntWidgetPad, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(4, 4, 4, 4)
        self.alignment = "left"

        # Members to hold a borrowed widget and it's original parent docker for returning
        self.widget = None
        self.widgetDocker = None

        # Track the Quick Brush Docker for positioning
        self.quickBrushDocker = None
        self.dockerEventFilter = None

        # Visibility toggle
        self.btnHide = ntToggleVisibleButton()
        self.btnHide.clicked.connect(self.toggleWidgetVisible)
        self.layout().addWidget(self.btnHide)

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

            globalTargetPos = QPoint()
            if self.alignment == "left":
                globalTargetPos = view.mapToGlobal(QPoint(self.rulerMargin(), 0))
                if DEBUG_POSITIONING:
                    write_log(f"[ntWidgetPad] Alignment: LEFT, Position: {globalTargetPos}")
            elif self.alignment == "right":
                if DEBUG_POSITIONING:
                    write_log(f"[ntWidgetPad] Alignment: RIGHT, searching for docker...")
                # Try to find the Quick Brush Adjust docker
                quick_brush_docker = self.findQuickBrushDocker()
                if quick_brush_docker and quick_brush_docker.isVisible():
                    if DEBUG_POSITIONING:
                        write_log(f"[ntWidgetPad] Docker found and visible, positioning to its left")
                    # Install event filter on docker if not already installed
                    self.installDockerEventFilter(quick_brush_docker)

                    # Get docker's geometry and position
                    docker_geometry = quick_brush_docker.geometry()
                    docker_frame_geometry = quick_brush_docker.frameGeometry()

                    if DEBUG_POSITIONING:
                        # Try multiple methods to get the docker's screen position
                        docker_pos_method1 = quick_brush_docker.mapToGlobal(QPoint(0, 0))
                        docker_pos_method2 = quick_brush_docker.pos()

                        write_log(f"[ntWidgetPad] Docker geometry: {docker_geometry}")
                        write_log(f"[ntWidgetPad] Docker frame geometry: {docker_frame_geometry}")
                        write_log(f"[ntWidgetPad] Docker pos (mapToGlobal): {docker_pos_method1}")
                        write_log(f"[ntWidgetPad] Docker pos (pos()): {docker_pos_method2}")

                    # Use the frame geometry to get the actual screen position
                    docker_x = docker_frame_geometry.x()
                    docker_y = docker_frame_geometry.y()

                    # Position to the left of the docker with a 5px gap
                    globalTargetPos = QPoint(docker_x - self.width() - 5, docker_y)
                    if DEBUG_POSITIONING:
                        write_log(f"[ntWidgetPad] Docker screen pos: ({docker_x}, {docker_y}), Pad width: {self.width()}")
                        write_log(f"[ntWidgetPad] Target position (global): {globalTargetPos}")
                else:
                    if DEBUG_POSITIONING:
                        write_log(f"[ntWidgetPad] Docker not found or hidden, using canvas right edge")
                    # Fallback to canvas right edge if docker not found or hidden
                    globalTargetPos = view.mapToGlobal(
                        QPoint(view.width() - self.width() - self.scrollBarMargin(), 0)
                    )
                    if DEBUG_POSITIONING:
                        write_log(f"[ntWidgetPad] Fallback position (global): {globalTargetPos}")

            local_pos = self.parentWidget().mapFromGlobal(globalTargetPos)
            if DEBUG_POSITIONING:
                write_log(f"[ntWidgetPad] Final local position: {local_pos}")
            self.move(local_pos)

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

            ### GOAL: REMOVE THIS IF-STATEMENT
            if isinstance(self.widget, ntScrollAreaContainer):
                containerSize = self.widget.sizeHint()

                if (
                    view.height()
                    < containerSize.height()
                    + self.btnHide.height()
                    + 14
                    + self.scrollBarMargin()
                ):
                    containerSize.setHeight(
                        view.height()
                        - self.btnHide.height()
                        - 14
                        - self.scrollBarMargin()
                    )

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
        # Ensure there's a widget to return
        if self.widget:
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

    def setViewAlignment(self, newAlignment):
        """
        Set the Pad's alignment to the view to either 'left' or 'right'.
        Returns False if the argument is an invalid value."""
        if isinstance(newAlignment, str):
            if newAlignment.lower() == "left" or newAlignment.lower() == "right":
                self.alignment = newAlignment.lower()

                self.btnHide.setArrow(self.alignment)

                return True

        return False

    def toggleWidgetVisible(self, value=None):
        if not value:
            value = not self.widget.isVisible()

        self.widget.setVisible(value)
        self.adjustToView()
        self.updateHideButtonIcon(value)

    def updateHideButtonIcon(self, isVisible):
        """
        Flip the direction of the arrow to fit the Pads current visibility"""
        if self.alignment == "left":
            if isVisible:
                self.btnHide.setArrowType(Qt.ArrowType.LeftArrow)
            else:
                self.btnHide.setArrowType(Qt.ArrowType.RightArrow)
        elif self.alignment == "right":
            if isVisible:
                self.btnHide.setArrowType(Qt.ArrowType.RightArrow)
            else:
                self.btnHide.setArrowType(Qt.ArrowType.LeftArrow)

    def getViewAlignment(self):
        return self.alignment

    def findQuickBrushDocker(self):
        """Find the Quick Brush Adjustments docker"""
        try:
            app = Krita.instance()
            if app.activeWindow():
                dockers = app.activeWindow().dockers()
                if DEBUG_POSITIONING:
                    write_log(f"[ntWidgetPad] Searching for brush_adjust_docker among {len(dockers)} dockers")
                for docker in dockers:
                    docker_name = docker.objectName()
                    if DEBUG_POSITIONING:
                        write_log(f"[ntWidgetPad] Found docker: {docker_name}")
                    if docker_name == "brush_adjust_docker":
                        if DEBUG_POSITIONING:
                            write_log(f"[ntWidgetPad] ✅ Found brush_adjust_docker!")
                            write_log(f"[ntWidgetPad] Docker visible: {docker.isVisible()}")
                            write_log(f"[ntWidgetPad] Docker geometry: {docker.geometry()}")
                            write_log(f"[ntWidgetPad] Docker position: {docker.pos()}")
                        return docker
                if DEBUG_POSITIONING:
                    write_log(f"[ntWidgetPad] ❌ brush_adjust_docker not found in docker list")
        except Exception as e:
            write_log(f"[ntWidgetPad] Error finding brush_adjust_docker: {e}")  # Always log errors
        return None

    def installDockerEventFilter(self, docker):
        """Install event filter on docker to track its movement and visibility changes"""
        if docker and docker != self.quickBrushDocker:
            # Remove old filter if exists
            self.removeDockerEventFilter()

            # Store reference and install new filter
            self.quickBrushDocker = docker
            self.dockerEventFilter = DockerEventFilter(self)
            docker.installEventFilter(self.dockerEventFilter)

    def removeDockerEventFilter(self):
        """Remove event filter from docker"""
        if self.quickBrushDocker and self.dockerEventFilter:
            try:
                self.quickBrushDocker.removeEventFilter(self.dockerEventFilter)
            except:
                pass
            self.quickBrushDocker = None
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
