"""Grid Edit's canvas widget: draws the cell guides and runs the rubber-band
(marquee) multi-select."""

from ....compat import (
    QApplication,
    QColor,
    QPainter,
    QPen,
    QRect,
    QRubberBand,
    QSize,
    Qt,
    QWidget,
)


class GridEditCanvas(QWidget):
    """Grid background that supports rubber-band (marquee) multi-select."""

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog
        self.rubber_band = None
        self.origin = None
        self.grid_rows = 0
        self.grid_columns = 0

    def paintEvent(self, event):
        """Draw the cell guides.

        Cheaper than the QFrame-per-cell approach it replaces, which rebuilt
        rows x columns widgets on every drop.
        """
        super().paintEvent(event)
        if not self.grid_rows or not self.grid_columns:
            return
        cell = self.dialog.cell_size
        spacing = self.dialog.spacing
        painter = QPainter(self)
        painter.setPen(QPen(QColor("#3f3f3f"), 1))
        painter.setBrush(Qt.NoBrush)
        for row in range(self.grid_rows):
            y = 4 + row * (cell + spacing)
            for col in range(self.grid_columns):
                x = 4 + col * (cell + spacing)
                painter.drawRect(x, y, cell - 1, cell - 1)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            if self.rubber_band is None:
                self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.origin is not None and self.rubber_band is not None:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.origin is not None and self.rubber_band is not None:
            selection_rect = self.rubber_band.geometry()
            self.rubber_band.hide()
            self.origin = None
            additive = QApplication.keyboardModifiers() == Qt.ControlModifier
            self.dialog.select_items_in_rect(selection_rect, additive=additive)
            return
        super().mouseReleaseEvent(event)
