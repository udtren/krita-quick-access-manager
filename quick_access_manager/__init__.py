"""Quick Access Manager Krita plugin entry point.

The remastered implementation is the active plugin namespace. The legacy
namespace remains available for reference and gradual reuse, but its dockers are
not registered by this entry point.
"""

try:
    from .remaster.plugin import *  # noqa: F401,F403
except ModuleNotFoundError as exc:
    if exc.name != "krita":
        raise
