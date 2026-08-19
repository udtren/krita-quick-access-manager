"""Minimal opt-in file logger for the gesture system (no-op unless enable_debug=True)."""

import os

from ..infrastructure import get_remaster_config_dir


def write_log(log_msg, enable_debug=False):
    if not enable_debug:
        return
    log_file = os.path.join(get_remaster_config_dir(), "logs", "log.txt")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")
