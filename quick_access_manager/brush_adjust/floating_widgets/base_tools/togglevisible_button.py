from PyQt6.QtWidgets import QToolButton, QSizePolicy
from PyQt6.QtCore import Qt, QSize


class float_tool_optionsggleVisibleButton(QToolButton):
    def __init__(self, parent=None):
        super(float_tool_optionsggleVisibleButton, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setIconSize(QSize(11, 11))

    def setArrow(self, alignment):
        if alignment == "right":
            self.setArrowType(Qt.ArrowType.RightArrow)
        else:
            self.setArrowType(Qt.ArrowType.LeftArrow)
