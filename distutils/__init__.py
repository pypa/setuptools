"""distutils

The main package for the Python Module Distribution Utilities.  Normally
used from a setup script as

   from distutils.core import setup

   setup (...)
"""

import sys

if sys.version_info < (3, 6):
    __path__ = __import__('pkgutil').extend_path([], __name__)
else:
    __version__ = sys.version[:sys.version.index(' ')]
