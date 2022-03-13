"""Automatic discovery of Python modules and packages (for inclusion in the
distribution) and other config values.

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
  have a directory under the project root for each package::

    .
    ├── tox.ini
    ├── pyproject.toml
    └── mypkg/
        ├── __init__.py
        ├── mymodule.py
        └── my_data_file.txt

- "single-module": a project that contains a single Python script direct under
  the project root (no directory used)::

    .
    ├── tox.ini
    ├── pyproject.toml
    └── mymodule.py

"""

import itertools
import os
from fnmatch import fnmatchcase
from glob import glob

import _distutils_hack.override  # noqa: F401

from distutils import log
from distutils.util import convert_path

from typing import Dict, List, Optional, Union
_Path = Union[str, os.PathLike]

chain_iter = itertools.chain.from_iterable


def _valid_name(path):
    # Ignore invalid names that cannot be imported directly
    return os.path.basename(path).isidentifier()


class _Finder:
    """Base class that exposes functionality for module/package finders"""

    ALWAYS_EXCLUDE = ()
    DEFAULT_EXCLUDE = ()

    @classmethod
    def find(cls, where='.', exclude=(), include=('*',)):
        """Return a list of all Python items (packages or modules, depending on
        the finder implementation) found within directory 'where'.

        'where' is the root directory which will be searched.
        It should be supplied as a "cross-platform" (i.e. URL-style) path;
        it will be converted to the appropriate local path syntax.

        'exclude' is a sequence of names to exclude; '*' can be used
        as a wildcard in the names.
        When finding packages, 'foo.*' will exclude all subpackages of 'foo'
        (but not 'foo' itself).

        'include' is a sequence of names to include.
        If it's specified, only the named items will be included.
        If it's not specified, all found items will be included.
        'include' can contain shell style wildcard patterns just like
        'exclude'.
        """

        exclude = exclude or cls.DEFAULT_EXCLUDE
        return list(
            cls._find_iter(
                convert_path(str(where)),
                cls._build_filter(*cls.ALWAYS_EXCLUDE, *exclude),
                cls._build_filter(*include),
            )
        )

    @classmethod
    def _find_iter(cls, where, exclude, include):
        raise NotImplementedError

    @staticmethod
    def _build_filter(*patterns):
        """
        Given a list of patterns, return a callable that will be true only if
        the input matches at least one of the patterns.
        """
        return lambda name: any(fnmatchcase(name, pat) for pat in patterns)


class PackageFinder(_Finder):
    """
    Generate a list of all Python packages found within a directory
    """

    ALWAYS_EXCLUDE = ("ez_setup", "*__pycache__")

    @classmethod
    def _find_iter(cls, where, exclude, include):
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


class ModuleFinder(_Finder):
    """Find isolated Python modules.
    This function will **not** recurse subdirectories.
    """

    @classmethod
    def _find_iter(cls, where, exclude, include):
        for file in glob(os.path.join(where, "*.py")):
            module, _ext = os.path.splitext(os.path.basename(file))

            if not cls._looks_like_module(module):
                continue

            if include(module) and not exclude(module):
                yield module

    _looks_like_module = staticmethod(_valid_name)


# We have to be extra careful in the case of flat layout to not include files
# and directories not meant for distribution (e.g. tool-related)


class FlatLayoutPackageFinder(PEP420PackageFinder):
    _EXCLUDE = (
        "bin",
        "doc",
        "docs",
        "documentation",
        "test",
        "tests",
        "example",
        "examples",
        "scripts",
        "tools",
        "build",
        "dist",
        "venv",
        # ---- Task runners / Build tools ----
        "tasks",  # invoke
        "fabfile",  # fabric
        "site_scons",  # SCons
        # ---- Hidden directories/Private packages ----
        "[._]*",
    )

    DEFAULT_EXCLUDE = tuple(chain_iter((p, f"{p}.*") for p in _EXCLUDE))
    """Reserved package names"""

    _looks_like_package = staticmethod(_valid_name)


class FlatLayoutModuleFinder(ModuleFinder):
    DEFAULT_EXCLUDE = (
        "setup",
        "conftest",
        "test",
        "tests",
        "example",
        "examples",
        "build",
        # ---- Task runners ----
        "noxfile",
        "pavement",
        "dodo",
        "tasks",
        "fabfile",
        # ---- Other tools ----
        "[Ss][Cc]onstruct",  # SCons
        "conanfile",  # Connan: C/C++ build tool
        "manage",  # Django
        # ---- Hidden files/Private modules ----
        "[._]*",
    )
    """Reserved top-level module names"""


def _find_packages_within(root_pkg, pkg_dir):
    nested = PEP420PackageFinder.find(pkg_dir)
    return [root_pkg] + [".".join((root_pkg, n)) for n in nested]


class ConfigDiscovery:
    """Fill-in metadata and options that can be automatically derived
    (from other metadata/options, the file system or conventions)
    """

    def __init__(self, distribution):
        self.dist = distribution
        self._called = False
        self._root_dir = None  # delay so `src_root` can be set in dist

    def __call__(self, force=False, name=True):
        """Automatically discover missing configuration fields
        and modifies the given ``distribution`` object in-place.

        Note that by default this will only have an effect the first time the
        ``ConfigDiscovery`` object is called.

        To repeatedly invoke automatic discovery (e.g. when the project
        directory changes), please use ``force=True`` (or create a new
        ``ConfigDiscovery`` instance).
        """
        if force is False and self._called:
            # Avoid overhead of multiple calls
            return

        self._root_dir = self.dist.src_root or os.curdir

        self._analyse_package_layout()
        if name:
            self.analyse_name()  # depends on ``packages`` and ``py_modules``

        self._called = True

    def _analyse_package_layout(self):
        if self.dist.packages is not None or self.dist.py_modules is not None:
            # For backward compatibility, just try to find modules/packages
            # when nothing is given
            return None

        log.debug(
            "No `packages` or `py_modules` configuration, performing "
            "automatic discovery."
        )

        return (
            self._analyse_explicit_layout()
            or self._analyse_src_layout()
            # flat-layout is the trickiest for discovery so it should be last
            or self._analyse_flat_layout()
        )

    def _analyse_explicit_layout(self):
        """The user can explicitly give a package layout via ``package_dir``"""
        package_dir = (self.dist.package_dir or {}).copy()
        package_dir.pop("", None)  # This falls under the "src-layout" umbrella
        root_dir = self._root_dir

        if not package_dir:
            return False

        pkgs = chain_iter(
            _find_packages_within(pkg, os.path.join(root_dir, parent_dir))
            for pkg, parent_dir in package_dir.items()
        )
        self.dist.packages = list(pkgs)
        log.debug(f"`explicit-layout` detected -- analysing {package_dir}")
        return True

    def _analyse_src_layout(self):
        """Try to find all packages or modules under the ``src`` directory
        (or anything pointed by ``package_dir[""]``).

        The "src-layout" is relatively safe for automatic discovery.
        We assume that everything within is meant to be included in the
        distribution.

        If ``package_dir[""]`` is not given, but the ``src`` directory exists,
        this function will set ``package_dir[""] = "src"``.
        """
        package_dir = self.dist.package_dir = self.dist.package_dir or {}
        src_dir = os.path.join(self._root_dir, package_dir.get("", "src"))
        if not os.path.isdir(src_dir):
            return False

        package_dir.setdefault("", os.path.basename(src_dir))
        self.dist.packages = PEP420PackageFinder.find(src_dir)
        self.dist.py_modules = ModuleFinder.find(src_dir)
        log.debug(f"`src-layout` detected -- analysing {src_dir}")
        return True

    def _analyse_flat_layout(self):
        """Try to find all packages and modules under the project root"""
        self.dist.packages = FlatLayoutPackageFinder.find(self._root_dir)
        self.dist.py_modules = FlatLayoutModuleFinder.find(self._root_dir)
        log.debug(f"`flat-layout` detected -- analysing {self._root_dir}")
        return True

    def analyse_name(self):
        """The packages/modules are the essential contribution of the author.
        Therefore the name of the distribution can be derived from them.
        """
        if self.dist.metadata.name or self.dist.name:
            # get_name() is not reliable (can return "UNKNOWN")
            return None

        log.debug("No `name` configuration, performing automatic discovery")

        name = (
            self._find_name_single_package_or_module()
            or self._find_name_from_packages()
        )
        if name:
            self.dist.metadata.name = name
            self.dist.name = name

    def _find_name_single_package_or_module(self):
        """Exactly one module or package"""
        for field in ('packages', 'py_modules'):
            items = getattr(self.dist, field, None) or []
            if items and len(items) == 1:
                log.debug(f"Single module/package detected, name: {items[0]}")
                return items[0]

        return None

    def _find_name_from_packages(self):
        """Try to find the root package that is not a PEP 420 namespace"""
        if not self.dist.packages:
            return None

        packages = sorted(self.dist.packages, key=len)
        package_dir = self.dist.package_dir or {}

        parent_pkg = find_parent_package(packages, package_dir, self._root_dir)
        if parent_pkg:
            log.debug(f"Common parent package detected, name: {parent_pkg}")
            return parent_pkg

        log.warn("No parent package detected, impossible to derive `name`")
        return None


def find_parent_package(
    packages: List[str], package_dir: Dict[str, str], root_dir: _Path
) -> Optional[str]:
    packages = sorted(packages, key=len)
    common_ancestors = []
    for i, name in enumerate(packages):
        if not all(n.startswith(name) for n in packages[i+1:]):
            # Since packages are sorted by length, this condition is able
            # to find a list of all common ancestors.
            # When there is divergence (e.g. multiple root packages)
            # the list will be empty
            break
        common_ancestors.append(name)

    for name in common_ancestors:
        pkg_path = find_package_path(name, package_dir, root_dir)
        init = os.path.join(pkg_path, "__init__.py")
        if os.path.isfile(init):
            return name

    return None


def find_package_path(name: str, package_dir: Dict[str, str], root_dir: _Path) -> str:
    """Given a package name, return the path where it should be found on
    disk, considering the ``package_dir`` option.
    """
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        # Look backwards, the most specific package_dir first
        partial_name = ".".join(parts[:i])
        if partial_name in package_dir:
            parent = package_dir[partial_name]
            return os.path.join(root_dir, parent, *parts[i:])

    parent = package_dir.get("") or ""
    return os.path.join(root_dir, *parent.split("/"), *parts)
