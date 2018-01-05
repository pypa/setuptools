"""distutils

The main package for the Python Module Distribution Utilities.  Normally
used from a setup script as

   from distutils.core import setup

   setup (...)
"""

import sys
import os

from os.path import abspath, normcase, dirname, basename

if sys.version_info < (3, 6):
    __path__ = __import__('pkgutil').extend_path(__path__, __name__)
    __path__ = (p for p in __path__ if normcase(abspath(p)) != normcase(abspath(dirname(__file__))))
    __path__ = [p for p in __path__ if basename(dirname(abspath(p))) not in ('site-packages', 'dist-packages')]
else:
    __version__ = sys.version[:sys.version.index(' ')]
