"""Extensions to the 'distutils' for large or complex distributions"""

import os
import functools
import distutils.core
import distutils.filelist
from distutils.util import convert_path
from fnmatch import fnmatchcase

from setuptools.extern.six.moves import filter, map

import setuptools.version
from setuptools.extension import Extension
from setuptools.dist import Distribution, Feature
from setuptools.depends import Require
from . import monkey

__all__ = [
    'setup', 'Distribution', 'Feature', 'Command', 'Extension', 'Require',
    'find_packages',
]

__version__ = setuptools.version.__version__

bootstrap_install_from = None

# If we run 2to3 on .py files, should we also convert docstrings?
# Default: yes; assume that we can detect doctests reliably
run_2to3_on_doctests = True
# Standard package names for fixer packages
lib2to3_fixer_packages = ['lib2to3.fixes']


def find_packages(where='.', exclude=(), include=('*',)):
    """Return a list all Python packages found within directory 'where'

    'where' is the root directory which will be searched for packages.  It
    should be supplied as a "cross-platform" (i.e. URL-style) path; it will
    be converted to the appropriate local path syntax.

    'exclude' is a sequence of package names to exclude; '*' can be used
    as a wildcard in the names, such that 'foo.*' will exclude all
    subpackages of 'foo' (but not 'foo' itself).

    'include' is a sequence of package names to include.  If it's
    specified, only the named packages will be included.  If it's not
    specified, all found packages will be included.  'include' can contain
    shell style wildcard patterns just like 'exclude'.
    """
    def build_filter(*patterns):
        """
        Given a list of patterns, return a callable that will be true only if
        the input matches at least one of the patterns.
        """
        return lambda name: any(fnmatchcase(name, pat=pat) for pat in patterns)

    def looks_like_package(path):
        """Does a directory look like a package?"""
        return os.path.isfile(os.path.join(path, '__init__.py'))

    excluded = build_filter('ez_setup', '*__pycache__', *exclude)
    included = build_filter(*include)
    packages = []
    for root, dirs, files in os.walk(convert_path(where), followlinks=True):
        # Copy dirs to iterate over it, then empty dirs.
        all_dirs = dirs[:]
        dirs[:] = []

        for dirname in all_dirs:
            full_path = os.path.join(root, dirname)
            rel_path = os.path.relpath(full_path, where)
            package = rel_path.replace(os.path.sep, '.')

            # Skip directory trees that are not valid packages
            if '.' in dirname or not looks_like_package(full_path):
                continue

            # Should this package be included?
            if included(package) and not excluded(package):
                packages.append(package)

            # Keep searching subdirectories, as there may be more packages
            # down there, even if the parent was excluded.
            dirs.append(dirname)

    return packages

setup = distutils.core.setup

_Command = monkey.get_unpatched(distutils.core.Command)


class Command(_Command):
    __doc__ = _Command.__doc__

    command_consumes_arguments = False

    def __init__(self, dist, **kw):
        """
        Construct the command for dist, updating
        vars(self) with any keyword parameters.
        """
        _Command.__init__(self, dist)
        vars(self).update(kw)

    def reinitialize_command(self, command, reinit_subcommands=0, **kw):
        cmd = _Command.reinitialize_command(self, command, reinit_subcommands)
        vars(cmd).update(kw)
        return cmd


def _find_all_simple(path):
    """
    Find all files under 'path'
    """
    results = (
        os.path.join(base, file)
        for base, dirs, files in os.walk(path, followlinks=True)
        for file in files
    )
    return filter(os.path.isfile, results)


def findall(dir=os.curdir):
    """
    Find all files under 'dir' and return the list of full filenames.
    Unless dir is '.', return full filenames with dir prepended.
    """
    files = _find_all_simple(dir)
    if dir == os.curdir:
        make_rel = functools.partial(os.path.relpath, start=dir)
        files = map(make_rel, files)
    return list(files)


monkey.patch_all()
