#!/usr/bin/env python

import os
import sys
import textwrap

import setuptools
from setuptools.command.install import install

here = os.path.dirname(__file__)


package_data = dict(
    setuptools=['script (dev).tmpl', 'script.tmpl', 'site-patch.py'],
)

force_windows_specific_files = os.environ.get(
    "SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES", "1"
).lower() not in ("", "0", "false", "no")

include_windows_files = sys.platform == 'win32' or force_windows_specific_files

if include_windows_files:
    package_data.setdefault('setuptools', []).extend(['*.exe'])
    package_data.setdefault('setuptools.command', []).extend(['*.xml'])


def pypi_link(pkg_filename):
    """
    Given the filename, including md5 fragment, construct the
    dependency link for PyPI.
    """
    root = 'https://files.pythonhosted.org/packages/source'
    name, sep, rest = pkg_filename.partition('-')
    parts = root, name[0], name, pkg_filename
    return '/'.join(parts)


class install_with_pth(install):
    """
    Custom install command to install a .pth file for distutils patching.

    This hack is necessary because there's no standard way to install behavior
    on startup (and it's debatable if there should be one). This hack (ab)uses
    the `extra_path` behavior in Setuptools to install a `.pth` file with
    implicit behavior on startup to give higher precedence to the local version
    of `distutils` over the version from the standard library.

    Please do not replicate this behavior.
    """

    _pth_name = 'distutils-precedence'
    _pth_contents = (
        textwrap.dedent(
            """
        import os
        var = 'SETUPTOOLS_USE_DISTUTILS'
        enabled = os.environ.get(var, 'local') == 'local'
        enabled and __import__('_distutils_hack').add_shim()
        """
        )
        .lstrip()
        .replace('\n', '; ')
    )

    def initialize_options(self):
        install.initialize_options(self)
        self.extra_path = self._pth_name, self._pth_contents

    def finalize_options(self):
        install.finalize_options(self)
        self._restore_install_lib()

    def _restore_install_lib(self):
        """
        Undo secondary effect of `extra_path` adding to `install_lib`
        """
        suffix = os.path.relpath(self.install_lib, self.install_libbase)

        if suffix.strip() == self._pth_contents.strip():
            self.install_lib = self.install_libbase


setup_params = dict(
    cmdclass={'install': install_with_pth},
    package_data=package_data,
)

if __name__ == '__main__':
    # allow setup.py to run from another directory
    # TODO: Use a proper conditional statement here
    here and os.chdir(here)  # type: ignore[func-returns-value]
    dist = setuptools.setup(**setup_params)
