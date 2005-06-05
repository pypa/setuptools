#!/usr/bin/env python

"""Distutils setup file, used to install or test 'setuptools'"""

from setuptools import setup, find_packages, Require
from distutils.version import LooseVersion

setup(
    name="setuptools",
    version="0.4a1",

    description="Distutils packaging and installation enhancements",
    author="Phillip J. Eby",
    author_email="peak@eby-sarna.com",
    license="PSF or ZPL",

    test_suite = 'setuptools.tests.test_suite',
    requires = [
        Require('Distutils','1.0.3','distutils',
            "http://www.python.org/sigs/distutils-sig/"
        ),
        Require('PyUnit', None, 'unittest', "http://pyunit.sf.net/"),
    ],
    packages = find_packages(),
    py_modules = ['pkg_resources', 'easy_install'],
    scripts = ['easy_install.py']
)

