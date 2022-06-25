import os
import stat
import sys
import subprocess
import platform
from copy import deepcopy
from importlib import import_module
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock
from uuid import uuid4

import jaraco.envs
import jaraco.path
import pip_run.launch
import pytest
from path import Path as _Path

from . import contexts, namespaces

from setuptools._importlib import resources as importlib_resources
from setuptools.command.editable_wheel import (
    _LinkTree,
    _find_virtual_namespaces,
    _find_namespaces,
    _find_package_roots,
    _finder_template,
)
from setuptools.dist import Distribution


@pytest.fixture(params=["strict", "lax"])
def editable_mode(request, monkeypatch):
    if request.param == "strict":
        monkeypatch.setenv("SETUPTOOLS_EDITABLE", "strict")
    yield


EXAMPLE = {
    'pyproject.toml': dedent("""\
        [build-system]
        requires = ["setuptools"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "mypkg"
        version = "3.14159"
        license = {text = "MIT"}
        description = "This is a Python package"
        dynamic = ["readme"]
        classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers"
        ]
        urls = {Homepage = "http://github.com"}
        dependencies = ['importlib-metadata; python_version<"3.8"']

        [tool.setuptools]
        package-dir = {"" = "src"}
        packages = {find = {where = ["src"]}}
        license-files = ["LICENSE*"]

        [tool.setuptools.dynamic]
        readme = {file = "README.rst"}

        [tool.distutils.egg_info]
        tag-build = ".post0"
        """),
    "MANIFEST.in": dedent("""\
        global-include *.py *.txt
        global-exclude *.py[cod]
        prune dist
        prune build
        """).strip(),
    "README.rst": "This is a ``README``",
    "LICENSE.txt": "---- placeholder MIT license ----",
    "src": {
        "mypkg": {
            "__init__.py": dedent("""\
                import sys

                if sys.version_info[:2] >= (3, 8):
                    from importlib.metadata import PackageNotFoundError, version
                else:
                    from importlib_metadata import PackageNotFoundError, version

                try:
                    __version__ = version(__name__)
                except PackageNotFoundError:
                    __version__ = "unknown"
                """),
            "__main__.py": dedent("""\
                from importlib.resources import read_text
                from . import __version__, __name__ as parent
                from .mod import x

                data = read_text(parent, "data.txt")
                print(__version__, data, x)
                """),
            "mod.py": "x = ''",
            "data.txt": "Hello World",
        }
    }
}


SETUP_SCRIPT_STUB = "__import__('setuptools').setup()"


@pytest.mark.parametrize(
    "files",
    [
        {**EXAMPLE, "setup.py": SETUP_SCRIPT_STUB},  # type: ignore
        EXAMPLE,  # No setup.py script
    ]
)
def test_editable_with_pyproject(tmp_path, venv, files, editable_mode):
    project = tmp_path / "mypkg"
    project.mkdir()
    jaraco.path.build(files, prefix=project)

    cmd = [venv.exe(), "-m", "pip", "install",
           "--no-build-isolation",  # required to force current version of setuptools
           "-e", str(project)]
    print(str(subprocess.check_output(cmd), "utf-8"))

    cmd = [venv.exe(), "-m", "mypkg"]
    assert subprocess.check_output(cmd).strip() == b"3.14159.post0 Hello World"

    (project / "src/mypkg/data.txt").write_text("foobar")
    (project / "src/mypkg/mod.py").write_text("x = 42")
    assert subprocess.check_output(cmd).strip() == b"3.14159.post0 foobar 42"


def test_editable_with_flat_layout(tmp_path, venv, editable_mode):
    files = {
        "mypkg": {
            "pyproject.toml": dedent("""\
                [build-system]
                requires = ["setuptools", "wheel"]
                build-backend = "setuptools.build_meta"

                [project]
                name = "mypkg"
                version = "3.14159"

                [tool.setuptools]
                packages = ["pkg"]
                py-modules = ["mod"]
                """),
            "pkg": {"__init__.py": "a = 4"},
            "mod.py": "b = 2",
        },
    }
    jaraco.path.build(files, prefix=tmp_path)
    project = tmp_path / "mypkg"

    cmd = [venv.exe(), "-m", "pip", "install",
           "--no-build-isolation",  # required to force current version of setuptools
           "-e", str(project)]
    print(str(subprocess.check_output(cmd), "utf-8"))
    cmd = [venv.exe(), "-c", "import pkg, mod; print(pkg.a, mod.b)"]
    assert subprocess.check_output(cmd).strip() == b"4 2"


class TestLegacyNamespaces:
    """Ported from test_develop"""

    def test_namespace_package_importable(self, venv, tmp_path, editable_mode):
        """
        Installing two packages sharing the same namespace, one installed
        naturally using pip or `--single-version-externally-managed`
        and the other installed in editable mode should leave the namespace
        intact and both packages reachable by import.
        """
        pkg_A = namespaces.build_namespace_package(tmp_path, 'myns.pkgA')
        pkg_B = namespaces.build_namespace_package(tmp_path, 'myns.pkgB')
        # use pip to install to the target directory
        opts = ["--no-build-isolation"]  # force current version of setuptools
        venv.run(["python", "-m", "pip", "install", str(pkg_A), *opts])
        venv.run(["python", "-m", "pip", "install", "-e", str(pkg_B), *opts])
        venv.run(["python", "-c", "import myns.pkgA; import myns.pkgB"])
        # additionally ensure that pkg_resources import works
        venv.run(["python", "-c", "import pkg_resources"])


class TestPep420Namespaces:
    def test_namespace_package_importable(self, venv, tmp_path, editable_mode):
        """
        Installing two packages sharing the same namespace, one installed
        normally using pip and the other installed in editable mode
        should allow importing both packages.
        """
        pkg_A = namespaces.build_pep420_namespace_package(tmp_path, 'myns.n.pkgA')
        pkg_B = namespaces.build_pep420_namespace_package(tmp_path, 'myns.n.pkgB')
        # use pip to install to the target directory
        opts = ["--no-build-isolation"]  # force current version of setuptools
        venv.run(["python", "-m", "pip", "install", str(pkg_A), *opts])
        venv.run(["python", "-m", "pip", "install", "-e", str(pkg_B), *opts])
        venv.run(["python", "-c", "import myns.n.pkgA; import myns.n.pkgB"])

    def test_namespace_created_via_package_dir(self, venv, tmp_path, editable_mode):
        """Currently users can create a namespace by tweaking `package_dir`"""
        files = {
            "pkgA": {
                "pyproject.toml": dedent("""\
                    [build-system]
                    requires = ["setuptools", "wheel"]
                    build-backend = "setuptools.build_meta"

                    [project]
                    name = "pkgA"
                    version = "3.14159"

                    [tool.setuptools]
                    package-dir = {"myns.n.pkgA" = "src"}
                    """),
                "src": {"__init__.py": "a = 1"},
            },
        }
        jaraco.path.build(files, prefix=tmp_path)
        pkg_A = tmp_path / "pkgA"
        pkg_B = namespaces.build_pep420_namespace_package(tmp_path, 'myns.n.pkgB')
        pkg_C = namespaces.build_pep420_namespace_package(tmp_path, 'myns.n.pkgC')

        # use pip to install to the target directory
        opts = ["--no-build-isolation"]  # force current version of setuptools
        venv.run(["python", "-m", "pip", "install", str(pkg_A), *opts])
        venv.run(["python", "-m", "pip", "install", "-e", str(pkg_B), *opts])
        venv.run(["python", "-m", "pip", "install", "-e", str(pkg_C), *opts])
        venv.run(["python", "-c", "from myns.n import pkgA, pkgB, pkgC"])


# Moved here from test_develop:
@pytest.mark.xfail(
    platform.python_implementation() == 'PyPy',
    reason="Workaround fails on PyPy (why?)",
)
@pytest.mark.parametrize("mode", ("strict", "lax"))
def test_editable_with_prefix(tmp_path, sample_project, mode):
    """
    Editable install to a prefix should be discoverable.
    """
    prefix = tmp_path / 'prefix'

    # figure out where pip will likely install the package
    site_packages = prefix / next(
        Path(path).relative_to(sys.prefix)
        for path in sys.path
        if 'site-packages' in path and path.startswith(sys.prefix)
    )
    site_packages.mkdir(parents=True)

    # install workaround
    pip_run.launch.inject_sitecustomize(str(site_packages))

    env = dict(os.environ, PYTHONPATH=str(site_packages), SETUPTOOLS_EDITABLE=mode)
    cmd = [
        sys.executable,
        '-m',
        'pip',
        'install',
        '--editable',
        str(sample_project),
        '--prefix',
        str(prefix),
        '--no-build-isolation',
    ]
    subprocess.check_call(cmd, env=env)

    # now run 'sample' with the prefix on the PYTHONPATH
    bin = 'Scripts' if platform.system() == 'Windows' else 'bin'
    exe = prefix / bin / 'sample'
    if sys.version_info < (3, 8) and platform.system() == 'Windows':
        exe = str(exe)
    subprocess.check_call([exe], env=env)


class TestFinderTemplate:
    """This test focus in getting a particular implementation detail right.
    If at some point in time the implementation is changed for something different,
    this test can be modified or even excluded.
    """
    def install_finder(self, finder):
        loc = {}
        exec(finder, loc, loc)
        loc["install"]()

    def test_packages(self, tmp_path):
        files = {
            "src1": {
                "pkg1": {
                    "__init__.py": "",
                    "subpkg": {"mod1.py": "a = 42"},
                },
            },
            "src2": {"mod2.py": "a = 43"},
        }
        jaraco.path.build(files, prefix=tmp_path)

        mapping = {
            "pkg1": str(tmp_path / "src1/pkg1"),
            "mod2": str(tmp_path / "src2/mod2")
        }
        template = _finder_template(str(uuid4()), mapping, {})

        with contexts.save_paths(), contexts.save_sys_modules():
            for mod in ("pkg1", "pkg1.subpkg", "pkg1.subpkg.mod1", "mod2"):
                sys.modules.pop(mod, None)

            self.install_finder(template)
            mod1 = import_module("pkg1.subpkg.mod1")
            mod2 = import_module("mod2")
            subpkg = import_module("pkg1.subpkg")

            assert mod1.a == 42
            assert mod2.a == 43
            expected = str((tmp_path / "src1/pkg1/subpkg").resolve())
            assert_path(subpkg, expected)

    def test_namespace(self, tmp_path):
        files = {"pkg": {"__init__.py": "a = 13", "text.txt": "abc"}}
        jaraco.path.build(files, prefix=tmp_path)

        mapping = {"ns.othername": str(tmp_path / "pkg")}
        namespaces = {"ns": []}

        template = _finder_template(str(uuid4()), mapping, namespaces)
        with contexts.save_paths(), contexts.save_sys_modules():
            for mod in ("ns", "ns.othername"):
                sys.modules.pop(mod, None)

            self.install_finder(template)
            pkg = import_module("ns.othername")
            text = importlib_resources.files(pkg) / "text.txt"

            expected = str((tmp_path / "pkg").resolve())
            assert_path(pkg, expected)
            assert pkg.a == 13

            # Make sure resources can also be found
            assert text.read_text(encoding="utf-8") == "abc"

    def test_combine_namespaces(self, tmp_path):
        files = {
            "src1": {"ns": {"pkg1": {"__init__.py": "a = 13"}}},
            "src2": {"ns": {"mod2.py": "b = 37"}},
        }
        jaraco.path.build(files, prefix=tmp_path)

        mapping = {
            "ns.pkgA": str(tmp_path / "src1/ns/pkg1"),
            "ns": str(tmp_path / "src2/ns"),
        }
        namespaces_ = {"ns": [str(tmp_path / "src1"), str(tmp_path / "src2")]}
        template = _finder_template(str(uuid4()), mapping, namespaces_)

        with contexts.save_paths(), contexts.save_sys_modules():
            for mod in ("ns", "ns.pkgA", "ns.mod2"):
                sys.modules.pop(mod, None)

            self.install_finder(template)
            pkgA = import_module("ns.pkgA")
            mod2 = import_module("ns.mod2")

            expected = str((tmp_path / "src1/ns/pkg1").resolve())
            assert_path(pkgA, expected)
            assert pkgA.a == 13
            assert mod2.b == 37

    def test_dynamic_path_computation(self, tmp_path):
        # Follows the example in PEP 420
        files = {
            "project1": {"parent": {"child": {"one.py": "x = 1"}}},
            "project2": {"parent": {"child": {"two.py": "x = 2"}}},
            "project3": {"parent": {"child": {"three.py": "x = 3"}}},
        }
        jaraco.path.build(files, prefix=tmp_path)
        mapping = {}
        namespaces_ = {"parent": [str(tmp_path / "project1/parent")]}
        template = _finder_template(str(uuid4()), mapping, namespaces_)

        mods = (f"parent.child.{name}" for name in ("one", "two", "three"))
        with contexts.save_paths(), contexts.save_sys_modules():
            for mod in ("parent", "parent.child", "parent.child", *mods):
                sys.modules.pop(mod, None)

            self.install_finder(template)

            one = import_module("parent.child.one")
            assert one.x == 1

            with pytest.raises(ImportError):
                import_module("parent.child.two")

            sys.path.append(str(tmp_path / "project2"))
            two = import_module("parent.child.two")
            assert two.x == 2

            with pytest.raises(ImportError):
                import_module("parent.child.three")

            sys.path.append(str(tmp_path / "project3"))
            three = import_module("parent.child.three")
            assert three.x == 3


def test_pkg_roots(tmp_path):
    """This test focus in getting a particular implementation detail right.
    If at some point in time the implementation is changed for something different,
    this test can be modified or even excluded.
    """
    files = {
        "a": {"b": {"__init__.py": "ab = 1"}, "__init__.py": "a = 1"},
        "d": {"__init__.py": "d = 1", "e": {"__init__.py": "de = 1"}},
        "f": {"g": {"h": {"__init__.py": "fgh = 1"}}},
        "other": {"__init__.py": "abc = 1"},
        "another": {"__init__.py": "abcxyz = 1"},
        "yet_another": {"__init__.py": "mnopq = 1"},
    }
    jaraco.path.build(files, prefix=tmp_path)
    package_dir = {
        "a.b.c": "other",
        "a.b.c.x.y.z": "another",
        "m.n.o.p.q": "yet_another"
    }
    packages = [
        "a",
        "a.b",
        "a.b.c",
        "a.b.c.x.y",
        "a.b.c.x.y.z",
        "d",
        "d.e",
        "f",
        "f.g",
        "f.g.h",
        "m.n.o.p.q",
    ]
    roots = _find_package_roots(packages, package_dir, tmp_path)
    assert roots == {
        "a": str(tmp_path / "a"),
        "a.b.c": str(tmp_path / "other"),
        "a.b.c.x.y.z": str(tmp_path / "another"),
        "d": str(tmp_path / "d"),
        "f": str(tmp_path / "f"),
        "m.n.o.p.q": str(tmp_path / "yet_another"),
    }

    ns = set(dict(_find_namespaces(packages, roots)))
    assert ns == {"f", "f.g"}

    ns = set(_find_virtual_namespaces(roots))
    assert ns == {"a.b.c.x", "a.b.c.x.y", "m", "m.n", "m.n.o", "m.n.o.p"}


class TestOverallBehaviour:
    PYPROJECT = """\
        [build-system]
        requires = ["setuptools"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "mypkg"
        version = "3.14159"
        """

    FLAT_LAYOUT = {
        "pyproject.toml": dedent(PYPROJECT),
        "MANIFEST.in": EXAMPLE["MANIFEST.in"],
        "otherfile.py": "",
        "mypkg": {
            "__init__.py": "",
            "mod1.py": "var = 42",
            "subpackage": {
                "__init__.py": "",
                "mod2.py": "var = 13",
                "resource_file.txt": "resource 39",
            },
        },
    }

    EXAMPLES = {
        "flat-layout": FLAT_LAYOUT,
        "src-layout": {
            "pyproject.toml": dedent(PYPROJECT),
            "MANIFEST.in": EXAMPLE["MANIFEST.in"],
            "otherfile.py": "",
            "src": {"mypkg": FLAT_LAYOUT["mypkg"]},
        },
        "custom-layout": {
            "pyproject.toml": dedent(PYPROJECT) + dedent("""\
                [tool.setuptools]
                packages = ["mypkg", "mypkg.subpackage"]

                [tool.setuptools.package-dir]
                "mypkg.subpackage" = "other"
                """),
            "MANIFEST.in": EXAMPLE["MANIFEST.in"],
            "otherfile.py": "",
            "mypkg": {
                "__init__.py": "",
                "mod1.py": FLAT_LAYOUT["mypkg"]["mod1.py"],  # type: ignore
            },
            "other": FLAT_LAYOUT["mypkg"]["subpackage"],  # type: ignore
        },
        "namespace": {
            "pyproject.toml": dedent(PYPROJECT),
            "MANIFEST.in": EXAMPLE["MANIFEST.in"],
            "otherfile.py": "",
            "src": {
                "mypkg": {
                    "mod1.py": FLAT_LAYOUT["mypkg"]["mod1.py"],  # type: ignore
                    "subpackage": FLAT_LAYOUT["mypkg"]["subpackage"],  # type: ignore
                },
            },
        },
    }

    @pytest.mark.parametrize("layout", EXAMPLES.keys())
    def test_editable_install(self, tmp_path, venv, layout, editable_mode):
        project = install_project("mypkg", venv, tmp_path, self.EXAMPLES[layout])

        # Ensure stray files are not importable
        cmd_import_error = """\
        try:
            import otherfile
        except ImportError as ex:
            print(ex)
        """
        out = venv.run(["python", "-c", dedent(cmd_import_error)])
        assert b"No module named 'otherfile'" in out

        # Ensure the modules are importable
        cmd_get_vars = """\
        import mypkg, mypkg.mod1, mypkg.subpackage.mod2
        print(mypkg.mod1.var, mypkg.subpackage.mod2.var)
        """
        out = venv.run(["python", "-c", dedent(cmd_get_vars)])
        assert b"42 13" in out

        # Ensure resources are reachable
        cmd_get_resource = """\
        import mypkg.subpackage
        from setuptools._importlib import resources as importlib_resources
        text = importlib_resources.files(mypkg.subpackage) / "resource_file.txt"
        print(text.read_text(encoding="utf-8"))
        """
        out = venv.run(["python", "-c", dedent(cmd_get_resource)])
        assert b"resource 39" in out

        # Ensure files are editable
        mod1 = next(project.glob("**/mod1.py"))
        mod2 = next(project.glob("**/mod2.py"))
        resource_file = next(project.glob("**/resource_file.txt"))

        mod1.write_text("var = 17", encoding="utf-8")
        mod2.write_text("var = 781", encoding="utf-8")
        resource_file.write_text("resource 374", encoding="utf-8")

        out = venv.run(["python", "-c", dedent(cmd_get_vars)])
        assert b"42 13" not in out
        assert b"17 781" in out

        out = venv.run(["python", "-c", dedent(cmd_get_resource)])
        assert b"resource 39" not in out
        assert b"resource 374" in out


class TestLinkTree:
    FILES = deepcopy(TestOverallBehaviour.EXAMPLES["src-layout"])
    FILES["pyproject.toml"] += dedent("""\
        [tool.setuptools]
        # Temporary workaround: both `include-package-data` and `package-data` configs
        # can be removed after #3260 is fixed.
        include-package-data = false
        package-data = {"*" = ["*.txt"]}

        [tool.setuptools.packages.find]
        where = ["src"]
        exclude = ["*.subpackage*"]
        """)
    FILES["src"]["mypkg"]["resource.not_in_manifest"] = "abc"

    def test_generated_tree(self, tmp_path):
        jaraco.path.build(self.FILES, prefix=tmp_path)

        with _Path(tmp_path):
            name = "mypkg-3.14159"
            dist = Distribution({"script_name": "%PEP 517%"})
            dist.parse_config_files()

            wheel = Mock()
            aux = tmp_path / ".aux"
            build = tmp_path / ".build"
            aux.mkdir()
            build.mkdir()

            build_py = dist.get_command_obj("build_py")
            build_py.editable_mode = True
            build_py.build_lib = str(build)
            build_py.ensure_finalized()
            outputs = build_py.get_outputs()
            output_mapping = build_py.get_output_mapping()

            make_tree = _LinkTree(dist, name, aux, build)
            make_tree(wheel, outputs, output_mapping)

            mod1 = next(aux.glob("**/mod1.py"))
            expected = tmp_path / "src/mypkg/mod1.py"
            assert_link_to(mod1, expected)

            assert next(aux.glob("**/subpackage"), None) is None
            assert next(aux.glob("**/mod2.py"), None) is None
            assert next(aux.glob("**/resource_file.txt"), None) is None

            assert next(aux.glob("**/resource.not_in_manifest"), None) is None

    def test_strict_install(self, tmp_path, venv, monkeypatch):
        monkeypatch.setenv("SETUPTOOLS_EDITABLE", "strict")
        install_project("mypkg", venv, tmp_path, self.FILES)

        out = venv.run(["python", "-c", "import mypkg.mod1; print(mypkg.mod1.var)"])
        assert b"42" in out

        # Ensure packages excluded from distribution are not importable
        cmd_import_error = """\
        try:
            from mypkg import subpackage
        except ImportError as ex:
            print(ex)
        """
        out = venv.run(["python", "-c", dedent(cmd_import_error)])
        assert b"cannot import name 'subpackage'" in out

        # Ensure resource files excluded from distribution are not reachable
        cmd_get_resource = """\
        import mypkg
        from setuptools._importlib import resources as importlib_resources
        try:
            text = importlib_resources.files(mypkg) / "resource.not_in_manifest"
            print(text.read_text(encoding="utf-8"))
        except FileNotFoundError as ex:
            print(ex)
        """
        out = venv.run(["python", "-c", dedent(cmd_get_resource)])
        assert b"No such file or directory" in out
        assert b"resource.not_in_manifest" in out


def install_project(name, venv, tmp_path, files):
    project = tmp_path / name
    project.mkdir()
    jaraco.path.build(files, prefix=project)
    opts = ["--no-build-isolation"]  # force current version of setuptools
    venv.run(["python", "-m", "pip", "install", "-e", str(project), *opts])
    return project


# ---- Assertion Helpers ----


def assert_path(pkg, expected):
    # __path__ is not guaranteed to exist, so we have to account for that
    if pkg.__path__:
        path = next(iter(pkg.__path__), None)
        if path:
            assert str(Path(path).resolve()) == expected


def assert_link_to(file: Path, other: Path):
    if file.is_symlink():
        assert str(file.resolve()) == str(other.resolve())
    else:
        file_stat = file.stat()
        other_stat = other.stat()
        assert file_stat[stat.ST_INO] == other_stat[stat.ST_INO]
        assert file_stat[stat.ST_DEV] == other_stat[stat.ST_DEV]
