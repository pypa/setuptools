from configparser import ConfigParser

import pytest

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
    expanded_project = expanded["project"]
    assert read_configuration(pyproject, expand=True) == expanded
    assert expanded_project["version"] == "3.10"
    assert expanded_project["readme"]["text"] == "hello world"
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


ENTRY_POINTS = {
    "console_scripts": {"a": "mod.a:func"},
    "gui_scripts": {"b": "mod.b:func"},
    "other": {"c": "mod.c:func [extra]"},
}


def test_expand_entry_point(tmp_path):
    entry_points = ConfigParser()
    entry_points.read_dict(ENTRY_POINTS)
    with open(tmp_path / "entry-points.txt", "w") as f:
        entry_points.write(f)

    tool = {"setuptools": {"dynamic": {"entry-points": {"file": "entry-points.txt"}}}}
    project = {"dynamic": ["scripts", "gui-scripts", "entry-points"]}
    pyproject = {"project": project, "tool": tool}
    expanded = expand_configuration(pyproject, tmp_path)
    expanded_project = expanded["project"]
    assert len(expanded_project["scripts"]) == 1
    assert expanded_project["scripts"]["a"] == "mod.a:func"
    assert len(expanded_project["gui-scripts"]) == 1
    assert expanded_project["gui-scripts"]["b"] == "mod.b:func"
    assert len(expanded_project["entry-points"]) == 1
    assert expanded_project["entry-points"]["other"]["c"] == "mod.c:func [extra]"

    project = {"dynamic": ["entry-points"]}
    pyproject = {"project": project, "tool": tool}
    expanded = expand_configuration(pyproject, tmp_path)
    expanded_project = expanded["project"]
    assert len(expanded_project["entry-points"]) == 3
    assert "scripts" not in expanded_project
    assert "gui-scripts" not in expanded_project


EXAMPLE_INVALID_3RD_PARTY_CONFIG = """
[project]
name = "myproj"
version = "1.2"

[my-tool.that-disrespect.pep518]
value = 42
"""


def test_ignore_unrelated_config(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(EXAMPLE_INVALID_3RD_PARTY_CONFIG)

    # Make sure no error is raised due to 3rd party configs in pyproject.toml
    assert read_configuration(pyproject) is not None


@pytest.mark.parametrize("config", ("", "[tool.something]\nvalue = 42"))
def test_empty(tmp_path, config):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(config)

    # Make sure no error is raised
    assert read_configuration(pyproject) == {}
