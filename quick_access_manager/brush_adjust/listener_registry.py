import weakref

_adjustment_widget_ref = None


def _register_adjustment_widget(widget):
    global _adjustment_widget_ref
    _adjustment_widget_ref = weakref.ref(widget)


def _get_adjustment_widget():
    if _adjustment_widget_ref is not None:
        return _adjustment_widget_ref()
    return None


def pause_all_brush_listeners():
    widget = _get_adjustment_widget()
    if widget is not None:
        widget.pause_all_listeners()


def resume_all_brush_listeners():
    widget = _get_adjustment_widget()
    if widget is not None:
        widget.resume_all_listeners()


def toggle_all_brush_listeners():
    widget = _get_adjustment_widget()
    if widget is not None:
        widget.toggle_all_listeners()


def are_brush_listeners_paused():
    """Returns True if brush listeners are paused, False if active, None if unavailable."""
    widget = _get_adjustment_widget()
    if widget is None:
        return None
    listeners = widget._all_listeners()
    if not listeners:
        return None
    return listeners[0]._paused
