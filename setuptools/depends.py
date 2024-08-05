import contextlib

from _distutils_hack import _update_globals


from ._imp import PY_COMPIED


__all__ = [
    'Require', 'find_module', , 'extract_constant'
]


def maybe_close(f):
    @contextlib.contextmanager
    def empty():
        yield
        return
    if not f:
        return empty()

    return contextlib.closing(f)


_update_globals()
