"""Krita docker discovery/toggle helpers for the remastered palette."""

from krita import Krita  # type: ignore

from ..compat import QCursor, QDockWidget, QPoint


class DockerManager:
    """Discover Krita's own QDockWidgets and toggle their visibility."""

    @staticmethod
    def _qwindow():
        app = Krita.instance()
        main_window = app.activeWindow()
        return main_window.qwindow() if main_window else None

    @staticmethod
    def get_dockers_dict():
        """Return {objectName: titleText} for every docker in the active window."""
        qwin = DockerManager._qwindow()
        if not qwin:
            return {}
        dockers = {}
        for docker in qwin.findChildren(QDockWidget):
            object_name = docker.objectName()
            if object_name:
                dockers[object_name] = docker.windowTitle() or object_name
        return dockers

    @staticmethod
    def toggle_docker(docker_id):
        qwin = DockerManager._qwindow()
        if not qwin or not docker_id:
            return False
        docker = qwin.findChild(QDockWidget, docker_id)
        if not docker:
            return False
        docker.setVisible(not docker.isVisible())
        return True

    @staticmethod
    def toggle_docker_position_at_cursor(docker_id):
        """Toggle a docker between its docked position and floating under the cursor.

        Ported from the dock<->float toggle core of the DockerUnderCursor plugin
        (https://github.com/Aqaao/DockerUnderCursor), scoped to just that toggle.
        """
        qwin = DockerManager._qwindow()
        if not qwin or not docker_id:
            return False
        docker = qwin.findChild(QDockWidget, docker_id)
        if not docker or docker.isHidden():
            return False
        if docker.isFloating():
            docker.setFloating(False)
        else:
            docker.setFloating(True)
            pos = QCursor.pos()
            docker.move(
                QPoint(
                    int(pos.x() - docker.width() / 2),
                    int(pos.y() - docker.height() / 2),
                )
            )
            docker.raise_()
            docker.activateWindow()
        return True
