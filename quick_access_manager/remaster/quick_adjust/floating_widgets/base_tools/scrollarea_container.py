from ....compat import QScrollArea, QVBoxLayout, QWidget


class ntScrollAreaContainer(QWidget):

    def __init__(self, scrollArea=None, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.sa = None

        self.setScrollArea(scrollArea)

    def sizeHint(self):
        """If a QScrollArea has been set, return the size hint of its widget."""
        if self.sa and self.sa.widget():
            return self.sa.widget().sizeHint()
        return super().sizeHint()

    def setScrollArea(self, scrollArea):
        """Set the QScrollArea for the container to hold.

        Returns True on success, the previously set QScrollArea if one was
        replaced (so it can be disposed of), or False if nothing changed.
        """
        if isinstance(scrollArea, QScrollArea) and scrollArea is not self.sa:
            ret = True
            if not self.sa:
                self.layout().addWidget(scrollArea)
            else:
                self.layout().replaceWidget(self.sa, scrollArea)
                ret = self.sa

            self.sa = scrollArea
            return ret

        return False

    def scrollArea(self):
        return self.sa
