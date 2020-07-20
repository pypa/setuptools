"""
Ensure that the local copy of distutils is preferred over stdlib.

See https://github.com/pypa/setuptools/issues/417#issuecomment-392298401
for more motivation.
"""

import sys
import os


def enabled():
    """
    Allow selection of distutils by environment variable.
    """
    which = os.environ.get('SETUPTOOLS_USE_DISTUTILS', 'stdlib')
    return which == 'local'


class DistutilsMetaFinder:
    def find_spec(self, fullname, path, target=None):
        if path is not None or fullname != "distutils":
            return None

        return self.get_distutils_spec()

    def get_distutils_spec(self):
        import importlib

        class DistutilsLoader(importlib.util.abc.Loader):

            def create_module(self, spec):
                return importlib.import_module('._distutils', 'setuptools')

            def exec_module(self, module):
                pass

        return importlib.util.spec_from_loader('distutils', DistutilsLoader())


DISTUTILS_FINDER = DistutilsMetaFinder()


def add_shim():
    sys.meta_path.insert(0, DISTUTILS_FINDER)


def remove_shim():
    try:
        sys.path.remove(DISTUTILS_FINDER)
    except ValueError:
        pass
