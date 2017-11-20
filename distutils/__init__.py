"""distutils

The main package for the Python Module Distribution Utilities.  Normally
used from a setup script as

   from distutils.core import setup

   setup (...)
"""

import sys
import os

if sys.version_info < (3, 6):
    __path__ = __import__('pkgutil').extend_path(__path__, __name__)
    __path__ = [p for p in __path__ if os.path.normpath(p) != os.path.dirname(__file__)]

    raise Exception(__path__)
else:
    __version__ = sys.version[:sys.version.index(' ')]
