#!/usr/bin/env python

import os
import sys
import textwrap

import setuptools

here = os.path.dirname(__file__)

package_data = {
    "": ["LICEN[CS]E*", "COPYING*", "NOTICE*", "AUTHORS*"],
    "setuptools": ['script (dev).tmpl', 'script.tmpl', 'site-patch.py'],
}

force_windows_specific_files = os.environ.get(
    "SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES", "1"
).lower() not in ("", "0", "false", "no")

include_windows_files = sys.platform == 'win32' or force_windows_specific_files

if include_windows_files:
    package_data.setdefault('setuptools', []).extend(['*.exe'])
    package_data.setdefault('setuptools.command', []).extend(['*.xml'])

setup_params = dict(
    package_data=package_data,
)

if __name__ == '__main__':
    # allow setup.py to run from another directory
    # TODO: Use a proper conditional statement here
    here and os.chdir(here)  # type: ignore[func-returns-value]
    dist = setuptools.setup(**setup_params)
