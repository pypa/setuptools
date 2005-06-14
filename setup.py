#!/usr/bin/env python
"""Distutils setup file, used to install or test 'setuptools'"""

VERSION = "0.4a3"
from setuptools import setup, find_packages, Require

setup(
    name="setuptools",
    version=VERSION,

    description="Download, build, install, upgrade, and uninstall Python "
        "packages -- easily!",

    author="Phillip J. Eby",
    author_email="peak@eby-sarna.com",
    license="PSF or ZPL",
    long_description =
        "Setuptools enhances the distutils with support for Python Eggs "
        "(http://peak.telecommunity.com/DevCenter/PythonEggs) and more.  Its "
        "'EasyInstall' tool "
        "(http://peak.telecommunity.com/DevCenter/EasyInstall) lets you "
        "download and install (or cleanly upgrade) Python packages on your "
        "system, from source distributions, subversion checkouts, SourceForge "
        "download mirrors, or from Python Eggs.  Been looking for a CPAN "
        "clone for Python? When combined with PyPI, this gets pretty darn "
        "close. See the home page and download page for details and docs.",

    keywords = "CPAN PyPI distutils eggs package management",
    url = "http://peak.telecommunity.com/PythonEggs",
    download_url = "http://peak.telecommunity.com/DevCenter/EasyInstall",

    test_suite = 'setuptools.tests.test_suite',
    requires = [
        Require('Distutils','1.0.3','distutils',
            "http://www.python.org/sigs/distutils-sig/"
        ),
        Require('PyUnit', None, 'unittest', "http://pyunit.sf.net/"),
    ],



    packages = find_packages(),
    py_modules = ['pkg_resources', 'easy_install'],
    scripts = ['easy_install.py'],
    extra_path = ('setuptools', 'setuptools-%s.egg' % VERSION),

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
    Topic :: Utilities
    """.splitlines() if f.strip()]
)























