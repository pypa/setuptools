"""Extensions to the 'distutils' for large or complex distributions"""

import os
import sys
import distutils.core
import distutils.filelist
from distutils.core import Command as _Command
from distutils.util import convert_path
from fnmatch import fnmatchcase

import setuptools.version
from setuptools.extension import Extension
from setuptools.dist import Distribution, Feature, _get_unpatched
from setuptools.depends import Require
from setuptools.compat import filterfalse

__all__ = [
    'setup', 'Distribution', 'Feature', 'Command', 'Extension', 'Require',
    'find_packages'
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

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.  'exclude' is a
    sequence of package names to exclude; '*' can be used as a wildcard in the
    names, such that 'foo.*' will exclude all subpackages of 'foo' (but not
    'foo' itself).

    'include' is a sequence of package names to include.  If it's specified,
    only the named packages will be included.  If it's not specified, all found
    packages will be included.  'include' can contain shell style wildcard
    patterns just like 'exclude'.

    The list of included packages is built up first and then any explicitly
    excluded packages are removed from it.
    """
    out = []
    stack=[(convert_path(where), '')]
    while stack:
        where,prefix = stack.pop(0)
        dirs = _dirs(where)
        suitable = filterfalse(lambda n: '.' in n, dirs)
        paths = (os.path.join(where, name) for name in suitable)
        packages = filter(_looks_like_package, paths)
        for path in packages:
            name = os.path.basename(path)
            pkg_name = prefix + name
            out.append(pkg_name)
            stack.append((path, pkg_name + '.'))
    includes = _build_filter(*include)
    excludes = _build_filter('ez_setup', '*__pycache__', *exclude)
    out = filter(includes, out)
    out = filterfalse(excludes, out)
    return list(out)

def _looks_like_package(path):
    return (
        os.path.isfile(os.path.join(path, '__init__.py'))
        or sys.version_info[:2] >= (3, 3)  # PEP 420
    )

def _dirs(target):
    """
    Return all directories in target
    """
    return (
        fn
        for fn in os.listdir(target)
        if os.path.isdir(os.path.join(target, fn))
    )

def _build_filter(*patterns):
    """
    Given a list of patterns, return a callable that will be true only if
    the input matches one of the patterns.
    """
    return lambda name: any(fnmatchcase(name, pat=pat) for pat in patterns)

setup = distutils.core.setup

_Command = _get_unpatched(_Command)

class Command(_Command):
    __doc__ = _Command.__doc__

    command_consumes_arguments = False

    def __init__(self, dist, **kw):
        # Add support for keyword arguments
        _Command.__init__(self,dist)
        for k,v in kw.items():
            setattr(self,k,v)

    def reinitialize_command(self, command, reinit_subcommands=0, **kw):
        cmd = _Command.reinitialize_command(self, command, reinit_subcommands)
        for k,v in kw.items():
            setattr(cmd,k,v)    # update command with keywords
        return cmd

distutils.core.Command = Command    # we can't patch distutils.cmd, alas

def findall(dir = os.curdir):
    """Find all files under 'dir' and return the list of full filenames
    (relative to 'dir').
    """
    all_files = []
    for base, dirs, files in os.walk(dir):
        if base==os.curdir or base.startswith(os.curdir+os.sep):
            base = base[2:]
        if base:
            files = [os.path.join(base, f) for f in files]
        all_files.extend(filter(os.path.isfile, files))
    return all_files

distutils.filelist.findall = findall    # fix findall bug in distutils.

# sys.dont_write_bytecode was introduced in Python 2.6.
_dont_write_bytecode = getattr(sys, 'dont_write_bytecode',
    bool(os.environ.get("PYTHONDONTWRITEBYTECODE")))
