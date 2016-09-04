"""
Monkey patching of distutils.
"""

import sys
import distutils.filelist

import setuptools


__all__ = []
"everything is private"


def get_unpatched(cls):
    """Protect against re-patching the distutils if reloaded

    Also ensures that no other distutils extension monkeypatched the distutils
    first.
    """
    while cls.__module__.startswith('setuptools'):
        cls, = cls.__bases__
    if not cls.__module__.startswith('distutils'):
        raise AssertionError(
            "distutils has already been patched by %r" % cls
        )
    return cls


def patch_all():
    # we can't patch distutils.cmd, alas
    distutils.core.Command = setuptools.Command

    has_issue_12885 = (
        sys.version_info < (3, 4, 6)
        or
        (3, 5) < sys.version_info <= (3, 5, 3)
        or
        (3, 6) < sys.version_info
    )

    if has_issue_12885:
        # fix findall bug in distutils (http://bugs.python.org/issue12885)
        distutils.filelist.findall = setuptools.findall

    needs_warehouse = (
        sys.version_info < (2, 7, 13)
        or
        (3, 0) < sys.version_info < (3, 3, 7)
        or
        (3, 4) < sys.version_info < (3, 4, 6)
        or
        (3, 5) < sys.version_info <= (3, 5, 3)
        or
        (3, 6) < sys.version_info
    )

    if needs_warehouse:
        warehouse = 'https://upload.pypi.org/legacy/'
        distutils.config.PyPIRCCommand.DEFAULT_REPOSITORY = warehouse
