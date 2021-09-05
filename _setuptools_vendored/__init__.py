"""
Ensure Setuptools dependencies are present.
"""
import sys
import pathlib
import importlib

try:
    # roughly check that dependencies are present
    for name in 'packaging appdirs pyparsing ordered_set more_itertools'.split():
        importlib.import_module(name)
except ImportError:
    # if any dependendencies appear to be missing, include vendored
    sys.path.append(str(pathlib.Path(__file__).parent))
