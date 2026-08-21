"""Focus helpers for the application-wide key event filters.

The gesture detector and the temporary-key listeners watch every key press in
the application. Without this check they also fire while the user is typing a
layer name, a filter value, or a shortcut into a dialog.
"""

from .compat import QApplication

# Matched against the Qt meta-object hierarchy, so subclasses (QSpinBox ->
# QAbstractSpinBox, Krita's own line edits, ...) are covered without importing
# every widget class.
_TEXT_INPUT_CLASSES = frozenset(
    (
        "QLineEdit",
        "QTextEdit",
        "QPlainTextEdit",
        "QAbstractSpinBox",
        "QKeySequenceEdit",
    )
)


def is_text_input_focused():
    """True when keyboard focus is inside a widget that consumes typing."""
    app = QApplication.instance()
    if app is None:
        return False
    widget = app.focusWidget()
    if widget is None:
        return False
    try:
        meta = widget.metaObject()
    except Exception:
        return False
    while meta is not None:
        if meta.className() in _TEXT_INPUT_CLASSES:
            return True
        meta = meta.superClass()
    return False
