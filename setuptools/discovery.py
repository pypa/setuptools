"""Automatic discovery for Python modules and packages for inclusion in the
distribution.

For the purposes of this module, the following nomenclature is used:

- "src-layout": a directory representing a Python project that contains a "src"
  folder. Everything under the "src" folder is meant to be included in the
  distribution when packaging the project. Example::

    .
    ├── tox.ini
    ├── pyproject.toml
    └── src/
        └── mypkg/
            ├── __init__.py
            ├── mymodule.py
            └── my_data_file.txt

- "flat-layout": a Python project that does not use "src-layout" but instead
  have a folder direct under the project root for each package::

    .
    ├── tox.ini
    ├── pyproject.toml
    └── mypkg/
        ├── __init__.py
        ├── mymodule.py
        └── my_data_file.txt

- "single-module": a project that contains a single Python script::

    .
    ├── tox.ini
    ├── pyproject.toml
    └── mymodule.py

"""

import os
from glob import glob
from fnmatch import fnmatchcase

import _distutils_hack.override  # noqa: F401

from distutils.util import convert_path


def _valid_name(path):
    # Ignore invalid names that cannot be imported directly
    return os.path.basename(path).isidentifier()


class Finder:
    @staticmethod
    def _build_filter(*patterns):
        """
        Given a list of patterns, return a callable that will be true only if
        the input matches at least one of the patterns.
        """
        return lambda name: any(fnmatchcase(name, pat) for pat in patterns)


class PackageFinder(Finder):
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


class PEP420PackageFinder(PackageFinder):
    @staticmethod
    def _looks_like_package(path):
        return True


class FlatLayoutPackageFinder(PEP420PackageFinder):
    """When trying to find packages right under the root directory of a
    repository/project, we have to be extra careful to not include things that
    are not meant for inclusion (such as tool configuration files)
    """

    EXCLUDE = (
        "doc",
        "docs",
        "test",
        "tests",
        "example",
        "examples",
        # ---- Task runners / Build tools ----
        "tasks",  # invoke
        "fabfile",  # fabric
        "site_scons",  # SCons
        # ---- Hidden directories/Private packages ----
        "[._]*",
    )

    @classmethod
    def find(cls, where='.', exclude=(), include=('*',)):
        exclude = [*exclude, *cls.EXCLUDE] + [f"{e}.*" for e in cls.EXCLUDE]
        return super().find(where, exclude, include)

    _looks_like_package = staticmethod(_valid_name)


class ModuleFinder(Finder):
    INCLUDE = ()
    EXCLUDE = ()

    @classmethod
    def find(cls, where='.', exclude=(), include=('*',)):
        """Find isolated Python modules.

        The arguments ``where``, ``exclude`` and ``include`` have basically the
        same meaning as in PackageFinder. This function will **not** recurse
        subdirectories.
        """
        return list(
            cls._find_modules_iter(
                convert_path(where),
                cls._build_filter(*cls.EXCLUDE, *exclude),
                cls._build_filter(*cls.INCLUDE, *include),
            )
        )

    @classmethod
    def _find_modules_iter(cls, where, exclude, include):
        for file in glob(os.path.join(where, "*.py")):
            module, _ext = os.path.splitext(os.path.basename(file))

            if not cls._looks_like_module(module):
                continue

            if include(module) and not exclude(module):
                yield module

    _looks_like_module = staticmethod(_valid_name)


class FlatLayoutModuleFinder(ModuleFinder):
    """We have to be very careful in the case of flat layout and
    single-modules
    """

    EXCLUDE = (
        "setup",
        "conftest",
        "test",
        "tests",
        "example",
        "examples",
        # ---- Task runners ----
        "pavement",
        "tasks",
        "noxfile",
        "dodo",
        "fabfile",
        # ---- Other tools ----
        "[Ss][Cc]onstruct",  # SCons
        "conanfile",  # Connan: C/C++ build tool
        "manage",  # Django
        # ---- Hidden files/Private modules ----
        "[._]*",
    )
    _looks_like_module = staticmethod(_valid_name)
