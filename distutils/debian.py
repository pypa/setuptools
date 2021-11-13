"""
Apply Debian-specific patches to distutils commands and sysconfig.

Extracts the customized behavior from patches as reported
in pypa/distutils#2 and applies those customizations (except
for scheme definitions) to those commands.

Call ``apply_customizations`` to have these customizations
take effect. Debian can do that from site.py or similar::

    with contextlib.suppress(ImportError):
        import distutils.debian
        distutils.debian.apply_customizations()
"""

import os
import sys

import distutils.sysconfig
import distutils.command.install as orig_install
import distutils.command.install_egg_info as orig_install_egg_info
from distutils.command.install_egg_info import (
    to_filename,
    safe_name,
    safe_version,
    )
from distutils.errors import DistutilsOptionError


class install(orig_install.install):
    user_options = list(orig_install.install.user_options) + [
        ('install-layout=', None,
         "installation layout to choose (known values: deb, unix)"),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.prefix_option = None
        self.install_layout = None

    def finalize_unix(self):
        self.prefix_option = self.prefix
        super().finalize_unix()
        if self.install_layout:
            if self.install_layout.lower() in ['deb']:
                self.select_scheme("deb_system")
            elif self.install_layout.lower() in ['unix']:
                self.select_scheme("posix_prefix")
            else:
                raise DistutilsOptionError(
                    "unknown value for --install-layout")
        elif ((self.prefix_option and
               os.path.normpath(self.prefix) != '/usr/local')
              or sys.base_prefix != sys.prefix
              or 'PYTHONUSERBASE' in os.environ
              or 'VIRTUAL_ENV' in os.environ
              or 'real_prefix' in sys.__dict__):
            self.select_scheme("posix_prefix")
        else:
            if os.path.normpath(self.prefix) == '/usr/local':
                self.prefix = self.exec_prefix = '/usr'
                self.install_base = self.install_platbase = '/usr'
            self.select_scheme("posix_local")


class install_egg_info(orig_install_egg_info.install_egg_info):
    user_options = list(orig_install_egg_info.install_egg_info.user_options) + [
        ('install-layout', None, "custom installation layout"),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.prefix_option = None
        self.install_layout = None

    def finalize_options(self):
        self.set_undefined_options('install',('install_layout','install_layout'))
        self.set_undefined_options('install',('prefix_option','prefix_option'))
        super().finalize_options()

    @property
    def basename(self):
        if self.install_layout:
            if not self.install_layout.lower() in ['deb', 'unix']:
                raise DistutilsOptionError(
                    "unknown value for --install-layout")
            no_pyver = (self.install_layout.lower() == 'deb')
        elif self.prefix_option:
            no_pyver = False
        else:
            no_pyver = True
        if no_pyver:
            basename = "%s-%s.egg-info" % (
                to_filename(safe_name(self.distribution.get_name())),
                to_filename(safe_version(self.distribution.get_version()))
                )
        else:
            basename = "%s-%s-py%d.%d.egg-info" % (
                to_filename(safe_name(self.distribution.get_name())),
                to_filename(safe_version(self.distribution.get_version())),
                *sys.version_info[:2]
            )
        return basename


def _posix_lib(standard_lib, libpython, early_prefix, prefix):
    is_default_prefix = not early_prefix or os.path.normpath(early_prefix) in ('/usr', '/usr/local')
    if standard_lib:
        return libpython
    elif (is_default_prefix and
              'PYTHONUSERBASE' not in os.environ and
              'VIRTUAL_ENV' not in os.environ and
              'real_prefix' not in sys.__dict__ and
              sys.prefix == sys.base_prefix):
            return os.path.join(prefix, "lib", "python3", "dist-packages")
    else:
        return os.path.join(libpython, "site-packages")


def apply_customizations():
    orig_install.install = install
    orig_install_egg_info.install_egg_info = install_egg_info
    distutils.sysconfig._posix_lib = _posix_lib
