"""Ctrl + left-drag direct manipulation: move a placed grid item without
opening the Grid Edit dialog."""

from ...compat import QEvent, QObject, QRect, QRubberBand, Qt, QTimer

# Gap between grid cells, in pixels. The drag filter maps mouse deltas back to
# cells with it, so it has to match the geometry create_grid_widget() lays out.
GRID_CELL_SPACING = 2


class GridItemDragFilter(QObject):
    """Ctrl + left-drag moves one placed item to another cell of its grid.

    Installed on every item widget the docker builds. A plain left-click still
    activates the item (run the action, pick the brush, ...); only a Ctrl-held
    press starts a drag, and that press is swallowed so the widget never fires
    its click. Everything else - the multi-select marquee, resizing, moving
    items between tabs - stays in the Grid Edit dialog.
    """

    def __init__(self, docker):
        super().__init__(docker)
        self.docker = docker
        self.item_id = None
        self.start_pos = None
        self.highlight = None

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QEvent.MouseButtonPress:
            return self._start_drag(watched, event)
        if self.item_id is None:
            return False
        if event_type == QEvent.MouseMove:
            self._update_highlight(watched, event)
            return True
        if event_type == QEvent.MouseButtonRelease:
            self._finish_drag(watched, event)
            return True
        return False

    # ------------------------------------------------------------------
    def _start_drag(self, watched, event):
        if event.button() != Qt.LeftButton:
            if self.item_id is not None:
                # Any other button during a drag cancels it (and is swallowed,
                # so a right-click aborts instead of opening the item menu).
                self._cancel_drag()
                return True
            return False
        if not (event.modifiers() & Qt.ControlModifier):
            return False
        item_id = watched.property("palette_item_id")
        if not item_id or self.docker.find_active_item(item_id) is None:
            return False
        self.item_id = item_id
        self.start_pos = self._global_pos(event)
        return True

    def _update_highlight(self, watched, event):
        target = self._target_position(watched, event)
        if target is None:
            self._hide_highlight()
            return
        item, row, col = target
        grid_widget = watched.parentWidget()
        if grid_widget is None:
            return
        if self.highlight is None or self.highlight.parentWidget() is not grid_widget:
            self._hide_highlight()
            self.highlight = QRubberBand(QRubberBand.Rectangle, grid_widget)
        self.highlight.setGeometry(
            QRect(*self.docker.cell_geometry(row, col, item.row_span, item.col_span))
        )
        self.highlight.show()

    def _finish_drag(self, watched, event):
        target = self._target_position(watched, event)
        self._cancel_drag()
        if target is None:
            return
        item, row, col = target
        if (row, col) == (item.row, item.col):
            return
        # Deferred: applying the move rebuilds the tab pages, which deletes the
        # very widget whose mouse release is still being delivered.
        QTimer.singleShot(0, lambda: self.docker.move_item(item.id, row, col))

    def _cancel_drag(self):
        self._hide_highlight()
        self.item_id = None
        self.start_pos = None

    def _target_position(self, watched, event):
        """The clamped (item, row, col) this drag currently points at."""
        item = self.docker.find_active_item(self.item_id)
        if item is None or self.start_pos is None:
            return None
        grid = self.docker.controller.active_grid()
        if grid is None:
            return None
        step = self.docker.item_cell_size() + GRID_CELL_SPACING
        delta = self._global_pos(event) - self.start_pos
        row = max(0, item.row + int(round(delta.y() / float(step))))
        col = item.col + int(round(delta.x() / float(step)))
        col = max(0, min(col, max(0, grid.columns - item.col_span)))
        return item, row, col

    def _hide_highlight(self):
        if self.highlight is not None:
            self.highlight.hide()
            self.highlight.setParent(None)
            self.highlight.deleteLater()
            self.highlight = None

    def _global_pos(self, event):
        try:
            return event.globalPos()  # PyQt5
        except AttributeError:
            return event.globalPosition().toPoint()  # PyQt6
