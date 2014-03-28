#!/usr/bin/env python
"""Distutils setup file, used to install or test 'setuptools'"""
import io
import os
import sys
import textwrap
import contextlib

# Allow to run setup.py from another directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

src_root = None

from distutils.util import convert_path

command_ns = {}
init_path = convert_path('setuptools/command/__init__.py')
with open(init_path) as init_file:
    exec(init_file.read(), command_ns)

SETUP_COMMANDS = command_ns['__all__']

main_ns = {}
ver_path = convert_path('setuptools/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

import setuptools
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.test import test as _test

scripts = []

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
    yield ("easy_install-{shortver} = setuptools.command.easy_install:main"
        .format(shortver=sys.version[:3]))

console_scripts = list(_gen_console_scripts())


# specific command that is used to generate windows .exe files
class build_py(_build_py):
    def build_package_data(self):
        """Copy data files into build directory"""
        for package, src_dir, build_dir, filenames in self.data_files:
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                srcfile = os.path.join(src_dir, filename)
                outf, copied = self.copy_file(srcfile, target)
                srcfile = os.path.abspath(srcfile)

class test(_test):
    """Specific test class to avoid rewriting the entry_points.txt"""
    def run(self):
        with self._save_entry_points():
            _test.run(self)

    @contextlib.contextmanager
    def _save_entry_points(self):
        entry_points = os.path.join('setuptools.egg-info', 'entry_points.txt')

        if not os.path.exists(entry_points):
            yield
            return

        # save the content
        with open(entry_points, 'rb') as f:
            ep_content = f.read()

        # run the tests
        try:
            yield
        finally:
            # restore the file
            with open(entry_points, 'wb') as f:
                f.write(ep_content)


readme_file = io.open('README.txt', encoding='utf-8')

# the release script adds hyperlinks to issues
if os.path.exists('CHANGES (links).txt'):
    changes_file = open('CHANGES (links).txt')
else:
    # but if the release script has not run, fall back to the source file
    changes_file = open('CHANGES.txt')
with readme_file:
    with changes_file:
        long_description = readme_file.read() + '\n' + changes_file.read()

package_data = {'setuptools': ['site-patch.py']}
force_windows_specific_files = (
    os.environ.get("SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES")
    not in (None, "", "0")
)
if sys.platform == 'win32' or force_windows_specific_files:
    package_data.setdefault('setuptools', []).extend(['*.exe'])
    package_data.setdefault('setuptools.command', []).extend(['*.xml'])

pytest_runner = ['pytest-runner'] if 'ptr' in sys.argv else []

setup_params = dict(
    name="setuptools",
    version=main_ns['__version__'],
    description="Easily download, build, install, upgrade, and uninstall "
                "Python packages",
    author="Python Packaging Authority",
    author_email="distutils-sig@python.org",
    license="PSF or ZPL",
    long_description = long_description,
    keywords = "CPAN PyPI distutils eggs package management",
    url = "https://pypi.python.org/pypi/setuptools",
    test_suite = 'setuptools.tests',
    src_root = src_root,
    packages = setuptools.find_packages(),
    package_data = package_data,

    py_modules = ['pkg_resources', 'easy_install'],

    zip_safe = True,

    cmdclass = {'test': test},
    entry_points = {
        "distutils.commands": [
            "%(cmd)s = setuptools.command.%(cmd)s:%(cmd)s" % locals()
            for cmd in SETUP_COMMANDS
        ],
        "distutils.setup_keywords": [
            "eager_resources        = setuptools.dist:assert_string_list",
            "namespace_packages     = setuptools.dist:check_nsp",
            "extras_require         = setuptools.dist:check_extras",
            "install_requires       = setuptools.dist:check_requirements",
            "tests_require          = setuptools.dist:check_requirements",
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
            "namespace_packages.txt = setuptools.command.egg_info:overwrite_arg",
            "top_level.txt = setuptools.command.egg_info:write_toplevel_names",
            "depends.txt = setuptools.command.egg_info:warn_depends_obsolete",
            "dependency_links.txt = setuptools.command.egg_info:overwrite_arg",
        ],
        "console_scripts": console_scripts,

        "setuptools.file_finders":
            ["svn_cvs = setuptools.command.sdist:_default_revctrl"],

        "setuptools.installation":
            ['eggsecutable = setuptools.command.easy_install:bootstrap'],
    },


    classifiers = textwrap.dedent("""
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        License :: OSI Approved :: Python Software Foundation License
        License :: OSI Approved :: Zope Public License
        Operating System :: OS Independent
        Programming Language :: Python :: 2.6
        Programming Language :: Python :: 2.7
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.1
        Programming Language :: Python :: 3.2
        Programming Language :: Python :: 3.3
        Programming Language :: Python :: 3.4
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: System :: Archiving :: Packaging
        Topic :: System :: Systems Administration
        Topic :: Utilities
        """).strip().splitlines(),
    extras_require = {
        "ssl:sys_platform=='win32'": "wincertstore==0.2",
        "certs": "certifi==1.0.1",
    },
    dependency_links = [
        'https://pypi.python.org/packages/source/c/certifi/certifi-1.0.1.tar.gz#md5=45f5cb94b8af9e1df0f9450a8f61b790',
        'https://pypi.python.org/packages/source/w/wincertstore/wincertstore-0.2.zip#md5=ae728f2f007185648d0c7a8679b361e2',
    ],
    scripts = [],
    tests_require = [
        'setuptools[ssl]',
        'pytest',
    ],
    setup_requires = [
    ] + pytest_runner,
)

if __name__ == '__main__':
    dist = setuptools.setup(**setup_params)
