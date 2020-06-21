"""
Ensure that the local copy of distutils is preferred over stdlib.

See https://github.com/pypa/setuptools/issues/417#issuecomment-392298401
for more motivation.
"""

import sys
import re
import importlib
import contextlib
import warnings
from os.path import dirname


@contextlib.contextmanager
def patch_sys_path():
    orig = sys.path[:]
    sys.path[:] = [dirname(dirname(__file__))]
    try:
        yield
    finally:
        sys.path[:] = orig


def clear_distutils():
    if 'distutils' not in sys.modules:
        return
    warnings.warn("Setuptools is replacing distutils")
    mods = [name for name in sys.modules if re.match(r'distutils\b', name)]
    for name in mods:
        del sys.modules[name]


def ensure_local_distutils():
    clear_distutils()
    with patch_sys_path():
        importlib.import_module('distutils')
        assert sys.modules['distutils'].local


ensure_local_distutils()
