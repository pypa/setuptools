import os
import sys
import subprocess
import platform
import pathlib
from textwrap import dedent

import jaraco.envs
import jaraco.path
import pip_run.launch
import pytest

from . import namespaces

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
        venv.run(["python", "-m", "pip", "install", str(pkg_A)])
        venv.run(["python", "-m", "pip", "install", "-e", str(pkg_B)])
        venv.run(["python", "-c", "import myns.pkgA; import myns.pkgB"])
        # additionally ensure that pkg_resources import works
        venv.run(["python", "-c", "import pkg_resources"])


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
        pathlib.Path(path).relative_to(sys.prefix)
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
