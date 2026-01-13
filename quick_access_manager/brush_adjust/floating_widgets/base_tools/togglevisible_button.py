from PyQt5.QtWidgets import QToolButton, QSizePolicy
from PyQt5.QtCore import Qt, QSize


class ntToggleVisibleButton(QToolButton):
    def __init__(self, parent=None):
        super(ntToggleVisibleButton, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setIconSize(QSize(11, 11))

    def setArrow(self, alignment):
        if alignment == "right":
            self.setArrowType(Qt.ArrowType.RightArrow)
        else:
            self.setArrowType(Qt.ArrowType.LeftArrow)
