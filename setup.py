#!/usr/bin/env python
"""Distutils setup file, used to install or test 'setuptools'"""

def get_description():
    # Get our long description from the documentation
    f = file('setuptools.txt')
    lines = []
    for line in f:
        if not line.strip():
            break     # skip to first blank line
    for line in f:
        if line.startswith('.. contents::'):
            break     # read to table of contents
        lines.append(line)
    f.close()
    return ''.join(lines)

VERSION = "0.6a9"
from setuptools import setup, find_packages
import sys
from setuptools.command import __all__ as SETUP_COMMANDS
scripts = []
if sys.platform != "win32":
    scripts = ["easy_install.py"]   # for backward compatibility only

setup(
    name="setuptools",
    version=VERSION,
    description="Download, build, install, upgrade, and uninstall Python "
        "packages -- easily!",
    author="Phillip J. Eby",
    author_email="peak@eby-sarna.com",
    license="PSF or ZPL",
    long_description = get_description(),
    keywords = "CPAN PyPI distutils eggs package management",
    url = "http://peak.telecommunity.com/DevCenter/setuptools",
    test_suite = 'setuptools.tests.test_suite',
    packages = find_packages(),
    include_package_data = True,
    py_modules = ['pkg_resources', 'easy_install', 'site'],

    zip_safe = False,   # We want 'python -m easy_install' to work, for now :(
    entry_points = {
        "distutils.commands" : [
            "%(cmd)s = setuptools.command.%(cmd)s:%(cmd)s" % locals()
            for cmd in SETUP_COMMANDS
        ],
        "distutils.setup_keywords": [
            "eager_resources    = setuptools.dist:assert_string_list",
            "namespace_packages = setuptools.dist:check_nsp",
            "extras_require     = setuptools.dist:check_extras",
            "install_requires   = setuptools.dist:check_install_requires",
            "entry_points       = setuptools.dist:check_entry_points",
            "test_suite         = setuptools.dist:check_test_suite",
            "zip_safe           = setuptools.dist:assert_bool",
            "include_package_data = setuptools.dist:assert_bool",
        ],
        "egg_info.writers": [
            "PKG-INFO = setuptools.command.egg_info:write_pkg_info",
            "requires.txt = setuptools.command.egg_info:write_requirements",
            "entry_points.txt = setuptools.command.egg_info:write_entries",
            "eager_resources.txt = setuptools.command.egg_info:write_arg",
            "namespace_packages.txt = setuptools.command.egg_info:write_arg",
            "top_level.txt = setuptools.command.egg_info:write_toplevel_names",
            "depends.txt = setuptools.command.egg_info:warn_depends_obsolete",
        ],
        "console_scripts":
            ["easy_install = setuptools.command.easy_install:main"],
    },
    classifiers = [f.strip() for f in """
    Development Status :: 3 - Alpha
    Intended Audience :: Developers
    License :: OSI Approved :: Python Software Foundation License
    License :: OSI Approved :: Zope Public License
    Operating System :: OS Independent
    Programming Language :: Python
    Topic :: Software Development :: Libraries :: Python Modules
    Topic :: System :: Archiving :: Packaging
    Topic :: System :: Systems Administration
    Topic :: Utilities""".splitlines() if f.strip()],
    scripts = scripts,

    # uncomment for testing
    # setup_requires = ['setuptools>=0.6a0'],
)






































