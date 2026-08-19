"""PyQt5 / PyQt6 compatibility shim.

Import all Qt symbols from this module instead of directly from PyQt5 or PyQt6.
The shim detects which binding is available and patches PyQt6 to expose the
old-style flat enum names that PyQt5 used (e.g. Qt.AlignLeft instead of
Qt.AlignmentFlag.AlignLeft), so the rest of the codebase can remain unchanged.
"""

try:
    from PyQt5.QtCore import (
        QEvent,
        QMimeData,
        QObject,
        QPoint,
        QPointF,
        QRect,
        QRectF,
        QSize,
        Qt,
        QTimer,
        pyqtSignal,
    )
    from PyQt5.QtGui import (
        QBrush,
        QColor,
        QCursor,
        QDrag,
        QFont,
        QFontMetrics,
        QIcon,
        QIntValidator,
        QKeyEvent,
        QKeySequence,
        QLinearGradient,
        QPainter,
        QPalette,
        QPen,
        QPixmap,
    )
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QAction,
        QApplication,
        QCheckBox,
        QColorDialog,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QKeySequenceEdit,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMdiArea,
        QMenu,
        QMessageBox,
        QPushButton,
        QRubberBand,
        QScrollArea,
        QShortcut,
        QSizePolicy,
        QSlider,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT6 = False

except ImportError:
    from PyQt6.QtCore import (  # noqa: F401
        QEvent,
        QMimeData,
        QObject,
        QPoint,
        QPointF,
        QRect,
        QRectF,
        QSize,
        Qt,
        QTimer,
        pyqtSignal,
    )
    from PyQt6.QtGui import (  # noqa: F401
        QAction,
        QBrush,
        QColor,
        QCursor,
        QDrag,
        QFont,
        QFontMetrics,
        QIcon,
        QIntValidator,
        QKeyEvent,
        QKeySequence,
        QLinearGradient,
        QMouseEvent,
        QPainter,
        QPalette,
        QPen,
        QPixmap,
        QShortcut,
    )
    from PyQt6.QtWidgets import (  # noqa: F401
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QColorDialog,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QKeySequenceEdit,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMdiArea,
        QMenu,
        QMessageBox,
        QPushButton,
        QRubberBand,
        QScrollArea,
        QSizePolicy,
        QSlider,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

    PYQT6 = True

    # ------------------------------------------------------------------
    # Patch flat enum aliases onto Qt (PyQt5 style 竊・PyQt6 namespaced)
    # ------------------------------------------------------------------

    # Alignment
    Qt.AlignLeft = Qt.AlignmentFlag.AlignLeft
    Qt.AlignRight = Qt.AlignmentFlag.AlignRight
    Qt.AlignTop = Qt.AlignmentFlag.AlignTop
    Qt.AlignBottom = Qt.AlignmentFlag.AlignBottom
    Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
    Qt.AlignHCenter = Qt.AlignmentFlag.AlignHCenter
    Qt.AlignVCenter = Qt.AlignmentFlag.AlignVCenter

    # Mouse buttons
    Qt.LeftButton = Qt.MouseButton.LeftButton
    Qt.RightButton = Qt.MouseButton.RightButton
    Qt.MiddleButton = Qt.MouseButton.MiddleButton
    Qt.NoButton = Qt.MouseButton.NoButton

    # Keyboard modifiers
    Qt.NoModifier = Qt.KeyboardModifier.NoModifier
    Qt.ShiftModifier = Qt.KeyboardModifier.ShiftModifier
    Qt.ControlModifier = Qt.KeyboardModifier.ControlModifier
    Qt.AltModifier = Qt.KeyboardModifier.AltModifier
    Qt.MetaModifier = Qt.KeyboardModifier.MetaModifier

    # Keys 窶・common named keys
    Qt.Key_Shift = Qt.Key.Key_Shift
    Qt.Key_Control = Qt.Key.Key_Control
    Qt.Key_Alt = Qt.Key.Key_Alt
    Qt.Key_Meta = Qt.Key.Key_Meta
    Qt.Key_Escape = Qt.Key.Key_Escape
    Qt.Key_Space = Qt.Key.Key_Space
    Qt.Key_Return = Qt.Key.Key_Return
    Qt.Key_Enter = Qt.Key.Key_Enter
    Qt.Key_Tab = Qt.Key.Key_Tab
    Qt.Key_Backspace = Qt.Key.Key_Backspace
    Qt.Key_QuoteLeft = Qt.Key.Key_QuoteLeft
    Qt.Key_Delete = Qt.Key.Key_Delete
    Qt.Key_Left = Qt.Key.Key_Left
    Qt.Key_Right = Qt.Key.Key_Right
    Qt.Key_Up = Qt.Key.Key_Up
    Qt.Key_Down = Qt.Key.Key_Down

    # Keys 窶・A-Z
    for _c in range(ord("A"), ord("Z") + 1):
        setattr(Qt, f"Key_{chr(_c)}", Qt.Key[f"Key_{chr(_c)}"])

    # Keys 窶・0-9
    for _d in range(10):
        setattr(Qt, f"Key_{_d}", Qt.Key[f"Key_{_d}"])

    # Keys 窶・F1-F12
    for _i in range(1, 13):
        setattr(Qt, f"Key_F{_i}", Qt.Key[f"Key_F{_i}"])

    # Window flags / types
    Qt.FramelessWindowHint = Qt.WindowType.FramelessWindowHint
    Qt.WindowStaysOnTopHint = Qt.WindowType.WindowStaysOnTopHint
    Qt.Tool = Qt.WindowType.Tool
    Qt.ToolTip = Qt.WindowType.ToolTip
    Qt.Dialog = Qt.WindowType.Dialog
    Qt.Window = Qt.WindowType.Window
    Qt.SubWindow = Qt.WindowType.SubWindow

    # Widget attributes
    Qt.WA_DeleteOnClose = Qt.WidgetAttribute.WA_DeleteOnClose
    Qt.WA_TranslucentBackground = Qt.WidgetAttribute.WA_TranslucentBackground

    # Cursor shapes
    Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor
    Qt.ArrowCursor = Qt.CursorShape.ArrowCursor
    Qt.SizeAllCursor = Qt.CursorShape.SizeAllCursor

    # Scroll bar policies
    Qt.ScrollBarAlwaysOff = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    Qt.ScrollBarAlwaysOn = Qt.ScrollBarPolicy.ScrollBarAlwaysOn
    Qt.ScrollBarAsNeeded = Qt.ScrollBarPolicy.ScrollBarAsNeeded

    # Drop actions
    Qt.MoveAction = Qt.DropAction.MoveAction
    Qt.CopyAction = Qt.DropAction.CopyAction

    # Aspect ratio / transformation
    Qt.KeepAspectRatio = Qt.AspectRatioMode.KeepAspectRatio
    Qt.SmoothTransformation = Qt.TransformationMode.SmoothTransformation

    # Global colors
    Qt.gray = Qt.GlobalColor.gray
    Qt.black = Qt.GlobalColor.black
    Qt.white = Qt.GlobalColor.white
    Qt.transparent = Qt.GlobalColor.transparent
    Qt.red = Qt.GlobalColor.red
    Qt.green = Qt.GlobalColor.green
    Qt.blue = Qt.GlobalColor.blue

    # Shortcut context
    Qt.ApplicationShortcut = Qt.ShortcutContext.ApplicationShortcut
    Qt.WidgetShortcut = Qt.ShortcutContext.WidgetShortcut
    Qt.WindowShortcut = Qt.ShortcutContext.WindowShortcut

    # Orientation
    Qt.Horizontal = Qt.Orientation.Horizontal
    Qt.Vertical = Qt.Orientation.Vertical

    # Item data roles
    Qt.DisplayRole = Qt.ItemDataRole.DisplayRole
    Qt.UserRole = Qt.ItemDataRole.UserRole
    Qt.DecorationRole = Qt.ItemDataRole.DecorationRole

    # Sort order
    Qt.AscendingOrder = Qt.SortOrder.AscendingOrder
    Qt.DescendingOrder = Qt.SortOrder.DescendingOrder

    # Context menu policy
    Qt.CustomContextMenu = Qt.ContextMenuPolicy.CustomContextMenu

    # Focus policy
    Qt.NoFocus = Qt.FocusPolicy.NoFocus
    Qt.StrongFocus = Qt.FocusPolicy.StrongFocus
    Qt.ClickFocus = Qt.FocusPolicy.ClickFocus
    Qt.TabFocus = Qt.FocusPolicy.TabFocus
    Qt.WheelFocus = Qt.FocusPolicy.WheelFocus

    # Pen style
    Qt.NoPen = Qt.PenStyle.NoPen
    Qt.SolidLine = Qt.PenStyle.SolidLine
    Qt.DashLine = Qt.PenStyle.DashLine
    Qt.DotLine = Qt.PenStyle.DotLine

    # Brush style
    Qt.NoBrush = Qt.BrushStyle.NoBrush
    Qt.SolidPattern = Qt.BrushStyle.SolidPattern

    # Text interaction
    Qt.TextSelectableByMouse = Qt.TextInteractionFlag.TextSelectableByMouse

    # ------------------------------------------------------------------
    # Patch QEvent type aliases
    # ------------------------------------------------------------------
    QEvent.KeyPress = QEvent.Type.KeyPress
    QEvent.KeyRelease = QEvent.Type.KeyRelease
    QEvent.MouseButtonPress = QEvent.Type.MouseButtonPress
    QEvent.MouseButtonRelease = QEvent.Type.MouseButtonRelease
    QEvent.MouseButtonDblClick = QEvent.Type.MouseButtonDblClick
    QEvent.MouseMove = QEvent.Type.MouseMove
    QEvent.Move = QEvent.Type.Move
    QEvent.Resize = QEvent.Type.Resize
    QEvent.WindowActivate = QEvent.Type.WindowActivate
    QEvent.WindowDeactivate = QEvent.Type.WindowDeactivate
    QEvent.Show = QEvent.Type.Show
    QEvent.Hide = QEvent.Type.Hide
    QEvent.Enter = QEvent.Type.Enter
    QEvent.Leave = QEvent.Type.Leave
    QEvent.FocusIn = QEvent.Type.FocusIn
    QEvent.FocusOut = QEvent.Type.FocusOut
    QEvent.Wheel = QEvent.Type.Wheel
    QEvent.Paint = QEvent.Type.Paint
    QEvent.Close = QEvent.Type.Close
    QEvent.ContextMenu = QEvent.Type.ContextMenu
    QEvent.DragEnter = QEvent.Type.DragEnter
    QEvent.DragMove = QEvent.Type.DragMove
    QEvent.Drop = QEvent.Type.Drop

    # ------------------------------------------------------------------
    # Patch widget-class enum aliases
    # ------------------------------------------------------------------
    QPalette.Window = QPalette.ColorRole.Window
    QPalette.WindowText = QPalette.ColorRole.WindowText
    QPalette.Base = QPalette.ColorRole.Base
    QPalette.AlternateBase = QPalette.ColorRole.AlternateBase
    QPalette.Text = QPalette.ColorRole.Text
    QPalette.Button = QPalette.ColorRole.Button
    QPalette.ButtonText = QPalette.ColorRole.ButtonText
    QPalette.Highlight = QPalette.ColorRole.Highlight
    QPalette.HighlightedText = QPalette.ColorRole.HighlightedText

    QFrame.VLine = QFrame.Shape.VLine
    QFrame.HLine = QFrame.Shape.HLine
    QFrame.StyledPanel = QFrame.Shape.StyledPanel
    QFrame.Sunken = QFrame.Shadow.Sunken
    QFrame.Raised = QFrame.Shadow.Raised
    QFrame.Plain = QFrame.Shadow.Plain
    QFrame.NoFrame = QFrame.Shape.NoFrame
    QFrame.Box = QFrame.Shape.Box
    QFrame.Panel = QFrame.Shape.Panel

    QDialogButtonBox.Ok = QDialogButtonBox.StandardButton.Ok
    QDialogButtonBox.Cancel = QDialogButtonBox.StandardButton.Cancel
    QDialogButtonBox.Yes = QDialogButtonBox.StandardButton.Yes
    QDialogButtonBox.No = QDialogButtonBox.StandardButton.No
    QDialogButtonBox.Close = QDialogButtonBox.StandardButton.Close
    QDialogButtonBox.Save = QDialogButtonBox.StandardButton.Save

    QHeaderView.Stretch = QHeaderView.ResizeMode.Stretch
    QHeaderView.ResizeToContents = QHeaderView.ResizeMode.ResizeToContents
    QHeaderView.Fixed = QHeaderView.ResizeMode.Fixed
    QHeaderView.Interactive = QHeaderView.ResizeMode.Interactive

    QSizePolicy.Expanding = QSizePolicy.Policy.Expanding
    QSizePolicy.Fixed = QSizePolicy.Policy.Fixed
    QSizePolicy.Preferred = QSizePolicy.Policy.Preferred
    QSizePolicy.Minimum = QSizePolicy.Policy.Minimum
    QSizePolicy.Maximum = QSizePolicy.Policy.Maximum
    QSizePolicy.MinimumExpanding = QSizePolicy.Policy.MinimumExpanding

    QAbstractItemView.SelectRows = QAbstractItemView.SelectionBehavior.SelectRows
    QAbstractItemView.SingleSelection = QAbstractItemView.SelectionMode.SingleSelection
    QAbstractItemView.ExtendedSelection = (
        QAbstractItemView.SelectionMode.ExtendedSelection
    )

    # QListWidget inherits these from QListView; the nested enum classes carry
    # over through the MRO so no separate QListView import is needed here.
    QListWidget.IconMode = QListWidget.ViewMode.IconMode
    QListWidget.ListMode = QListWidget.ViewMode.ListMode
    QListWidget.Adjust = QListWidget.ResizeMode.Adjust
    QListWidget.Static = QListWidget.Movement.Static

    QDialog.Accepted = QDialog.DialogCode.Accepted
    QDialog.Rejected = QDialog.DialogCode.Rejected

    # ------------------------------------------------------------------
    # QMouseEvent.globalPos() removed in Qt6 窶・patch it back
    # ------------------------------------------------------------------
    QMouseEvent.globalPos = lambda self: self.globalPosition().toPoint()
