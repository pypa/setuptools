"""Automatic discovery for Python modules and packages for inclusion in the
distribution.
"""

import os
from fnmatch import fnmatchcase

import _distutils_hack.override  # noqa: F401

from distutils.util import convert_path


class PackageFinder:
    """
    Generate a list of all Python packages found within a directory
    """

    @classmethod
    def find(cls, where='.', exclude=(), include=('*',)):
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

        return list(
            cls._find_packages_iter(
                convert_path(where),
                cls._build_filter('ez_setup', '*__pycache__', *exclude),
                cls._build_filter(*include),
            )
        )

    @classmethod
    def _find_packages_iter(cls, where, exclude, include):
        """
        All the packages found in 'where' that pass the 'include' filter, but
        not the 'exclude' filter.
        """
        for root, dirs, files in os.walk(where, followlinks=True):
            # Copy dirs to iterate over it, then empty dirs.
            all_dirs = dirs[:]
            dirs[:] = []

            for dir in all_dirs:
                full_path = os.path.join(root, dir)
                rel_path = os.path.relpath(full_path, where)
                package = rel_path.replace(os.path.sep, '.')

                # Skip directory trees that are not valid packages
                if '.' in dir or not cls._looks_like_package(full_path):
                    continue

                # Should this package be included?
                if include(package) and not exclude(package):
                    yield package

                # Keep searching subdirectories, as there may be more packages
                # down there, even if the parent was excluded.
                dirs.append(dir)

    @staticmethod
    def _looks_like_package(path):
        """Does a directory look like a package?"""
        return os.path.isfile(os.path.join(path, '__init__.py'))

    @staticmethod
    def _build_filter(*patterns):
        """
        Given a list of patterns, return a callable that will be true only if
        the input matches at least one of the patterns.
        """
        return lambda name: any(fnmatchcase(name, pat=pat) for pat in patterns)


class PEP420PackageFinder(PackageFinder):
    @staticmethod
    def _looks_like_package(path):
        return True
