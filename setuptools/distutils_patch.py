"""
Ensure that the local copy of distutils is preferred over stdlib.

See https://github.com/pypa/setuptools/issues/417#issuecomment-392298401
for more motivation.
"""

import sys
import re
import os
import importlib
import warnings


def clear_distutils():
    if 'distutils' not in sys.modules:
        return
    warnings.warn("Setuptools is replacing distutils")
    mods = [name for name in sys.modules if re.match(r'distutils\b', name)]
    for name in mods:
        del sys.modules[name]


def enabled():
    """
    Allow selection of distutils by environment variable.
    """
    which = os.environ.get('SETUPTOOLS_USE_DISTUTILS', 'stdlib')
    return which == 'local'


def ensure_local_distutils():
    clear_distutils()
    distutils = importlib.import_module('setuptools._distutils')
    distutils.__name__ = 'distutils'
    sys.modules['distutils'] = distutils

    # sanity check that submodules load as expected
    core = importlib.import_module('distutils.core')
    assert '_distutils' in core.__file__, core.__file__


if enabled():
    ensure_local_distutils()
