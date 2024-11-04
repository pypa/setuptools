import importlib.resources as resources  # noqa: F401
import sys

if sys.version_info < (3, 10):
    import importlib_metadata as metadata  # pragma: no cover
else:
    import importlib.metadata as metadata  # noqa: F401
