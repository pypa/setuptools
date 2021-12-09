from configparser import ConfigParser
from unittest.mock import Mock

from setuptools import options
from setuptools.config.pyprojecttoml import read_configuration
from setuptools.dist import Distribution

EXAMPLE = """
[project]
name = "myproj"
keywords = ["some", "key", "words"]
dynamic = ["version", "readme", "license"]
requires-python = ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*"
dependencies = [
    'importlib_metadata>=0.12;python_version<"3.8"',
    'importlib_resources>=1.0;python_version<"3.7"',
    'pathlib2>=2.3.3,<3;python_version < "3.4" and sys.platform != "win32"',
]

[project.optional-dependencies]
docs = [
    "sphinx>=3",
    "sphinx-argparse>=0.2.5",
    "sphinx-rtd-theme>=0.4.3",
]
testing = [
    "pytest>=1",
    "coverage>=3,<5",
]

[project.scripts]
exec = "pkg.__main__:exec"

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}
zip-safe = true
platforms = ["any"]
include-package-data = true

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true

[tool.setuptools.cmdclass]
sdist = "pkg.mod.CustomSdist"

[tool.setuptools.dynamic]
license = "MIT"
license-files = ["LICENSE.txt"]

[tool.setuptools.dynamic.version]
attr = "pkg.__version__.VERSION"

[tool.setuptools.dynamic.readme]
file = ["README.md"]
content-type = "text/markdown"

[tool.setuptools.package-data]
"*" = ["*.txt"]

[tool.setuptools.data-files]
"data" = ["files/*.txt"]

[tool.distutils.sdist]
formats = "gztar"

[tool.distutils.bdist_wheel]
universal = true
"""


ENTRY_POINTS = {
    "console_scripts": {"a": "mod.a:func"},
    "gui_scripts": {"b": "mod.b:func"},
    "other": {"c": "mod.c:func [extra]"},
}


def _project_files(root_dir):
    pyproject = root_dir / "pyproject.toml"

    files = ["src/pkg/__init__.py", "src/other/nested/__init__.py", "files/file.txt"]
    for file in files:
        (root_dir / file).parent.mkdir(exist_ok=True, parents=True)
        (root_dir / file).touch()

    pyproject.write_text(EXAMPLE)
    (root_dir / "README.md").write_text("hello world")
    (root_dir / "src/pkg/mod.py").write_text("class CustomSdist: pass")
    (root_dir / "src/pkg/__version__.py").write_text("VERSION = (3, 10)")
    (root_dir / "src/pkg/__main__.py").write_text("def exec(): print('hello')")

    entry_points = ConfigParser()
    entry_points.read_dict(ENTRY_POINTS)
    with open(root_dir / "entry-points.txt", "w") as f:
        entry_points.write(f)


EXPECTED_OPTIONS = {
    "zip_safe": True,
    "include_package_data": True,
    "package_dir": {"": "src"},
    "packages": ["pkg", "other", "other.nested"],
    "package_data": {"": ["*.txt"]},
    "data_files": [("data", ["files/file.txt"])],
    "cmdclass": {"sdist": Mock(__qualname__="pkg.mod.CustomSdist")},
    "entry_points": {"console_scripts": ["exec = pkg.__main__:exec"]},
    "command_options": {
        "sdist": {"formats": "gztar"},
        "bdist_wheel": {"universal": True},
    }
}


def test_from_pyproject(tmp_path):
    _project_files(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    opts = options.from_pyproject(read_configuration(pyproject), root_dir=tmp_path)
    cmp = options.compare(opts, EXPECTED_OPTIONS)
    if cmp is not True:
        print("cmp:", cmp)
        assert opts == EXPECTED_OPTIONS  # just so pytest will print the diff


def test_apply(tmp_path):
    _project_files(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    opts = options.from_pyproject(read_configuration(pyproject), root_dir=tmp_path)
    dist = Distribution({})
    options.apply(opts, dist)
    assert dist.zip_safe is True
    assert dist.include_package_data is True
    assert set(dist.data_files[0][1]) == {"files/file.txt"}
    cls = dist.cmdclass["sdist"]
    assert f"{cls.__module__}.{cls.__name__}" == "pkg.mod.CustomSdist"
    assert set(dist.entry_points["console_scripts"]) == {"exec = pkg.__main__:exec"}
    assert dist.command_options["sdist"]["formats"] == ("pyproject.toml", "gztar")
    assert dist.command_options["bdist_wheel"]["universal"] == ("pyproject.toml", True)

    reconstructed = options.from_dist(dist)
    cmp = options.compare(opts, reconstructed)
    if cmp is not True:
        print("cmp:", cmp)
        assert opts == reconstructed  # just so pytest will print the diff
