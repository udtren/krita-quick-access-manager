"""mtime-validated JSON cache shared by the config repositories.

Every settings getter in the plugin re-reads its JSON file, and some of them run
per palette item or per key press. Parsing is cheap but the open/read/decode
round trip is not, so the parsed data is kept in memory and revalidated with a
stat() call. A file edited outside the plugin is picked up on the next read.
"""

import copy
import json
import os

# {path: (mtime_ns, size, parsed_data)}
_cache = {}


def _stamp(path):
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def read_json(path, default=None):
    """Return the parsed contents of `path`, or a deep copy of `default`.

    The result is always a private copy, so callers may mutate it freely
    without corrupting the cache.
    """
    stamp = _stamp(path)
    if stamp is None:
        _cache.pop(path, None)
        return copy.deepcopy(default) if default is not None else None

    cached = _cache.get(path)
    if cached is not None and cached[0] == stamp:
        return copy.deepcopy(cached[1])

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        _cache.pop(path, None)
        raise

    _cache[path] = (stamp, data)
    return copy.deepcopy(data)


def write_json(path, data, indent=2):
    """Write `data` to `path` and refresh the cache entry from what was written."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=indent, ensure_ascii=False)
    stamp = _stamp(path)
    if stamp is not None:
        _cache[path] = (stamp, copy.deepcopy(data))
    else:
        _cache.pop(path, None)


def invalidate(path=None):
    """Drop one cached file, or the whole cache when `path` is None."""
    if path is None:
        _cache.clear()
    else:
        _cache.pop(path, None)
