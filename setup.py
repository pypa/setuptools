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
    
VERSION = "0.5a9"

from setuptools import setup, find_packages

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
    py_modules = ['pkg_resources', 'easy_install'],
    scripts = ['easy_install.py'],
    zip_safe = True,



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




























