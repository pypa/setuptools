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
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, Iterator, List, Mapping, Union, Tuple, TypeVar

from setuptools import Command, namespaces
from setuptools.discovery import find_package_path
from setuptools.dist import Distribution

_Path = Union[str, Path]
_P = TypeVar("_P", bound=_Path)
_logger = logging.getLogger(__name__)


_STRICT_WARNING = """
New or renamed files may not be automatically picked up without a new installation.
"""

_LAX_WARNING = """
Options like `package-data`, `include/exclude-package-data` or
`packages.find.exclude/include` may have no effect.
"""


class editable_wheel(Command):
    """Build 'editable' wheel for development"""

    description = "create a PEP 660 'editable' wheel"

    user_options = [
        ("dist-dir=", "d", "directory to put final built distributions in"),
        ("dist-info-dir=", "I", "path to a pre-build .dist-info directory"),
        ("strict", None, "perform an strict installation"),
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
        dist_name = dist_info.name
        tag = "-".join(bdist_wheel.get_tag())
        build_tag = "0.editable"  # According to PEP 427 needs to start with digit
        archive_name = f"{dist_name}-{build_tag}-{tag}.whl"
        wheel_path = Path(self.dist_dir, archive_name)
        if wheel_path.exists():
            wheel_path.unlink()

        # Currently the wheel API receives a directory and dump all its contents
        # inside of a wheel. So let's use a temporary directory.
        unpacked_tmp = TemporaryDirectory(suffix=archive_name)
        build_tmp = TemporaryDirectory(suffix=".build-temp")

        with unpacked_tmp as unpacked, build_tmp as tmp:
            unpacked_dist_info = Path(unpacked, Path(self.dist_info_dir).name)
            shutil.copytree(self.dist_info_dir, unpacked_dist_info)
            self._install_namespaces(unpacked, dist_info.name)

            # Add non-editable files to the wheel
            _configure_build(dist_name, self.distribution, unpacked, tmp)
            self._run_install("headers")
            self._run_install("scripts")
            self._run_install("data")

            self._populate_wheel(dist_info.name, tag, unpacked, tmp)
            with WheelFile(wheel_path, "w") as wf:
                wf.write_files(unpacked)

        return wheel_path

    def _run_install(self, category: str):
        has_category = getattr(self.distribution, f"has_{category}", None)
        if has_category and has_category():
            _logger.info(f"Installing {category} as non editable")
            self.run_command(f"install_{category}")

    def _populate_wheel(self, name: str, tag: str, unpacked_dir: Path, tmp: _Path):
        """Decides which strategy to use to implement an editable installation."""
        build_name = f"__editable__.{name}-{tag}"
        project_dir = Path(self.project_dir)

        if self.strict or os.getenv("SETUPTOOLS_EDITABLE", None) == "strict":
            return self._populate_link_tree(name, build_name, unpacked_dir, tmp)

        # Build extensions in-place
        self.reinitialize_command("build_ext", inplace=1)
        self.run_command("build_ext")

        packages = _find_packages(self.distribution)
        has_simple_layout = _simple_layout(packages, self.package_dir, project_dir)
        if set(self.package_dir) == {""} and has_simple_layout:
            # src-layout(ish) is relatively safe for a simple pth file
            return self._populate_static_pth(name, project_dir, unpacked_dir)

        # Use a MetaPathFinder to avoid adding accidental top-level packages/modules
        self._populate_finder(name, unpacked_dir)

    def _populate_link_tree(
        self, name: str, build_name: str, unpacked_dir: Path, tmp: _Path
    ):
        """Populate wheel using the "strict" ``link tree`` strategy."""
        msg = "Strict editable install will be performed using a link tree.\n"
        _logger.warning(msg + _STRICT_WARNING)
        auxiliary_build_dir = _empty_dir(Path(self.project_dir, "build", build_name))
        populate = _LinkTree(self.distribution, name, auxiliary_build_dir, tmp)
        populate(unpacked_dir)

    def _populate_static_pth(self, name: str, project_dir: Path, unpacked_dir: Path):
        """Populate wheel using the "lax" ``.pth`` file strategy, for ``src-layout``."""
        src_dir = self.package_dir[""]
        msg = f"Editable install will be performed using .pth file to {src_dir}.\n"
        _logger.warning(msg + _LAX_WARNING)
        populate = _StaticPth(self.distribution, name, [Path(project_dir, src_dir)])
        populate(unpacked_dir)

    def _populate_finder(self, name: str, unpacked_dir: Path):
        """Populate wheel using the "lax" MetaPathFinder strategy."""
        msg = "Editable install will be performed using a meta path finder.\n"
        _logger.warning(msg + _LAX_WARNING)
        populate = _TopLevelFinder(self.distribution, name)
        populate(unpacked_dir)


class _StaticPth:
    def __init__(self, dist: Distribution, name: str, path_entries: List[Path]):
        self.dist = dist
        self.name = name
        self.path_entries = path_entries

    def __call__(self, unpacked_wheel_dir: Path):
        pth = Path(unpacked_wheel_dir, f"__editable__.{self.name}.pth")
        entries = "\n".join((str(p.resolve()) for p in self.path_entries))
        pth.write_text(f"{entries}\n", encoding="utf-8")


class _LinkTree(_StaticPth):
    """
    Creates a ``.pth`` file that points to a link tree in the ``auxiliary_build_dir``.

    This strategy will only link files (not dirs), so it can be implemented in
    any OS, even if that means using hardlinks instead of symlinks.

    By collocating ``auxiliary_build_dir`` and the original source code, limitations
    with hardlinks should be avoided.
    """
    def __init__(
        self, dist: Distribution, name: str, auxiliary_build_dir: Path, tmp: _Path
    ):
        super().__init__(dist, name, [auxiliary_build_dir])
        self.auxiliary_build_dir = auxiliary_build_dir
        self.tmp = tmp

    def _build_py(self):
        if not self.dist.has_pure_modules():
            return

        build_py = self.dist.get_command_obj("build_py")
        build_py.ensure_finalized()
        # Force build_py to use links instead of copying files
        build_py.use_links = "sym" if _can_symlink_files() else "hard"
        build_py.run()

    def _build_ext(self):
        if not self.dist.has_ext_modules():
            return

        build_ext = self.dist.get_command_obj("build_ext")
        build_ext.ensure_finalized()
        # Extensions are not editable, so we just have to build them in the right dir
        build_ext.run()

    def __call__(self, unpacked_wheel_dir: Path):
        _configure_build(self.name, self.dist, self.auxiliary_build_dir, self.tmp)
        self._build_py()
        self._build_ext()
        super().__call__(unpacked_wheel_dir)


class _TopLevelFinder:
    def __init__(self, dist: Distribution, name: str):
        self.dist = dist
        self.name = name

    def __call__(self, unpacked_wheel_dir: Path):
        src_root = self.dist.src_root or os.curdir
        top_level = chain(_find_packages(self.dist), _find_top_level_modules(self.dist))
        package_dir = self.dist.package_dir or {}
        roots = _find_package_roots(top_level, package_dir, src_root)

        namespaces_: Dict[str, List[str]] = dict(chain(
            _find_namespaces(self.dist.packages, roots),
            ((ns, []) for ns in _find_virtual_namespaces(roots)),
        ))

        name = f"__editable__.{self.name}.finder"
        finder = _make_identifier(name)
        content = _finder_template(name, roots, namespaces_)
        Path(unpacked_wheel_dir, f"{finder}.py").write_text(content, encoding="utf-8")

        pth = f"__editable__.{self.name}.pth"
        content = f"import {finder}; {finder}.install()"
        Path(unpacked_wheel_dir, pth).write_text(content, encoding="utf-8")


def _configure_build(name: str, dist: Distribution, target_dir: _Path, tmp_dir: _Path):
    target = str(target_dir)
    data = str(Path(target_dir, f"{name}.data", "data"))
    headers = str(Path(target_dir, f"{name}.data", "include"))
    scripts = str(Path(target_dir, f"{name}.data", "scripts"))

    # egg-info will be generated again to create a manifest (used for package data)
    egg_info = dist.reinitialize_command("egg_info", reinit_subcommands=True)
    egg_info.egg_base = str(tmp_dir)
    egg_info.ignore_egg_info_in_manifest = True

    build = dist.reinitialize_command("build", reinit_subcommands=True)
    install = dist.reinitialize_command("install", reinit_subcommands=True)

    build.build_platlib = build.build_purelib = build.build_lib = target
    install.install_purelib = install.install_platlib = install.install_lib = target
    install.install_scripts = build.build_scripts = scripts
    install.install_headers = headers
    install.install_data = data

    build.build_temp = str(tmp_dir)

    build_py = dist.get_command_obj("build_py")
    build_py.compile = False

    build.ensure_finalized()
    install.ensure_finalized()


def _can_symlink_files():
    try:
        with TemporaryDirectory() as tmp:
            path1, path2 = Path(tmp, "file1.txt"), Path(tmp, "file2.txt")
            path1.write_text("file1", encoding="utf-8")
            os.symlink(path1, path2)
            return path2.is_symlink() and path2.read_text(encoding="utf-8") == "file1"
    except (AttributeError, NotImplementedError, OSError):
        return False


def _simple_layout(
    packages: Iterable[str], package_dir: Dict[str, str], project_dir: Path
) -> bool:
    """Return ``True`` if:
    - all packages are contained by the same parent directory, **and**
    - all packages become importable if the parent directory is added to ``sys.path``.

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
    >>> _simple_layout(['a', 'a.a1', 'a.a1.a2', 'b'], {"a.a1.a2": "_a2"}, ".")
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
    """Infer the parent path containing a package, that if added to ``sys.path`` would
    allow importing that package.
    When ``pkg`` is directly mapped into a directory with a different name, return its
    own path.
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


def _find_package_roots(
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


def _find_virtual_namespaces(pkg_roots: Dict[str, str]) -> Iterator[str]:
    """By carefully designing ``package_dir``, it is possible to implement the logical
    structure of PEP 420 in a package without the corresponding directories.
    This function will try to find this kind of namespaces.
    """
    for pkg in pkg_roots:
        if "." not in pkg:
            continue
        parts = pkg.split(".")
        for i in range(len(parts) - 1, 0, -1):
            partial_name = ".".join(parts[:i])
            path = Path(find_package_path(partial_name, pkg_roots, ""))
            if not path.exists():
                yield partial_name


def _find_namespaces(
    packages: List[str], pkg_roots: Dict[str, str]
) -> Iterator[Tuple[str, List[str]]]:
    for pkg in packages:
        path = find_package_path(pkg, pkg_roots, "")
        if Path(path).exists() and not Path(path, "__init__.py").exists():
            yield (pkg, [path])


def _remove_nested(pkg_roots: Dict[str, str]) -> Dict[str, str]:
    output = dict(pkg_roots.copy())

    for pkg, path in reversed(list(pkg_roots.items())):
        if any(
            pkg != other and _is_nested(pkg, path, other, other_path)
            for other, other_path in pkg_roots.items()
        ):
            output.pop(pkg)

    return output


def _is_nested(pkg: str, pkg_path: str, parent: str, parent_path: str) -> bool:
    """
    Return ``True`` if ``pkg`` is nested inside ``parent`` both logically and in the
    file system.
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


def _empty_dir(dir_: _P) -> _P:
    """Create a directory ensured to be empty. Existing files may be removed."""
    shutil.rmtree(dir_, ignore_errors=True)
    os.makedirs(dir_)
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
from importlib.machinery import ModuleSpec
from importlib.machinery import all_suffixes as module_suffixes
from importlib.util import spec_from_file_location
from itertools import chain
from pathlib import Path

MAPPING = {mapping!r}
NAMESPACES = {namespaces!r}
PATH_PLACEHOLDER = {name!r} + ".__path_hook__"


class _EditableFinder:  # MetaPathFinder
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        for pkg, pkg_path in reversed(list(MAPPING.items())):
            if fullname.startswith(pkg):
                rest = fullname.replace(pkg, "").strip(".").split(".")
                return cls._find_spec(fullname, Path(pkg_path, *rest))

        return None

    @classmethod
    def _find_spec(cls, fullname, candidate_path):
        init = candidate_path / "__init__.py"
        candidates = (candidate_path.with_suffix(x) for x in module_suffixes())
        for candidate in chain([init], candidates):
            if candidate.exists():
                return spec_from_file_location(fullname, candidate)


class _EditableNamespaceFinder:  # PathEntryFinder
    @classmethod
    def _path_hook(cls, path):
        if path == PATH_PLACEHOLDER:
            return cls
        raise ImportError

    @classmethod
    def _paths(cls, fullname):
        # Ensure __path__ is not empty for the spec to be considered a namespace.
        return NAMESPACES[fullname] or MAPPING.get(fullname) or [PATH_PLACEHOLDER]

    @classmethod
    def find_spec(cls, fullname, target=None):
        if fullname in NAMESPACES:
            spec = ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = cls._paths(fullname)
            return spec
        return None

    @classmethod
    def find_module(cls, fullname):
        return None


def install():
    if not any(finder == _EditableFinder for finder in sys.meta_path):
        sys.meta_path.append(_EditableFinder)

    if not NAMESPACES:
        return

    if not any(hook == _EditableNamespaceFinder._path_hook for hook in sys.path_hooks):
        # PathEntryFinder is needed to create NamespaceSpec without private APIS
        sys.path_hooks.append(_EditableNamespaceFinder._path_hook)
    if PATH_PLACEHOLDER not in sys.path:
        sys.path.append(PATH_PLACEHOLDER)  # Used just to trigger the path hook
"""


def _finder_template(
    name: str, mapping: Mapping[str, str], namespaces: Dict[str, List[str]]
) -> str:
    """Create a string containing the code for the``MetaPathFinder`` and
    ``PathEntryFinder``.
    """
    mapping = dict(sorted(mapping.items(), key=lambda p: p[0]))
    return _FINDER_TEMPLATE.format(name=name, mapping=mapping, namespaces=namespaces)
