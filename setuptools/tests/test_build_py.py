import importlib
import os
import shutil
import stat
import warnings
from pathlib import Path
from unittest.mock import Mock

import jaraco.path
import pytest

from setuptools import SetuptoolsDeprecationWarning
from setuptools.command.build_py import (
    _contains_python_sources,
    _find_package_data_owner,
    _find_packages_exclude_patterns,
    _IncludePackageDataAbuse,
    _is_explicitly_excluded,
    _split_find_excludes,
)
from setuptools.dist import Distribution

from .textwrap import DALS


def test_directories_in_package_data_glob(tmpdir_cwd):
    """
    Directories matching the glob in package_data should
    not be included in the package data.

    Regression test for #261.
    """
    dist = Distribution(
        dict(
            script_name='setup.py',
            script_args=['build_py'],
            packages=[''],
            package_data={'': ['path/*']},
        )
    )
    os.makedirs('path/subpath')
    dist.parse_command_line()
    dist.run_commands()


def test_recursive_in_package_data_glob(tmpdir_cwd):
    """
    Files matching recursive globs (**) in package_data should
    be included in the package data.

    #1806
    """
    dist = Distribution(
        dict(
            script_name='setup.py',
            script_args=['build_py'],
            packages=[''],
            package_data={'': ['path/**/data']},
        )
    )
    os.makedirs('path/subpath/subsubpath')
    open('path/subpath/subsubpath/data', 'wb').close()

    dist.parse_command_line()
    dist.run_commands()

    assert stat.S_ISREG(os.stat('build/lib/path/subpath/subsubpath/data').st_mode), (
        "File is not included"
    )


def test_read_only(tmpdir_cwd):
    """
    Ensure read-only flag is not preserved in copy
    for package modules and package data, as that
    causes problems with deleting read-only files on
    Windows.

    #1451
    """
    dist = Distribution(
        dict(
            script_name='setup.py',
            script_args=['build_py'],
            packages=['pkg'],
            package_data={'pkg': ['data.dat']},
        )
    )
    os.makedirs('pkg')
    open('pkg/__init__.py', 'wb').close()
    open('pkg/data.dat', 'wb').close()
    os.chmod('pkg/__init__.py', stat.S_IREAD)
    os.chmod('pkg/data.dat', stat.S_IREAD)
    dist.parse_command_line()
    dist.run_commands()
    shutil.rmtree('build')


@pytest.mark.xfail(
    'platform.system() == "Windows"',
    reason="On Windows, files do not have executable bits",
    raises=AssertionError,
    strict=True,
)
def test_executable_data(tmpdir_cwd):
    """
    Ensure executable bit is preserved in copy for
    package data, as users rely on it for scripts.

    #2041
    """
    dist = Distribution(
        dict(
            script_name='setup.py',
            script_args=['build_py'],
            packages=['pkg'],
            package_data={'pkg': ['run-me']},
        )
    )
    os.makedirs('pkg')
    open('pkg/__init__.py', 'wb').close()
    open('pkg/run-me', 'wb').close()
    os.chmod('pkg/run-me', 0o700)

    dist.parse_command_line()
    dist.run_commands()

    assert os.stat('build/lib/pkg/run-me').st_mode & stat.S_IEXEC, (
        "Script is not executable"
    )


EXAMPLE_WITH_MANIFEST = {
    "setup.cfg": DALS(
        """
        [metadata]
        name = mypkg
        version = 42

        [options]
        include_package_data = True
        packages = find:

        [options.packages.find]
        exclude = *.tests*
        """
    ),
    "mypkg": {
        "__init__.py": "",
        "resource_file.txt": "",
        "tests": {
            "__init__.py": "",
            "test_mypkg.py": "",
            "test_file.txt": "",
        },
    },
    "MANIFEST.in": DALS(
        """
        global-include *.py *.txt
        global-exclude *.py[cod]
        prune dist
        prune build
        prune *.egg-info
        """
    ),
}


EXAMPLE_WITH_SRC_LAYOUT_EXCLUDED_SUBPACKAGE = {
    "pyproject.toml": DALS(
        """
        [project]
        name = "mypkg"
        version = "42"

        [tool.setuptools]
        include-package-data = true

        [tool.setuptools.packages.find]
        where = ["src"]
        exclude = ["mypkg.subpkg", "mypkg.subpkg.*"]
        """
    ),
    "src": {
        "mypkg": {
            "__init__.py": "",
            "data.txt": "",
            "subpkg": {
                "sample1.json": "{}",
                "sample2.json": "{}",
            },
        },
    },
    "MANIFEST.in": DALS(
        """
        recursive-include src/mypkg *.txt
        recursive-include src/mypkg/subpkg *.json
        global-exclude *.py[cod]
        prune dist
        prune build
        prune *.egg-info
        """
    ),
}


EXAMPLE_WITH_IMPORTABLE_DATA_SUBPACKAGE = {
    "setup.cfg": DALS(
        """
        [metadata]
        name = mypkg
        version = 42

        [options]
        include_package_data = True
        packages = find:
        """
    ),
    "mypkg": {
        "__init__.py": "",
        "plugins": {
            "data.txt": "",
        },
    },
    "MANIFEST.in": DALS(
        """
        global-include *.txt
        global-exclude *.py[cod]
        prune dist
        prune build
        prune *.egg-info
        """
    ),
}


def test_excluded_subpackages(tmpdir_cwd):
    jaraco.path.build(EXAMPLE_WITH_MANIFEST)
    dist = Distribution({"script_name": "%PEP 517%"})
    dist.parse_config_files()

    build_py = dist.get_command_obj("build_py")
    build_py.finalize_options()
    build_py.run()

    build_dir = Path(dist.get_command_obj("build_py").build_lib)
    assert (build_dir / "mypkg/__init__.py").exists()
    assert (build_dir / "mypkg/resource_file.txt").exists()

    # Setuptools is configured to ignore `mypkg.tests`, therefore the following
    # files/dirs should not be included in the distribution.
    for f in [
        "mypkg/tests/__init__.py",
        "mypkg/tests/test_mypkg.py",
        "mypkg/tests/test_file.txt",
        "mypkg/tests",
    ]:
        assert not (build_dir / f).exists()


def test_excluded_subpackages_respect_pyproject_src_layout(tmpdir_cwd):
    jaraco.path.build(EXAMPLE_WITH_SRC_LAYOUT_EXCLUDED_SUBPACKAGE)
    dist = Distribution({"script_name": "%PEP 517%"})
    dist.parse_config_files()

    build_py = dist.get_command_obj("build_py")
    build_py.finalize_options()
    build_py.run()

    build_dir = Path(dist.get_command_obj("build_py").build_lib)
    assert (build_dir / "mypkg/__init__.py").exists()
    assert (build_dir / "mypkg/data.txt").exists()

    for f in [
        "mypkg/subpkg",
        "mypkg/subpkg/sample1.json",
        "mypkg/subpkg/sample2.json",
    ]:
        assert not (build_dir / f).exists()


def test_importable_data_subpackage_warns_and_includes_files(tmpdir_cwd):
    jaraco.path.build(EXAMPLE_WITH_IMPORTABLE_DATA_SUBPACKAGE)
    dist = Distribution({"script_name": "%PEP 517%"})
    dist.parse_config_files()

    build_py = dist.get_command_obj("build_py")
    msg = r"Package 'mypkg\.plugins' is absent from the `packages` configuration\."
    build_py.finalize_options()

    def run_build_py():
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                "'encoding' argument not specified",
                module="distutils.text_file",
                # This warning is already fixed in pypa/distutils but not in stdlib
            )
            build_py.run()

    with pytest.warns(SetuptoolsDeprecationWarning, match=msg):
        run_build_py()

    build_dir = Path(dist.get_command_obj("build_py").build_lib)
    assert (build_dir / "mypkg/plugins/data.txt").exists()


@pytest.mark.filterwarnings("ignore::setuptools.SetuptoolsDeprecationWarning")
def test_existing_egg_info(tmpdir_cwd, monkeypatch):
    """When provided with the ``existing_egg_info_dir`` attribute, build_py should not
    attempt to run egg_info again.
    """
    # == Pre-condition ==
    # Generate an egg-info dir
    jaraco.path.build(EXAMPLE_WITH_MANIFEST)
    dist = Distribution({"script_name": "%PEP 517%"})
    dist.parse_config_files()
    assert dist.include_package_data

    egg_info = dist.get_command_obj("egg_info")
    dist.run_command("egg_info")
    egg_info_dir = next(Path(egg_info.egg_base).glob("*.egg-info"))
    assert egg_info_dir.is_dir()

    # == Setup ==
    build_py = dist.get_command_obj("build_py")
    build_py.finalize_options()
    egg_info = dist.get_command_obj("egg_info")
    egg_info_run = Mock(side_effect=egg_info.run)
    monkeypatch.setattr(egg_info, "run", egg_info_run)

    # == Remove caches ==
    # egg_info is called when build_py looks for data_files, which gets cached.
    # We need to ensure it is not cached yet, otherwise it may impact on the tests
    build_py.__dict__.pop('data_files', None)
    dist.reinitialize_command(egg_info)

    # == Sanity check ==
    # Ensure that if existing_egg_info is not given, build_py attempts to run egg_info
    build_py.existing_egg_info_dir = None
    build_py.run()
    egg_info_run.assert_called()

    # == Remove caches ==
    egg_info_run.reset_mock()
    build_py.__dict__.pop('data_files', None)
    dist.reinitialize_command(egg_info)

    # == Actual test ==
    # Ensure that if existing_egg_info_dir is given, egg_info doesn't run
    build_py.existing_egg_info_dir = egg_info_dir
    build_py.run()
    egg_info_run.assert_not_called()
    assert build_py.data_files

    # Make sure the list of outputs is actually OK
    outputs = map(lambda x: x.replace(os.sep, "/"), build_py.get_outputs())
    assert outputs
    example = str(Path(build_py.build_lib, "mypkg/__init__.py")).replace(os.sep, "/")
    assert example in outputs


EXAMPLE_ARBITRARY_MAPPING = {
    "pyproject.toml": DALS(
        """
        [project]
        name = "mypkg"
        version = "42"

        [tool.setuptools]
        packages = ["mypkg", "mypkg.sub1", "mypkg.sub2", "mypkg.sub2.nested"]

        [tool.setuptools.package-dir]
        "" = "src"
        "mypkg.sub2" = "src/mypkg/_sub2"
        "mypkg.sub2.nested" = "other"
        """
    ),
    "src": {
        "mypkg": {
            "__init__.py": "",
            "resource_file.txt": "",
            "sub1": {
                "__init__.py": "",
                "mod1.py": "",
            },
            "_sub2": {
                "mod2.py": "",
            },
        },
    },
    "other": {
        "__init__.py": "",
        "mod3.py": "",
    },
    "MANIFEST.in": DALS(
        """
        global-include *.py *.txt
        global-exclude *.py[cod]
        """
    ),
}


def test_get_outputs(tmpdir_cwd):
    jaraco.path.build(EXAMPLE_ARBITRARY_MAPPING)
    dist = Distribution({"script_name": "%test%"})
    dist.parse_config_files()

    build_py = dist.get_command_obj("build_py")
    build_py.editable_mode = True
    build_py.ensure_finalized()
    build_lib = build_py.build_lib.replace(os.sep, "/")
    outputs = {x.replace(os.sep, "/") for x in build_py.get_outputs()}
    assert outputs == {
        f"{build_lib}/mypkg/__init__.py",
        f"{build_lib}/mypkg/resource_file.txt",
        f"{build_lib}/mypkg/sub1/__init__.py",
        f"{build_lib}/mypkg/sub1/mod1.py",
        f"{build_lib}/mypkg/sub2/mod2.py",
        f"{build_lib}/mypkg/sub2/nested/__init__.py",
        f"{build_lib}/mypkg/sub2/nested/mod3.py",
    }
    mapping = {
        k.replace(os.sep, "/"): v.replace(os.sep, "/")
        for k, v in build_py.get_output_mapping().items()
    }
    assert mapping == {
        f"{build_lib}/mypkg/__init__.py": "src/mypkg/__init__.py",
        f"{build_lib}/mypkg/resource_file.txt": "src/mypkg/resource_file.txt",
        f"{build_lib}/mypkg/sub1/__init__.py": "src/mypkg/sub1/__init__.py",
        f"{build_lib}/mypkg/sub1/mod1.py": "src/mypkg/sub1/mod1.py",
        f"{build_lib}/mypkg/sub2/mod2.py": "src/mypkg/_sub2/mod2.py",
        f"{build_lib}/mypkg/sub2/nested/__init__.py": "other/__init__.py",
        f"{build_lib}/mypkg/sub2/nested/mod3.py": "other/mod3.py",
    }


class TestTypeInfoFiles:
    PYPROJECTS = {
        "default_pyproject": DALS(
            """
            [project]
            name = "foo"
            version = "1"
            """
        ),
        "dont_include_package_data": DALS(
            """
            [project]
            name = "foo"
            version = "1"

            [tool.setuptools]
            include-package-data = false
            """
        ),
        "exclude_type_info": DALS(
            """
            [project]
            name = "foo"
            version = "1"

            [tool.setuptools]
            include-package-data = false

            [tool.setuptools.exclude-package-data]
            "*" = ["py.typed", "*.pyi"]
            """
        ),
    }

    EXAMPLES = {
        "simple_namespace": {
            "directory_structure": {
                "foo": {
                    "bar.pyi": "",
                    "py.typed": "",
                    "__init__.py": "",
                }
            },
            "expected_type_files": {"foo/bar.pyi", "foo/py.typed"},
        },
        "nested_inside_namespace": {
            "directory_structure": {
                "foo": {
                    "bar": {
                        "py.typed": "",
                        "mod.pyi": "",
                    }
                }
            },
            "expected_type_files": {"foo/bar/mod.pyi", "foo/bar/py.typed"},
        },
        "namespace_nested_inside_regular": {
            "directory_structure": {
                "foo": {
                    "namespace": {
                        "foo.pyi": "",
                    },
                    "__init__.pyi": "",
                    "py.typed": "",
                }
            },
            "expected_type_files": {
                "foo/namespace/foo.pyi",
                "foo/__init__.pyi",
                "foo/py.typed",
            },
        },
    }

    @pytest.mark.parametrize(
        "pyproject",
        [
            "default_pyproject",
            pytest.param(
                "dont_include_package_data",
                marks=pytest.mark.xfail(reason="pypa/setuptools#4350"),
            ),
        ],
    )
    @pytest.mark.parametrize("example", EXAMPLES.keys())
    def test_type_files_included_by_default(self, tmpdir_cwd, pyproject, example):
        structure = {
            **self.EXAMPLES[example]["directory_structure"],
            "pyproject.toml": self.PYPROJECTS[pyproject],
        }
        expected_type_files = self.EXAMPLES[example]["expected_type_files"]
        jaraco.path.build(structure)

        build_py = get_finalized_build_py()
        outputs = get_outputs(build_py)
        assert expected_type_files <= outputs

    @pytest.mark.parametrize("pyproject", ["exclude_type_info"])
    @pytest.mark.parametrize("example", EXAMPLES.keys())
    def test_type_files_can_be_excluded(self, tmpdir_cwd, pyproject, example):
        structure = {
            **self.EXAMPLES[example]["directory_structure"],
            "pyproject.toml": self.PYPROJECTS[pyproject],
        }
        expected_type_files = self.EXAMPLES[example]["expected_type_files"]
        jaraco.path.build(structure)

        build_py = get_finalized_build_py()
        outputs = get_outputs(build_py)
        assert expected_type_files.isdisjoint(outputs)

    def test_stub_only_package(self, tmpdir_cwd):
        structure = {
            "pyproject.toml": DALS(
                """
                [project]
                name = "foo-stubs"
                version = "1"
                """
            ),
            "foo-stubs": {"__init__.pyi": "", "bar.pyi": ""},
        }
        expected_type_files = {"foo-stubs/__init__.pyi", "foo-stubs/bar.pyi"}
        jaraco.path.build(structure)

        build_py = get_finalized_build_py()
        outputs = get_outputs(build_py)
        assert expected_type_files <= outputs


def get_finalized_build_py(script_name="%build_py-test%"):
    dist = Distribution({"script_name": script_name})
    dist.parse_config_files()
    build_py = dist.get_command_obj("build_py")
    build_py.finalize_options()
    return build_py


def get_outputs(build_py):
    build_dir = Path(build_py.build_lib)
    return {
        os.path.relpath(x, build_dir).replace(os.sep, "/")
        for x in build_py.get_outputs()
    }


def test_build_py_module_reload():
    import setuptools.command.build_py as build_py_module

    importlib.reload(build_py_module)


def test_split_find_excludes_strips_blank_lines():
    assert _split_find_excludes("\nfoo\n  bar.*  \n\nbaz\n") == (
        "foo",
        "bar.*",
        "baz",
    )


def test_find_packages_exclude_patterns_prefers_setup_cfg(tmpdir_cwd):
    Path("pyproject.toml").write_text(
        DALS(
            """
            [tool.setuptools.packages.find]
            exclude = ["ignored"]
            """
        ),
        encoding="utf-8",
    )
    dist = Distribution()
    dist.command_options = {
        "options.packages.find": {"exclude": ("setup.cfg", "\nfoo\nbar.*\n")}
    }

    assert _find_packages_exclude_patterns(dist) == ("foo", "bar.*")


def test_find_packages_exclude_patterns_without_pyproject(tmpdir_cwd):
    assert _find_packages_exclude_patterns(Distribution()) == ()


@pytest.mark.parametrize(
    ("pyproject", "expected"),
    [
        ("[tool.setuptools]\npackages = ['mypkg']\n", ()),
        ("[tool.setuptools.packages]\nfind = 'invalid'\n", ()),
        (
            "[tool.setuptools.packages.find]\nexclude = 'mypkg.tests'\n",
            ("mypkg.tests",),
        ),
        (
            "[tool.setuptools.packages.find]\nexclude = ['mypkg.tests', 'mypkg.tests.*']\n",
            ("mypkg.tests", "mypkg.tests.*"),
        ),
        ("[tool.setuptools.packages.find]\nexclude = 3\n", ()),
    ],
)
def test_find_packages_exclude_patterns_from_pyproject(tmpdir_cwd, pyproject, expected):
    Path("pyproject.toml").write_text(pyproject, encoding="utf-8")

    assert _find_packages_exclude_patterns(Distribution()) == expected


def test_contains_python_sources_filters_non_identifier_paths(tmpdir_cwd):
    jaraco.path.build({
        "pkg": {"valid.py": ""},
        "data": {"file.txt": "", "not-valid.py": ""},
    })

    assert _contains_python_sources("pkg")
    assert not _contains_python_sources("data")


def test_is_explicitly_excluded_matches_nested_packages():
    assert not _is_explicitly_excluded("mypkg", "plugins/data.txt", ())
    assert not _is_explicitly_excluded(
        "mypkg", "not-valid/data.txt", ("mypkg.not-valid",)
    )
    assert _is_explicitly_excluded(
        "mypkg", "plugins/nested/data.txt", ("mypkg.plugins", "mypkg.plugins.*")
    )


def test_find_package_data_owner_handles_nested_and_excluded_paths(tmpdir_cwd):
    jaraco.path.build({
        "src": {
            "mypkg": {
                "__init__.py": "",
                "data.txt": "",
                "plugins": {"resource.txt": ""},
                "nested": {"module.py": "", "resource.txt": ""},
            }
        }
    })
    src_dirs = {"src/mypkg": "mypkg"}

    assert _find_package_data_owner("src/mypkg/data.txt", src_dirs, ()) == (
        "mypkg",
        "data.txt",
        True,
    )
    assert _find_package_data_owner("src/mypkg/plugins/resource.txt", src_dirs, ()) == (
        "mypkg",
        os.path.join("plugins", "resource.txt"),
        False,
    )
    assert (
        _find_package_data_owner("src/mypkg/nested/resource.txt", src_dirs, ()) is None
    )
    assert (
        _find_package_data_owner(
            "src/mypkg/plugins/resource.txt", src_dirs, ("mypkg.plugins",)
        )
        is None
    )
    assert _find_package_data_owner("orphan/data.txt", src_dirs, ()) is None


def test_include_package_data_abuse_respects_excluded_patterns():
    excluded = _IncludePackageDataAbuse(("mypkg.plugins",))

    assert excluded.is_module("module.py")
    assert excluded.importable_subpackage("mypkg", "plugins/data.txt") is None
    assert (
        _IncludePackageDataAbuse().importable_subpackage("mypkg", "plugins/data.txt")
        == "mypkg.plugins"
    )
    assert (
        _IncludePackageDataAbuse().importable_subpackage("mypkg", "not-valid/data.txt")
        is None
    )
