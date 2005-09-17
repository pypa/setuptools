#!python
"""\

Easy Install
------------

A tool for doing automatic download/extract/build of distutils-based Python
packages.  For detailed documentation, see the accompanying EasyInstall.txt
file, or visit the `EasyInstall home page`__.

__ http://peak.telecommunity.com/DevCenter/EasyInstall
"""

import sys
from setuptools.command.easy_install import *

if __name__ == '__main__':
    print >>sys.stderr, "NOTE: python -m easy_install is deprecated."
    print >>sys.stderr, "Please use the 'easy_install' command instead."
    print >>sys.stderr
    main(sys.argv[1:])

