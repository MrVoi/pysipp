"""
`pluggy` plugin and hook management
"""
import pluggy
import contextlib
from . import hookspec

hookimpl = pluggy.HookimplMarker("pysipp")
mng = pluggy.PluginManager("pysipp", implprefix="pysipp")
mng.add_hookspecs(hookspec)


@contextlib.contextmanager
def register(plugins):
    """Temporarily register plugins"""
    try:
        if any(plugins):
            for p in plugins:
                mng.register(p)
        yield
    finally:
        if any(plugins):
            for p in plugins:
                mng.unregister(p)
