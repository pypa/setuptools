import subprocess
from textwrap import dedent

import pytest
import jaraco.envs
import path


@pytest.fixture
def venv(tmp_path, setuptools_wheel):
    env = jaraco.envs.VirtualEnv()
    vars(env).update(
        root=path.Path(tmp_path),  # workaround for error on windows
        name=".venv",
        create_opts=["--no-setuptools"],
        req=str(setuptools_wheel),
    )
    return env.create()


EXAMPLE = {
    'pyproject.toml': dedent("""\
        [build-system]
        requires = ["setuptools", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "mypkg"
        version = "3.14159"
        description = "This is a Python package"
        dynamic = ["license", "readme"]
        classifiers = [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers"
        ]
        urls = {Homepage = "http://github.com"}
        dependencies = ['importlib-metadata; python_version<"3.8"']

        [tool.setuptools]
        package-dir = {"" = "src"}
        packages = {find = {where = ["src"]}}

        [tool.setuptools.dynamic]
        license = "MIT"
        license_files = ["LICENSE*"]
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
MISSING_SETUP_SCRIPT = pytest.param(
    None,
    marks=pytest.mark.xfail(
        reason="Editable install is currently only supported with `setup.py`"
    )
)


@pytest.mark.parametrize("setup_script", [SETUP_SCRIPT_STUB, MISSING_SETUP_SCRIPT])
def test_editable_with_pyproject(tmp_path, venv, setup_script):
    project = tmp_path / "mypkg"
    files = {**EXAMPLE, "setup.py": setup_script}
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
