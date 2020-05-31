"""
Ensure that the local copy of distutils is preferred over stdlib.

See https://github.com/pypa/setuptools/issues/417#issuecomment-392298401
for more motivation.
"""

import sys
import importlib
import contextlib
from os.path import dirname


@contextlib.contextmanager
def patch_sys_path():
    orig = sys.path[:]
    sys.path[:] = [dirname(dirname(__file__))]
    try:
        yield
    finally:
        sys.path[:] = orig


def ensure_local_distutils():
    if 'distutils' in sys.path:
        raise RuntimeError("Distutils must not be imported before setuptools")
    with patch_sys_path():
        importlib.import_module('distutils')


ensure_local_distutils()
