import logging
from configparser import ConfigParser
from inspect import cleandoc

import pytest
import tomli_w

from setuptools.config.pyprojecttoml import (
    read_configuration,
    expand_configuration,
    validate,
)

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
"data" = ["_files/*.txt"]

[tool.distutils.sdist]
formats = "gztar"

[tool.distutils.bdist_wheel]
universal = true
"""


def create_example(path, pkg_root):
    pyproject = path / "pyproject.toml"

    files = [
        f"{pkg_root}/pkg/__init__.py",
        "_files/file.txt",
    ]
    if pkg_root != ".":  # flat-layout will raise error for multi-package dist
        # Ensure namespaces are discovered
        files.append(f"{pkg_root}/other/nested/__init__.py")

    for file in files:
        (path / file).parent.mkdir(exist_ok=True, parents=True)
        (path / file).touch()

    pyproject.write_text(EXAMPLE)
    (path / "README.md").write_text("hello world")
    (path / f"{pkg_root}/pkg/mod.py").write_text("class CustomSdist: pass")
    (path / f"{pkg_root}/pkg/__version__.py").write_text("VERSION = (3, 10)")
    (path / f"{pkg_root}/pkg/__main__.py").write_text("def exec(): print('hello')")


def verify_example(config, path, pkg_root):
    pyproject = path / "pyproject.toml"
    pyproject.write_text(tomli_w.dumps(config), encoding="utf-8")
    expanded = expand_configuration(config, path)
    expanded_project = expanded["project"]
    assert read_configuration(pyproject, expand=True) == expanded
    assert expanded_project["version"] == "3.10"
    assert expanded_project["readme"]["text"] == "hello world"
    assert "packages" in expanded["tool"]["setuptools"]
    if pkg_root == ".":
        # Auto-discovery will raise error for multi-package dist
        assert set(expanded["tool"]["setuptools"]["packages"]) == {"pkg"}
    else:
        assert set(expanded["tool"]["setuptools"]["packages"]) == {
            "pkg",
            "other",
            "other.nested",
        }
    assert expanded["tool"]["setuptools"]["include-package-data"] is True
    assert "" in expanded["tool"]["setuptools"]["package-data"]
    assert "*" not in expanded["tool"]["setuptools"]["package-data"]
    assert expanded["tool"]["setuptools"]["data-files"] == [
        ("data", ["_files/file.txt"])
    ]


def test_read_configuration(tmp_path):
    create_example(tmp_path, "src")
    pyproject = tmp_path / "pyproject.toml"

    config = read_configuration(pyproject, expand=False)
    assert config["project"].get("version") is None
    assert config["project"].get("readme") is None

    verify_example(config, tmp_path, "src")


@pytest.mark.parametrize(
    "pkg_root, opts",
    [
        (".", {}),
        ("src", {}),
        ("lib", {"packages": {"find": {"where": ["lib"]}}}),
    ],
)
def test_discovered_package_dir_with_attr_directive_in_config(tmp_path, pkg_root, opts):
    create_example(tmp_path, pkg_root)

    pyproject = tmp_path / "pyproject.toml"

    config = read_configuration(pyproject, expand=False)
    assert config["project"].get("version") is None
    assert config["project"].get("readme") is None
    config["tool"]["setuptools"].pop("packages", None)
    config["tool"]["setuptools"].pop("package-dir", None)

    config["tool"]["setuptools"].update(opts)
    verify_example(config, tmp_path, pkg_root)


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


def test_dynamic_classifiers(tmp_path):
    # Let's create a project example that has dynamic classifiers
    # coming from a txt file.
    create_example(tmp_path, "src")
    classifiers = """\
    Framework :: Flask
    Programming Language :: Haskell
    """
    (tmp_path / "classifiers.txt").write_text(cleandoc(classifiers))

    pyproject = tmp_path / "pyproject.toml"
    config = read_configuration(pyproject, expand=False)
    dynamic = config["project"]["dynamic"]
    config["project"]["dynamic"] = list({*dynamic, "classifiers"})
    dynamic_config = config["tool"]["setuptools"]["dynamic"]
    dynamic_config["classifiers"] = {"file": "classifiers.txt"}

    # When the configuration is expanded,
    # each line of the file should be an different classifier.
    validate(config, pyproject)
    expanded = expand_configuration(config, tmp_path)

    assert set(expanded["project"]["classifiers"]) == {
        "Framework :: Flask",
        "Programming Language :: Haskell",
    }


@pytest.mark.parametrize(
    "example",
    (
        """
        [project]
        name = "myproj"
        version = "1.2"

        [my-tool.that-disrespect.pep518]
        value = 42
        """,
    ),
)
def test_ignore_unrelated_config(tmp_path, example):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(cleandoc(example))

    # Make sure no error is raised due to 3rd party configs in pyproject.toml
    assert read_configuration(pyproject) is not None


@pytest.mark.parametrize(
    "example, error_msg, value_shown_in_debug",
    [
        (
            """
            [project]
            name = "myproj"
            version = "1.2"
            requires = ['pywin32; platform_system=="Windows"' ]
            """,
            "configuration error: `project` must not contain {'requires'} properties",
            '"requires": ["pywin32; platform_system==\\"Windows\\""]',
        ),
    ],
)
def test_invalid_example(tmp_path, caplog, example, error_msg, value_shown_in_debug):
    caplog.set_level(logging.DEBUG)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(cleandoc(example))

    caplog.clear()
    with pytest.raises(ValueError, match="invalid pyproject.toml"):
        read_configuration(pyproject)

    # Make sure the logs give guidance to the user
    error_log = caplog.record_tuples[0]
    assert error_log[1] == logging.ERROR
    assert error_msg in error_log[2]

    debug_log = caplog.record_tuples[1]
    assert debug_log[1] == logging.DEBUG
    debug_msg = "".join(line.strip() for line in debug_log[2].splitlines())
    assert value_shown_in_debug in debug_msg


@pytest.mark.parametrize("config", ("", "[tool.something]\nvalue = 42"))
def test_empty(tmp_path, config):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(config)

    # Make sure no error is raised
    assert read_configuration(pyproject) == {}


@pytest.mark.parametrize("config", ("[project]\nname = 'myproj'\nversion='42'\n",))
def test_include_package_data_by_default(tmp_path, config):
    """Builds with ``pyproject.toml`` should consider ``include-package-data=True`` as
    default.
    """
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(config)

    config = read_configuration(pyproject)
    assert config["tool"]["setuptools"]["include-package-data"] is True
