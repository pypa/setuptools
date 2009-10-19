#!/usr/bin/env python
"""Distutils setup file, used to install or test 'setuptools'"""

from distutils.util import convert_path

d = {}
execfile(convert_path('setuptools/command/__init__.py'), d)

SETUP_COMMANDS = d['__all__']
VERSION = "0.6c11"

from setuptools import setup, find_packages
import sys
scripts = []

setup(
    name="setuptools",
    version=VERSION,
    description="Download, build, install, upgrade, and uninstall Python "
        "packages -- easily!",
    author="Phillip J. Eby",
    author_email="distutils-sig@python.org",
    license="PSF or ZPL",
    long_description = open('README.txt').read(),
    keywords = "CPAN PyPI distutils eggs package management",
    url = "http://pypi.python.org/pypi/setuptools",
    test_suite = 'setuptools.tests',
    packages = find_packages(),
    package_data = {'setuptools':['*.exe']},

    py_modules = ['pkg_resources', 'easy_install', 'site'],

    zip_safe = (sys.version>="2.5"),   # <2.5 needs unzipped for -m to work

    entry_points = {

        "distutils.commands" : [
            "%(cmd)s = setuptools.command.%(cmd)s:%(cmd)s" % locals()
            for cmd in SETUP_COMMANDS
        ],

        "distutils.setup_keywords": [
            "eager_resources      = setuptools.dist:assert_string_list",
            "namespace_packages   = setuptools.dist:check_nsp",
            "extras_require       = setuptools.dist:check_extras",
            "install_requires     = setuptools.dist:check_requirements",
            "tests_require        = setuptools.dist:check_requirements",
            "entry_points         = setuptools.dist:check_entry_points",
            "test_suite           = setuptools.dist:check_test_suite",
            "zip_safe             = setuptools.dist:assert_bool",
            "package_data         = setuptools.dist:check_package_data",
            "exclude_package_data = setuptools.dist:check_package_data",
            "include_package_data = setuptools.dist:assert_bool",
            "dependency_links     = setuptools.dist:assert_string_list",
            "test_loader          = setuptools.dist:check_importable",
            "packages             = setuptools.dist:check_packages",
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

        "console_scripts": [
             "easy_install = setuptools.command.easy_install:main",
             "easy_install-%s = setuptools.command.easy_install:main"
                % sys.version[:3]
        ],

        "setuptools.file_finders":
            ["svn_cvs = setuptools.command.sdist:_default_revctrl"],

        "setuptools.installation":
            ['eggsecutable = setuptools.command.easy_install:bootstrap'],
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

























