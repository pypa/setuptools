#!/usr/bin/env python

import os
import sys
import textwrap

import setuptools
from setuptools.command.install import install

here = os.path.dirname(__file__)


def require_metadata():
    "Prevent improper installs without necessary metadata. See #659"
    egg_info_dir = os.path.join(here, 'setuptools.egg-info')
    if not os.path.exists(egg_info_dir):
        msg = (
            "Cannot build setuptools without metadata. "
            "Run `bootstrap.py`."
        )
        raise RuntimeError(msg)


def read_commands():
    command_ns = {}
    cmd_module_path = 'setuptools/command/__init__.py'
    init_path = os.path.join(here, cmd_module_path)
    with open(init_path) as init_file:
        exec(init_file.read(), command_ns)
    return command_ns['__all__']


def _gen_console_scripts():
    yield "easy_install = setuptools.command.easy_install:main"

    # Gentoo distributions manage the python-version-specific scripts
    # themselves, so those platforms define an environment variable to
    # suppress the creation of the version-specific scripts.
    var_names = (
        'SETUPTOOLS_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT',
        'DISTRIBUTE_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT',
    )
    if any(os.environ.get(var) not in (None, "", "0") for var in var_names):
        return
    tmpl = "easy_install-{shortver} = setuptools.command.easy_install:main"
    yield tmpl.format(shortver='{}.{}'.format(*sys.version_info))


package_data = dict(
    setuptools=['script (dev).tmpl', 'script.tmpl', 'site-patch.py'],
)

force_windows_specific_files = (
    os.environ.get("SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES", "1").lower()
    not in ("", "0", "false", "no")
)

include_windows_files = (
    sys.platform == 'win32' or
    os.name == 'java' and os._name == 'nt' or
    force_windows_specific_files
)

if include_windows_files:
    package_data.setdefault('setuptools', []).extend(['*.exe'])
    package_data.setdefault('setuptools.command', []).extend(['*.xml'])

needs_wheel = set(['release', 'bdist_wheel']).intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []


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
    _pth_contents = textwrap.dedent("""
        import os
        var = 'SETUPTOOLS_USE_DISTUTILS'
        enabled = os.environ.get(var, 'stdlib') == 'local'
        enabled and __import__('_distutils_hack').add_shim()
        """).lstrip().replace('\n', '; ')

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
    src_root=None,
    cmdclass={'install': install_with_pth},
    package_data=package_data,
    entry_points={
        "distutils.commands": [
            "%(cmd)s = setuptools.command.%(cmd)s:%(cmd)s" % locals()
            for cmd in read_commands()
        ],
        "setuptools.finalize_distribution_options": [
            "parent_finalize = setuptools.dist:_Distribution.finalize_options",
            "keywords = setuptools.dist:Distribution._finalize_setup_keywords",
            "2to3_doctests = "
            "setuptools.dist:Distribution._finalize_2to3_doctests",
        ],
        "distutils.setup_keywords": [
            "eager_resources        = setuptools.dist:assert_string_list",
            "namespace_packages     = setuptools.dist:check_nsp",
            "extras_require         = setuptools.dist:check_extras",
            "install_requires       = setuptools.dist:check_requirements",
            "tests_require          = setuptools.dist:check_requirements",
            "setup_requires         = setuptools.dist:check_requirements",
            "python_requires        = setuptools.dist:check_specifier",
            "entry_points           = setuptools.dist:check_entry_points",
            "test_suite             = setuptools.dist:check_test_suite",
            "zip_safe               = setuptools.dist:assert_bool",
            "package_data           = setuptools.dist:check_package_data",
            "exclude_package_data   = setuptools.dist:check_package_data",
            "include_package_data   = setuptools.dist:assert_bool",
            "packages               = setuptools.dist:check_packages",
            "dependency_links       = setuptools.dist:assert_string_list",
            "test_loader            = setuptools.dist:check_importable",
            "test_runner            = setuptools.dist:check_importable",
            "use_2to3               = setuptools.dist:assert_bool",
            "convert_2to3_doctests  = setuptools.dist:assert_string_list",
            "use_2to3_fixers        = setuptools.dist:assert_string_list",
            "use_2to3_exclude_fixers = setuptools.dist:assert_string_list",
        ],
        "egg_info.writers": [
            "PKG-INFO = setuptools.command.egg_info:write_pkg_info",
            "requires.txt = setuptools.command.egg_info:write_requirements",
            "entry_points.txt = setuptools.command.egg_info:write_entries",
            "eager_resources.txt = setuptools.command.egg_info:overwrite_arg",
            (
                "namespace_packages.txt = "
                "setuptools.command.egg_info:overwrite_arg"
            ),
            "top_level.txt = setuptools.command.egg_info:write_toplevel_names",
            "depends.txt = setuptools.command.egg_info:warn_depends_obsolete",
            "dependency_links.txt = setuptools.command.egg_info:overwrite_arg",
        ],
        "console_scripts": list(_gen_console_scripts()),
        "setuptools.installation":
            ['eggsecutable = setuptools.command.easy_install:bootstrap'],
    },
    dependency_links=[
        pypi_link(
            'certifi-2016.9.26.tar.gz#md5=baa81e951a29958563689d868ef1064d',
        ),
        pypi_link(
            'wincertstore-0.2.zip#md5=ae728f2f007185648d0c7a8679b361e2',
        ),
    ],
    setup_requires=[
    ] + wheel,
)

if __name__ == '__main__':
    # allow setup.py to run from another directory
    here and os.chdir(here)
    require_metadata()
    dist = setuptools.setup(**setup_params)
