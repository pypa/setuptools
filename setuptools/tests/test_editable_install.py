import os
import sys
import subprocess
import platform
from importlib import import_module
from pathlib import Path
from textwrap import dedent

import jaraco.envs
import jaraco.path
import pip_run.launch
import pytest

from . import contexts, namespaces

from setuptools._importlib import resources as importlib_resources
from setuptools.command.editable_wheel import (
    _finder_template,
    _find_pkg_roots,
    _find_mapped_namespaces,
)


EXAMPLE = {
    'pyproject.toml': dedent("""\
        [build-system]
        requires = ["setuptools", "wheel"]
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
        {**EXAMPLE, "setup.py": SETUP_SCRIPT_STUB},
        EXAMPLE,  # No setup.py script
    ]
)
def test_editable_with_pyproject(tmp_path, venv, files):
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


class TestLegacyNamespaces:
    """Ported from test_develop"""

    def test_namespace_package_importable(self, venv, tmp_path):
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

    def test_namespace_package_importable(self, venv, tmp_path):
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

    def test_namespace_created_via_package_dir(self, venv, tmp_path):
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
def test_editable_with_prefix(tmp_path, sample_project):
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

    env = dict(os.environ, PYTHONPATH=str(site_packages))
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
        template = _finder_template(mapping, {})

        with contexts.save_paths():
            self.install_finder(template)
            mod1 = import_module("pkg1.subpkg.mod1")
            mod2 = import_module("mod2")
            subpkg = import_module("pkg1.subpkg")

        assert mod1.a == 42
        assert mod2.a == 43
        assert Path(subpkg.__path__[0]) == tmp_path / "src1/pkg1/subpkg"

    def test_namespace(self, tmp_path):
        files = {"pkg": {"__init__.py": "a = 13", "text.txt": "abc"}}
        jaraco.path.build(files, prefix=tmp_path)

        mapping = {"ns.othername": str(tmp_path / "pkg")}
        namespaces = {"ns"}

        template = _finder_template(mapping, namespaces)
        with contexts.save_paths():
            self.install_finder(template)
            pkg = import_module("ns.othername")
            text = importlib_resources.files(pkg) / "text.txt"

        expected = str((tmp_path / "pkg").resolve())
        assert str(Path(pkg.__path__[0]).resolve()) == expected
        assert pkg.a == 13

        # Make sure resources can also be found
        assert text.read_text(encoding="utf-8") == "abc"

    def test_combine_namespaces(self, tmp_path, monkeypatch):
        files = {
            "src1": {"ns": {"pkg1": {"__init__.py": "a = 13"}}},
            "src2": {"ns": {"mod2.py": "b = 37"}},
        }
        jaraco.path.build(files, prefix=tmp_path)

        mapping = {
            "ns.pkgA": str(tmp_path / "src1/ns/pkg1"),
            "ns": str(tmp_path / "src2/ns"),
        }
        template = _finder_template(mapping, {})

        with contexts.save_paths():
            self.install_finder(template)
            pkgA = import_module("ns.pkgA")
            mod2 = import_module("ns.mod2")

        expected = str((tmp_path / "src1/ns/pkg1").resolve())
        assert str(Path(pkgA.__path__[0]).resolve()) == expected
        assert pkgA.a == 13
        assert mod2.b == 37


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
        "another": {"__init__.py": "abcxy = 1"},
    }
    jaraco.path.build(files, prefix=tmp_path)
    package_dir = {"a.b.c": "other", "a.b.c.x.y": "another"}
    packages = ["a", "a.b", "a.b.c", "a.b.c.x.y", "d", "d.e", "f", "f.g", "f.g.h"]
    roots = _find_pkg_roots(packages, package_dir, tmp_path)
    assert roots == {
        "a": str(tmp_path / "a"),
        "a.b.c": str(tmp_path / "other"),
        "a.b.c.x.y": str(tmp_path / "another"),
        "d": str(tmp_path / "d"),
        "f": str(tmp_path / "f"),
    }

    namespaces = set(_find_mapped_namespaces(roots))
    assert namespaces == {"a.b.c.x"}
