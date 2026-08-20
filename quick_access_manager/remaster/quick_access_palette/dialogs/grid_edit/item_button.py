"""Grid Edit's per-item button: click selection, cell drag movement, and -
for Label/Separator/unlocked Action items - an edge drag handle that resizes
instead of moving."""

from ....compat import QColor, QPainter, QPen, QPushButton, Qt

# Width, in pixels, of the right-edge strip that starts a resize drag instead
# of a move drag on a Label/Separator button.
RESIZE_HANDLE_WIDTH = 8


class GridEditItemButton(QPushButton):
    """Grid edit item button that supports click selection, cell drag movement,
    and - for Label/Separator items only - a drag handle that resizes instead
    of moving the item: the right edge for width (col_span), or the bottom
    edge for height (row_span) on a vertical Separator, which grows downward
    instead of sideways."""

    def __init__(self, item, dialog):
        super().__init__(dialog.item_label(item))
        self.item = item
        self.dialog = dialog
        self.drag_start_global_pos = None
        self.drag_mode = None  # "move" or "resize"
        self.setCursor(Qt.SizeAllCursor)
        if self._resizable:
            self.setMouseTracking(True)

    @property
    def _resizable(self):
        return self.dialog.is_resizable(self.item)

    @property
    def _resize_axis(self):
        return self.dialog.resize_axis(self.item) if self._resizable else None

    def _on_resize_handle(self, pos):
        if not self._resizable:
            return False
        if self._resize_axis == "row":
            return pos.y() >= self.height() - RESIZE_HANDLE_WIDTH
        return pos.x() >= self.width() - RESIZE_HANDLE_WIDTH

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._resizable:
            return
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 110), 1))
        if self._resize_axis == "row":
            y = self.height() - RESIZE_HANDLE_WIDTH // 2
            painter.drawLine(6, y, self.width() - 6, y)
        else:
            x = self.width() - RESIZE_HANDLE_WIDTH // 2
            painter.drawLine(x, 6, x, self.height() - 6)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_global_pos = event.globalPos()
            self.drag_mode = "resize" if self._on_resize_handle(event.pos()) else "move"
        elif event.button() == Qt.RightButton:
            self.dialog.show_item_context_menu(self.item, event.globalPos())
            return
        super().mousePressEvent(event)

    def _resize_delta(self, event):
        """The along-axis delta (in cells) for the resize currently in progress."""
        dx = event.globalPos().x() - self.drag_start_global_pos.x()
        dy = event.globalPos().y() - self.drag_start_global_pos.y()
        span = dy if self._resize_axis == "row" else dx
        return int(round(span / float(self.dialog.cell_size)))

    def mouseMoveEvent(self, event):
        if self.drag_start_global_pos is not None and event.buttons() & Qt.LeftButton:
            if self.drag_mode == "resize":
                delta = self._resize_delta(event)
                if delta:
                    kwargs = (
                        {"row_delta": delta}
                        if self._resize_axis == "row"
                        else {"col_delta": delta}
                    )
                    self.dialog.show_resize_highlight(self.item, **kwargs)
                else:
                    self.dialog.hide_drop_highlight()
            else:
                dx = event.globalPos().x() - self.drag_start_global_pos.x()
                dy = event.globalPos().y() - self.drag_start_global_pos.y()
                col_delta = int(round(dx / float(self.dialog.cell_size)))
                row_delta = int(round(dy / float(self.dialog.cell_size)))
                if col_delta or row_delta:
                    self.dialog.show_drop_highlight(self.item, row_delta, col_delta)
                else:
                    self.dialog.hide_drop_highlight()
        elif self._resizable:
            if self._on_resize_handle(event.pos()):
                cursor = Qt.SizeVerCursor if self._resize_axis == "row" else Qt.SizeHorCursor
            else:
                cursor = Qt.SizeAllCursor
            self.setCursor(cursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dialog.hide_drop_highlight()
        if event.button() == Qt.LeftButton and self.drag_start_global_pos is not None:
            if self.drag_mode == "resize":
                delta = self._resize_delta(event)
                if delta:
                    self.dialog.ensure_selected_for_drag(self.item.id)
                    if self._resize_axis == "row":
                        self.dialog.resize_selected(delta, 0)
                    else:
                        self.dialog.resize_selected(0, delta)
                self.drag_start_global_pos = None
                self.drag_mode = None
                return
            dx = event.globalPos().x() - self.drag_start_global_pos.x()
            dy = event.globalPos().y() - self.drag_start_global_pos.y()
            col_delta = int(round(dx / float(self.dialog.cell_size)))
            row_delta = int(round(dy / float(self.dialog.cell_size)))
            if col_delta or row_delta:
                self.dialog.ensure_selected_for_drag(self.item.id)
                self.dialog.move_selected(row_delta, col_delta)
                self.drag_start_global_pos = None
                self.drag_mode = None
                return
        self.drag_start_global_pos = None
        self.drag_mode = None
        super().mouseReleaseEvent(event)
