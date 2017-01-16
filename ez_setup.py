#!/usr/bin/env python

"""
Setuptools bootstrapping installer, reliant on pip and providing
nominal compatibility with the prior interface.

Maintained at https://github.com/pypa/setuptools/tree/bootstrap.

Don't use this script. Instead, just invoke pip commands to install
or update setuptools.
"""

import sys
import warnings


def use_setuptools(version=None, **kwargs):
    """
    A minimally-compatible version of ez_setup.use_setuptools
    """
    if kwargs:
        msg = "ignoring arguments: {keys}".format(keys=list(kwargs.keys()))
        warnings.warn(msg)

    requirement = _requirement(version)
    _pip_install(requirement)

    # ensure that the package resolved satisfies the requirement
    __import__('pkg_resources').require(requirement)


def download_setuptools(*args, **kwargs):
    msg = (
        "download_setuptools is no longer supported; "
        "use `pip download setuptools` instead."
    )
    raise NotImplementedError(msg)


def _requirement(version):
    req = 'setuptools'
    if version:
        req += '>=' + version
    return req


def _pip_install(*args):
    args = ('install', '--upgrade') + args
    __import__('pip').main(list(args))


def _check_sys_argv():
    if not sys.argv[1:]:
        return

    msg = (
        "parameters to ez_setup are no longer supported; "
        "invoke pip directly to customize setuptools install."
    )
    raise NotImplementedError(msg)


if __name__ == '__main__':
    _check_sys_argv()
    raise SystemExit(_pip_install('setuptools'))
