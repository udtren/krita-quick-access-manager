_registered_filters = []


def register_event_filter(obj):
    _registered_filters.append(obj)


def get_event_filter_count():
    return len(_registered_filters)
