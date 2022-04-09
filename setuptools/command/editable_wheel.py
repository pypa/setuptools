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
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, Iterator, List, Union

from setuptools import Command, namespaces
from setuptools.discovery import find_package_path
from setuptools.dist import Distribution

_Path = Union[str, Path]


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
            raise NotImplementedError

        packages = _find_packages(dist)
        has_simple_layout = _simple_layout(packages, self.package_dir, project_dir)
        if set(self.package_dir) == {""} and has_simple_layout:
            # src-layout(ish) package detected. These kind of packages are relatively
            # safe so we can simply add the src directory to the pth file.
            return _StaticPth(dist, name, [Path(project_dir, self.package_dir[""])])

        # >>> msg = "TODO: Explain limitations with meta path finder"
        # >>> warnings.warn(msg)
        paths = [Path(project_dir, p) for p in (".", self.package_dir.get("")) if p]
        # TODO: return _TopLevelFinder(dist, name, auxiliar_build_dir)
        return _StaticPth(dist, name, paths)


class _StaticPth:
    def __init__(self, dist: Distribution, name: str, path_entries: List[Path]):
        self.dist = dist
        self.name = name
        self.path_entries = path_entries

    def __call__(self, unpacked_wheel_dir: Path):
        pth = Path(unpacked_wheel_dir, f"__editable__.{self.name}.pth")
        entries = "\n".join((str(p.resolve()) for p in self.path_entries))
        pth.write_text(f"{entries}\n", encoding="utf-8")


def _simple_layout(
    packages: Iterable[str], package_dir: Dict[str, str], project_dir: Path
) -> bool:
    """Make sure all packages are contained by the same parent directory.

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
    parent = os.path.commonpath(list(layout.values()))
    return all(
        _normalize_path(Path(parent, *key.split('.'))) == _normalize_path(value)
        for key, value in layout.items()
    )


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


def _normalize_path(filename: _Path) -> str:
    """Normalize a file/dir name for comparison purposes"""
    # See pkg_resources.normalize_path
    file = os.path.abspath(filename) if sys.platform == 'cygwin' else filename
    return os.path.normcase(os.path.realpath(os.path.normpath(file)))


def _empty_dir(dir_: Path) -> Path:
    shutil.rmtree(dir_, ignore_errors=True)
    dir_.mkdir()
    return dir_


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


_FINDER_TEMPLATE = """
class __EditableFinder:
    MAPPING = {mapping!r}
    NAMESPACES = {namespaces!r}

    @classmethod
    def install(cls):
        import sys

        if not any(finder == cls for finder in sys.meta_path):
            sys.meta_path.append(cls)

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
        # when no other package is installed in the same namespace
        from importlib.machinery import ModuleSpec

        # PEP 451 mentions setting loader to None for namespaces:
        return ModuleSpec(name, None, is_package=True)

    @classmethod
    def _find_spec(cls, fullname, parent, parent_path):
        from importlib.machinery import all_suffixes as module_suffixes
        from importlib.util import spec_from_file_location
        from itertools import chain

        rest = fullname.replace(parent, "").strip(".").split(".")
        candidate_path = Path(parent_path, *rest)

        init = candidate_path / "__init__.py"
        candidates = (candidate_path.with_suffix(x) for x in module_suffixes())
        for candidate in chain([init], candidates):
            if candidate.exists():
                spec = spec_from_file_location(fullname, candidate)
                return spec

        return None


__EditableFinder.install()
"""
