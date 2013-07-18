#!/usr/bin/env python
"""Distutils setup file, used to install or test 'setuptools'"""
import sys
import os
import textwrap

# Allow to run setup.py from another directory.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

src_root = None

from distutils.util import convert_path

command_ns = {}
init_path = convert_path('setuptools/command/__init__.py')
init_file = open(init_path)
exec(init_file.read(), command_ns)
init_file.close()

SETUP_COMMANDS = command_ns['__all__']

main_ns = {}
init_path = convert_path('setuptools/__init__.py')
init_file = open(init_path)
exec(init_file.read(), main_ns)
init_file.close()

import setuptools
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.test import test as _test

scripts = []

console_scripts = ["easy_install = setuptools.command.easy_install:main"]

# Gentoo distributions manage the python-version-specific scripts themselves,
# so they define an environment variable to suppress the creation of the
# version-specific scripts.
if os.environ.get("SETUPTOOLS_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT") in (None, "", "0") and \
    os.environ.get("DISTRIBUTE_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT") in (None, "", "0"):
    console_scripts.append("easy_install-%s = setuptools.command.easy_install:main" % sys.version[:3])

# specific command that is used to generate windows .exe files
class build_py(_build_py):
    def build_package_data(self):
        """Copy data files into build directory"""
        lastdir = None
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
        entry_points = os.path.join('setuptools.egg-info', 'entry_points.txt')

        if not os.path.exists(entry_points):
            _test.run(self)
            return # even though _test.run will raise SystemExit

        f = open(entry_points)

        # running the test
        try:
            ep_content = f.read()
        finally:
            f.close()

        try:
            _test.run(self)
        finally:
            # restoring the file
            f = open(entry_points, 'w')
            try:
                f.write(ep_content)
            finally:
                f.close()


readme_file = open('README.txt')
# the release script adds hyperlinks to issues
if os.path.exists('CHANGES (links).txt'):
    changes_file = open('CHANGES (links).txt')
else:
    # but if the release script has not run, fall back to the source file
    changes_file = open('CHANGES.txt')
long_description = readme_file.read() + '\n' + changes_file.read()
readme_file.close()
changes_file.close()

package_data = {'setuptools': ['site-patch.py']}
if sys.platform == 'win32' or os.environ.get("SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES") not in (None, "", "0"):
    package_data.setdefault('setuptools', []).extend(['*.exe'])
    package_data.setdefault('setuptools.command', []).extend(['*.xml'])

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

    zip_safe = (sys.version>="2.5"),   # <2.5 needs unzipped for -m to work

    cmdclass = {'test': test},
    entry_points = {
        "distutils.commands" : [
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
        Programming Language :: Python :: 2.4
        Programming Language :: Python :: 2.5
        Programming Language :: Python :: 2.6
        Programming Language :: Python :: 2.7
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.1
        Programming Language :: Python :: 3.2
        Programming Language :: Python :: 3.3
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: System :: Archiving :: Packaging
        Topic :: System :: Systems Administration
        Topic :: Utilities
        """).strip().splitlines(),
    extras_require = {
        "ssl:sys_platform=='win32'": "wincertstore==0.1",
        "ssl:sys_platform=='win32' and python_version=='2.4'": "ctypes==1.0.2",
        "ssl:python_version in '2.4, 2.5'":"ssl==1.16",
        "certs": "certifi==0.0.8",
    },
    dependency_links = [
        'https://pypi.python.org/packages/source/c/certifi/certifi-0.0.8.tar.gz#md5=dc5f5e7f0b5fc08d27654b17daa6ecec',
        'https://pypi.python.org/packages/source/s/ssl/ssl-1.16.tar.gz#md5=fb12d335d56f3c8c7c1fefc1c06c4bfb',
        'https://pypi.python.org/packages/source/w/wincertstore/wincertstore-0.1.zip#md5=2f9accbebe8f7b4c06ac7aa83879b81c',
        'https://bitbucket.org/pypa/setuptools/downloads/ctypes-1.0.2.win32-py2.4.exe#md5=9092a0ad5a3d79fa2d980f1ddc5e9dbc',
        'https://bitbucket.org/pypa/setuptools/downloads/ssl-1.16-py2.4-win32.egg#md5=3cfa2c526dc66e318e8520b6f1aadce5',
        'https://bitbucket.org/pypa/setuptools/downloads/ssl-1.16-py2.5-win32.egg#md5=85ad1cda806d639743121c0bbcb5f39b',
    ],
    scripts = [],
    # tests_require = "setuptools[ssl]",
)

if __name__ == '__main__':
    dist = setuptools.setup(**setup_params)
