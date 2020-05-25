"""
Ensure that the local copy of distutils is preferred over stdlib.

See https://github.com/pypa/setuptools/issues/417#issuecomment-392298401
for more motivation.
"""

import sys
import importlib
from os.path import dirname


sys.path.insert(0, dirname(dirname(__file__)))
importlib.import_module('distutils')
sys.path.pop(0)
