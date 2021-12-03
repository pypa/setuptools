import os

from setuptools.config.pyprojecttoml import read_configuration, expand_configuration

EXAMPLE = """
[project]
name = "myproj"
keywords = ["some", "key", "words"]
dynamic = ["version", "readme"]
requires-python = ">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*"
dependencies = [
    'importlib-metadata>=0.12;python_version<"3.8"',
    'importlib-resources>=1.0;python_version<"3.7"',
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

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true

[tool.setuptools.cmdclass]
sdist = "pkg.mod.CustomSdist"

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


def test_read_configuration(tmp_path):
    pyproject = tmp_path / "pyproject.toml"

    files = [
        "src/pkg/__init__.py",
        "src/other/nested/__init__.py",
        "files/file.txt"
    ]
    for file in files:
        (tmp_path / file).parent.mkdir(exist_ok=True, parents=True)
        (tmp_path / file).touch()

    pyproject.write_text(EXAMPLE)
    (tmp_path / "README.md").write_text("hello world")
    (tmp_path / "src/pkg/mod.py").write_text("class CustomSdist: pass")
    (tmp_path / "src/pkg/__version__.py").write_text("VERSION = (3, 10)")
    (tmp_path / "src/pkg/__main__.py").write_text("def exec(): print('hello')")

    config = read_configuration(pyproject, expand=False)
    assert config["project"].get("version") is None
    assert config["project"].get("readme") is None

    expanded = expand_configuration(config, tmp_path)
    assert read_configuration(pyproject, expand=True) == expanded
    assert expanded["project"]["version"] == "3.10"
    assert expanded["project"]["readme"]["text"] == "hello world"
    assert set(expanded["tool"]["setuptools"]["packages"]) == {
        "pkg",
        "other",
        "other.nested",
    }
    assert "" in expanded["tool"]["setuptools"]["package-data"]
    assert "*" not in expanded["tool"]["setuptools"]["package-data"]
    assert expanded["tool"]["setuptools"]["data-files"] == [
        ("data", ["files/file.txt"])
    ]
