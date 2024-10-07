"""Convenience layer on top of stdlib's shutil and os"""

import os
import stat
from typing import Callable, TypeVar

from .compat import py311

from distutils import log

try:
    from os import chmod
except ImportError:
    # Jython compatibility
    def chmod(*args: object, **kwargs: object) -> None:  # type: ignore[misc] # Mypy reuses the imported definition anyway
        pass


_T = TypeVar("_T")


def attempt_chmod_verbose(path, mode):
    log.debug("changing mode of %s to %o", path, mode)
    try:
        chmod(path, mode)
    except OSError as e:
        log.debug("chmod failed: %s", e)


# Must match shutil._OnExcCallback
def _auto_chmod(func: Callable[..., _T], arg: str, exc: BaseException) -> _T:
    """shutils onexc callback to automatically call chmod for certain functions."""
    # Only retry for scenarios known to have an issue
    if func in [os.unlink, os.remove] and os.name == 'nt':
        attempt_chmod_verbose(arg, stat.S_IWRITE)
        return func(arg)
    raise exc


def rmtree(path, ignore_errors=False, onexc=_auto_chmod):
    return py311.shutil_rmtree(path, ignore_errors, onexc)


def rmdir(path, **opts):
    if os.path.isdir(path):
        rmtree(path, **opts)
