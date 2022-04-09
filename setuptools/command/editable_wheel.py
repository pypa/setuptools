"""
Create a wheel that, when installed, will make the source package 'editable'
(add it to the interpreter's path, including metadata) per PEP 660. Replaces
'setup.py develop'.

.. note::
   One of the mechanisms briefly mentioned in PEP 660 to implement editable installs is
   to create a separated directory inside ``build`` and use a .pth file to point to that
   directory. In the context of this file such directory is referred as
   *auxiliary build directory* or ``auxiliary_build_dir``.
"""

import os
import re
import shutil
import sys
import logging
from itertools import chain
from inspect import cleandoc
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, Iterator, List, Mapping, Set, Union

from setuptools import Command, namespaces
from setuptools.discovery import find_package_path
from setuptools.dist import Distribution

_Path = Union[str, Path]
_logger = logging.getLogger(__name__)


class editable_wheel(Command):
    """Build 'editable' wheel for development"""

    description = "create a PEP 660 'editable' wheel"

    user_options = [
        ("dist-dir=", "d", "directory to put final built distributions in"),
        ("dist-info-dir=", "I", "path to a pre-build .dist-info directory"),
    ]

    boolean_options = ["strict"]

    def initialize_options(self):
        self.dist_dir = None
        self.dist_info_dir = None
        self.project_dir = None
        self.strict = False

    def finalize_options(self):
        dist = self.distribution
        self.project_dir = dist.src_root or os.curdir
        self.package_dir = dist.package_dir or {}
        self.dist_dir = Path(self.dist_dir or os.path.join(self.project_dir, "dist"))
        self.dist_dir.mkdir(exist_ok=True)

    def run(self):
        self._ensure_dist_info()

        # Add missing dist_info files
        bdist_wheel = self.reinitialize_command("bdist_wheel")
        bdist_wheel.write_wheelfile(self.dist_info_dir)

        # Build extensions in-place
        self.reinitialize_command("build_ext", inplace=1)
        self.run_command("build_ext")

        self._create_wheel_file(bdist_wheel)

    def _ensure_dist_info(self):
        if self.dist_info_dir is None:
            dist_info = self.reinitialize_command("dist_info")
            dist_info.output_dir = self.dist_dir
            dist_info.finalize_options()
            dist_info.run()
            self.dist_info_dir = dist_info.dist_info_dir
        else:
            assert str(self.dist_info_dir).endswith(".dist-info")
            assert Path(self.dist_info_dir, "METADATA").exists()

    def _install_namespaces(self, installation_dir, pth_prefix):
        # XXX: Only required to support the deprecated namespace practice
        dist = self.distribution
        if not dist.namespace_packages:
            return

        src_root = Path(self.project_dir, self.pakcage_dir.get("", ".")).resolve()
        installer = _NamespaceInstaller(dist, installation_dir, pth_prefix, src_root)
        installer.install_namespaces()

    def _create_wheel_file(self, bdist_wheel):
        from wheel.wheelfile import WheelFile

        dist_info = self.get_finalized_command("dist_info")
        tag = "-".join(bdist_wheel.get_tag())
        editable_name = dist_info.name
        build_tag = "0.editable"  # According to PEP 427 needs to start with digit
        archive_name = f"{editable_name}-{build_tag}-{tag}.whl"
        wheel_path = Path(self.dist_dir, archive_name)
        if wheel_path.exists():
            wheel_path.unlink()

        # Currently the wheel API receives a directory and dump all its contents
        # inside of a wheel. So let's use a temporary directory.
        with TemporaryDirectory(suffix=archive_name) as tmp:
            tmp_dist_info = Path(tmp, Path(self.dist_info_dir).name)
            shutil.copytree(self.dist_info_dir, tmp_dist_info)
            self._install_namespaces(tmp, editable_name)
            populate = self._populate_strategy(editable_name, tag)
            populate(tmp)
            with WheelFile(wheel_path, "w") as wf:
                wf.write_files(tmp)

        return wheel_path

    def _populate_strategy(self, name, tag):
        """Decides which strategy to use to implement an editable installation."""
        dist = self.distribution
        build_name = f"__editable__.{name}-{tag}"
        project_dir = Path(self.project_dir)
        auxiliar_build_dir = Path(self.project_dir, "build", build_name)

        if self.strict:
            # The LinkTree strategy will only link files, so it can be implemented in
            # any OS, even if that means using hardlinks instead of symlinks
            auxiliar_build_dir = _empty_dir(auxiliar_build_dir)
            # TODO: return _LinkTree(dist, name, auxiliar_build_dir)
            msg = """
            Strict editable install will be performed using a link tree.
            New files will not be automatically picked up without a new installation.
            """
            _logger.info(cleandoc(msg))
            raise NotImplementedError

        packages = _find_packages(dist)
        has_simple_layout = _simple_layout(packages, self.package_dir, project_dir)
        if set(self.package_dir) == {""} and has_simple_layout:
            # src-layout(ish) package detected. These kind of packages are relatively
            # safe so we can simply add the src directory to the pth file.
            src_dir = self.package_dir[""]
            msg = f"Editable install will be performed using .pth file to {src_dir}."
            _logger.info(msg)
            return _StaticPth(dist, name, [Path(project_dir, src_dir)])

        msg = """
        Editable install will be performed using a meta path finder.
        If you add any top-level packages or modules, they might not be automatically
        picked up without a new installation.
        """
        _logger.info(cleandoc(msg))
        return _TopLevelFinder(dist, name)


class _StaticPth:
    def __init__(self, dist: Distribution, name: str, path_entries: List[Path]):
        self.dist = dist
        self.name = name
        self.path_entries = path_entries

    def __call__(self, unpacked_wheel_dir: Path):
        pth = Path(unpacked_wheel_dir, f"__editable__.{self.name}.pth")
        entries = "\n".join((str(p.resolve()) for p in self.path_entries))
        pth.write_text(f"{entries}\n", encoding="utf-8")


class _TopLevelFinder:
    def __init__(self, dist: Distribution, name: str):
        self.dist = dist
        self.name = name

    def __call__(self, unpacked_wheel_dir: Path):
        src_root = self.dist.src_root or os.curdir
        packages = chain(_find_packages(self.dist), _find_top_level_modules(self.dist))
        package_dir = self.dist.package_dir or {}
        pkg_roots = _find_pkg_roots(packages, package_dir, src_root)
        namespaces_ = set(_find_mapped_namespaces(pkg_roots))

        finder = _make_identifier(f"__editable__.{self.name}.finder")
        content = _finder_template(pkg_roots, namespaces_)
        Path(unpacked_wheel_dir, f"{finder}.py").write_text(content, encoding="utf-8")

        pth = f"__editable__.{self.name}.pth"
        content = f"import {finder}; {finder}.install()"
        Path(unpacked_wheel_dir, pth).write_text(content, encoding="utf-8")


def _simple_layout(
    packages: Iterable[str], package_dir: Dict[str, str], project_dir: Path
) -> bool:
    """Make sure all packages are contained by the same parent directory.

    >>> _simple_layout(['a'], {"": "src"}, "/tmp/myproj")
    True
    >>> _simple_layout(['a', 'a.b'], {"": "src"}, "/tmp/myproj")
    True
    >>> _simple_layout(['a', 'a.b'], {}, "/tmp/myproj")
    True
    >>> _simple_layout(['a', 'a.a1', 'a.a1.a2', 'b'], {"": "src"}, "/tmp/myproj")
    True
    >>> _simple_layout(['a', 'a.a1', 'a.a1.a2', 'b'], {"a": "a", "b": "b"}, ".")
    True
    >>> _simple_layout(['a', 'a.a1', 'a.a1.a2', 'b'], {"a": "_a", "b": "_b"}, ".")
    False
    >>> _simple_layout(['a', 'a.a1', 'a.a1.a2', 'b'], {"a": "_a"}, "/tmp/myproj")
    False
    >>> _simple_layout(
    ...     ['a', 'a.a1', 'a.a1.a2', 'b'],
    ...     {"a": "_a", "a.a1.a2": "_a2", "b": "_b"},
    ...     ".",
    ... )
    False
    """
    layout = {
        pkg: find_package_path(pkg, package_dir, project_dir)
        for pkg in packages
    }
    if not layout:
        return False
    parent = os.path.commonpath([_parent_path(k, v) for k, v in layout.items()])
    return all(
        _normalize_path(Path(parent, *key.split('.'))) == _normalize_path(value)
        for key, value in layout.items()
    )


def _parent_path(pkg, pkg_path):
    """Infer the parent path for a package if possible. When the pkg is directly mapped
    into a directory with a different name, return its own path.
    >>> _parent_path("a", "src/a")
    'src'
    >>> _parent_path("b", "src/c")
    'src/c'
    """
    parent = pkg_path[:-len(pkg)] if pkg_path.endswith(pkg) else pkg_path
    return parent.rstrip("/" + os.sep)


def _find_packages(dist: Distribution) -> Iterator[str]:
    yield from iter(dist.packages or [])

    py_modules = dist.py_modules or []
    nested_modules = [mod for mod in py_modules if "." in mod]
    if dist.ext_package:
        yield dist.ext_package
    else:
        ext_modules = dist.ext_modules or []
        nested_modules += [x.name for x in ext_modules if "." in x.name]

    for module in nested_modules:
        package, _, _ = module.rpartition(".")
        yield package


def _find_top_level_modules(dist: Distribution) -> Iterator[str]:
    py_modules = dist.py_modules or []
    yield from (mod for mod in py_modules if "." not in mod)

    if not dist.ext_package:
        ext_modules = dist.ext_modules or []
        yield from (x.name for x in ext_modules if "." not in x.name)


def _find_pkg_roots(
    packages: Iterable[str],
    package_dir: Mapping[str, str],
    src_root: _Path,
) -> Dict[str, str]:
    pkg_roots: Dict[str, str] = {
        pkg: _absolute_root(find_package_path(pkg, package_dir, src_root))
        for pkg in sorted(packages)
    }

    return _remove_nested(pkg_roots)


def _absolute_root(path: _Path) -> str:
    """Works for packages and top-level modules"""
    path_ = Path(path)
    parent = path_.parent

    if path_.exists():
        return str(path_.resolve())
    else:
        return str(parent.resolve() / path_.name)


def _find_mapped_namespaces(pkg_roots: Dict[str, str]) -> Iterator[str]:
    """By carefully designing ``package_dir``, it is possible to implement
    PEP 420 compatible namespaces without creating extra folders.
    This function will try to find this kind of namespaces.
    """
    for pkg in pkg_roots:
        if "." not in pkg:
            continue
        parts = pkg.split(".")
        for i in range(len(parts) - 1, 0, -1):
            partial_name = ".".join(parts[:i])
            path = find_package_path(partial_name, pkg_roots, "")
            if not Path(path, "__init__.py").exists():
                yield partial_name


def _remove_nested(pkg_roots: Dict[str, str]) -> Dict[str, str]:
    output = dict(pkg_roots.copy())

    for pkg, path in reversed(pkg_roots.items()):
        if any(
            pkg != other and _is_nested(pkg, path, other, other_path)
            for other, other_path in pkg_roots.items()
        ):
            output.pop(pkg)

    return output


def _is_nested(pkg: str, pkg_path: str, parent: str, parent_path: str) -> bool:
    """
    >>> _is_nested("a.b", "path/a/b", "a", "path/a")
    True
    >>> _is_nested("a.b", "path/a/b", "a", "otherpath/a")
    False
    >>> _is_nested("a.b", "path/a/b", "c", "path/c")
    False
    """
    norm_pkg_path = _normalize_path(pkg_path)
    rest = pkg.replace(parent, "").strip(".").split(".")
    return (
        pkg.startswith(parent)
        and norm_pkg_path == _normalize_path(Path(parent_path, *rest))
    )


def _normalize_path(filename: _Path) -> str:
    """Normalize a file/dir name for comparison purposes"""
    # See pkg_resources.normalize_path
    file = os.path.abspath(filename) if sys.platform == 'cygwin' else filename
    return os.path.normcase(os.path.realpath(os.path.normpath(file)))


def _empty_dir(dir_: Path) -> Path:
    shutil.rmtree(dir_, ignore_errors=True)
    dir_.mkdir()
    return dir_


def _make_identifier(name: str) -> str:
    """Make a string safe to be used as Python identifier.
    >>> _make_identifier("12abc")
    '_12abc'
    >>> _make_identifier("__editable__.myns.pkg-78.9.3_local")
    '__editable___myns_pkg_78_9_3_local'
    """
    safe = re.sub(r'\W|^(?=\d)', '_', name)
    assert safe.isidentifier()
    return safe


class _NamespaceInstaller(namespaces.Installer):
    def __init__(self, distribution, installation_dir, editable_name, src_root):
        self.distribution = distribution
        self.src_root = src_root
        self.installation_dir = installation_dir
        self.editable_name = editable_name
        self.outputs = []

    def _get_target(self):
        """Installation target."""
        return os.path.join(self.installation_dir, self.editable_name)

    def _get_root(self):
        """Where the modules/packages should be loaded from."""
        return repr(str(self.src_root))


_FINDER_TEMPLATE = """\
import sys
from importlib.machinery import all_suffixes as module_suffixes
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_file_location
from itertools import chain
from pathlib import Path

class __EditableFinder:
    MAPPING = {mapping!r}
    NAMESPACES = {namespaces!r}

    @classmethod
    def find_spec(cls, fullname, path, target=None):
        if fullname in cls.NAMESPACES:
            return cls._namespace_spec(fullname)

        for pkg, pkg_path in reversed(cls.MAPPING.items()):
            if fullname.startswith(pkg):
                return cls._find_spec(fullname, pkg, pkg_path)

        return None

    @classmethod
    def _namespace_spec(cls, name):
        # Since `cls` is appended to the path, this will only trigger
        # when no other package is installed in the same namespace.
        return ModuleSpec(name, None, is_package=True)
        # ^-- PEP 451 mentions setting loader to None for namespaces.

    @classmethod
    def _find_spec(cls, fullname, parent, parent_path):
        rest = fullname.replace(parent, "").strip(".").split(".")
        candidate_path = Path(parent_path, *rest)

        init = candidate_path / "__init__.py"
        candidates = (candidate_path.with_suffix(x) for x in module_suffixes())
        for candidate in chain([init], candidates):
            if candidate.exists():
                spec = spec_from_file_location(fullname, candidate)
                return spec

        if candidate_path.exists():
            return cls._namespace_spec(fullname)

        return None


def install():
    if not any(finder == __EditableFinder for finder in sys.meta_path):
        sys.meta_path.append(__EditableFinder)
"""


def _finder_template(mapping: Mapping[str, str], namespaces: Set[str]):
    mapping = dict(sorted(mapping.items(), key=lambda p: p[0]))
    return _FINDER_TEMPLATE.format(mapping=mapping, namespaces=namespaces)
