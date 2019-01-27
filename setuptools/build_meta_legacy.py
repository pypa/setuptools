"""Compatibility backend for setuptools

This is a version of setuptools.build_meta that endeavors to maintain backwards
compatibility with pre-PEP 517 modes of invocation. It exists as a temporary
bridge between the old packaging mechanism and the new packaging mechanism,
and will eventually be removed.
"""

import sys

from setuptools.build_meta import _BuildMetaBackend
from setuptools.build_meta import SetupRequirementsError


__all__ = ['get_requires_for_build_sdist',
           'get_requires_for_build_wheel',
           'prepare_metadata_for_build_wheel',
           'build_wheel',
           'build_sdist',
           'SetupRequirementsError']


class _BuildMetaLegacyBackend(_BuildMetaBackend):
    def run_setup(self, setup_script='setup.py'):
        # In order to maintain compatibility with scripts assuming that
        # the setup.py script is in a directory on the PYTHONPATH, inject
        # '' into sys.path. (pypa/setuptools#1642)
        sys_path = list(sys.path)       # Save the old path
        if '' not in sys.path:
            sys.path.insert(0, '')

        super(_BuildMetaLegacyBackend,
              self).run_setup(setup_script=setup_script)

        sys.path = sys_path             # Restore the old path


_BACKEND = _BuildMetaLegacyBackend()

get_requires_for_build_wheel = _BACKEND.get_requires_for_build_wheel
get_requires_for_build_sdist = _BACKEND.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = _BACKEND.prepare_metadata_for_build_wheel
build_wheel = _BACKEND.build_wheel
build_sdist = _BACKEND.build_sdist
