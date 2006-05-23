#!/bin/sh

# This script is for PJE's working environment only, to upload
# releases to PyPI, telecommunity, eby-sarna SVN, update local
# project checkouts, etc.
#
# If your initials aren't PJE, don't run it.  :)
#

export VERSION="0.6b2"

wpython setup.py -q source && \
cpython setup.py -q binary && \
python ez_setup.py --md5update dist/setuptools-$VERSION*-py2.?.egg && \
  scp ez_setup.py virtual-python.py t3:web/PEAK/dist/ && \
  cp ez_setup.py ~/projects/ez_setup/__init__.py && \
  svn ci -m "Update ez_setup for setuptools $VERSION" \
      ~/projects/ez_setup/__init__.py && \
  svn up ~/projects/*/ez_setup

# XXX update wiki pages from EasyInstall.txt, setuptools.txt, & 
#     pkg_resources.txt
