"""
Setuptools is released using 'jaraco.packaging.release'. To make a release,
install jaraco.packaging and run 'python -m jaraco.packaging.release'
"""

import os

import pkg_resources

pkg_resources.require('jaraco.packaging>=2.0')
pkg_resources.require('wheel')

files_with_versions = 'setuptools/version.py',

# bdist_wheel must be included or pip will break
dist_commands = 'sdist', 'bdist_wheel'

test_info = "Travis-CI tests: http://travis-ci.org/#!/jaraco/setuptools"

os.environ["SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES"] = "1"
