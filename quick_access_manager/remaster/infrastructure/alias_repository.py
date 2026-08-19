"""Repository for the shared Alias Config: custom name/color/icon per Krita action or docker."""

import os

from .json_cache import read_json, write_json
from .paths import get_remaster_config_dir

ALIAS_CONFIG_FILE = "alias_config.json"


def get_alias_config_path():
    return os.path.join(get_remaster_config_dir(), ALIAS_CONFIG_FILE)


class AliasRepository:
    """Loads/saves the shared alias config (actions + dockers) as plain dicts."""

    def load(self):
        path = get_alias_config_path()
        if os.path.exists(path):
            try:
                data = read_json(path, default={}) or {}
                return {
                    "actions": data.get("actions", {}),
                    "dockers": data.get("dockers", {}),
                }
            except Exception:
                pass
        return {"actions": {}, "dockers": {}}

    def save(self, data):
        write_json(get_alias_config_path(), data, indent=4)
