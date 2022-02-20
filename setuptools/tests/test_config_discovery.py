import os
import sys
from configparser import ConfigParser

import pytest

from setuptools.command.sdist import sdist
from setuptools.dist import Distribution

from .contexts import quiet
from .integration.helpers import get_sdist_members, get_wheel_members, run


class TestDiscoverPackagesAndPyModules:
    """Make sure discovered values for ``packages`` and ``py_modules`` work
    similarly to explicit configuration for the simple scenarios.
    """
    OPTIONS = {
        # Different options according to the circumstance being tested
        "explicit-src": {
            "package_dir": {"": "src"},
            "packages": ["pkg"]
        },
        "explicit-flat": {
            "packages": ["pkg"]
        },
        "explicit-single_module": {
            "py_modules": ["pkg"]
        },
        "explicit-namespace": {
            "packages": ["ns", "ns.pkg"]
        },
        "automatic-src": {},
        "automatic-flat": {},
        "automatic-single_module": {},
        "automatic-namespace": {}
    }
    FILES = {
        "src": ["src/pkg/__init__.py", "src/pkg/main.py"],
        "flat": ["pkg/__init__.py", "pkg/main.py"],
        "single_module": ["pkg.py"],
        "namespace": ["ns/pkg/__init__.py"]
    }

    def _get_info(self, circumstance):
        _, _, layout = circumstance.partition("-")
        files = self.FILES[layout]
        options = self.OPTIONS[circumstance]
        return files, options

    @pytest.mark.parametrize("circumstance", OPTIONS.keys())
    def test_sdist_filelist(self, tmp_path, circumstance):
        files, options = self._get_info(circumstance)
        _populate_project_dir(tmp_path, files, options)

        here = os.getcwd()
        root = "/".join(os.path.split(tmp_path))  # POSIX-style
        dist = Distribution({**options, "src_root": root})
        dist.script_name = 'setup.py'
        dist.set_defaults()
        cmd = sdist(dist)
        cmd.ensure_finalized()
        assert cmd.distribution.packages or cmd.distribution.py_modules

        with quiet():
            try:
                os.chdir(tmp_path)
                cmd.run()
            finally:
                os.chdir(here)

        manifest = [f.replace(os.sep, "/") for f in cmd.filelist.files]
        for file in files:
            assert any(f.endswith(file) for f in manifest)

    @pytest.mark.parametrize("circumstance", OPTIONS.keys())
    def test_project(self, tmp_path, circumstance):
        files, options = self._get_info(circumstance)
        _populate_project_dir(tmp_path, files, options)

        # Simulate a pre-existing `build` directory
        (tmp_path / "build").mkdir()
        (tmp_path / "build/lib").mkdir()
        (tmp_path / "build/bdist.linux-x86_64").mkdir()
        (tmp_path / "build/bdist.linux-x86_64/file.py").touch()
        (tmp_path / "build/lib/__init__.py").touch()
        (tmp_path / "build/lib/file.py").touch()
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist/file.py").touch()

        _run_build(tmp_path)

        sdist_files = get_sdist_members(next(tmp_path.glob("dist/*.tar.gz")))
        print("~~~~~ sdist_members ~~~~~")
        print('\n'.join(sdist_files))
        assert sdist_files >= set(files)

        wheel_files = get_wheel_members(next(tmp_path.glob("dist/*.whl")))
        print("~~~~~ wheel_members ~~~~~")
        print('\n'.join(wheel_files))
        assert wheel_files >= {f.replace("src/", "") for f in files}

        # Make sure build files are not included by mistake
        for file in wheel_files:
            assert "build" not in files
            assert "dist" not in files


class TestNoConfig:
    DEFAULT_VERSION = "0.0.0"  # Default version given by setuptools

    EXAMPLES = {
        "pkg1": ["src/pkg1.py"],
        "pkg2": ["src/pkg2/__init__.py"],
        "ns.nested.pkg3": ["src/ns/nested/pkg3/__init__.py"]
    }

    @pytest.mark.parametrize("example", EXAMPLES.keys())
    def test_discover_name(self, tmp_path, example):
        _populate_project_dir(tmp_path, self.EXAMPLES[example], {})
        _run_build(tmp_path, "--sdist")
        # Expected distribution file
        dist_file = tmp_path / f"dist/{example}-{self.DEFAULT_VERSION}.tar.gz"
        assert dist_file.is_file()


def _populate_project_dir(root, files, options):
    # NOTE: Currently pypa/build will refuse to build the project if no
    # `pyproject.toml` or `setup.py` is found. So it is impossible to do
    # completely "config-less" projects.
    (root / "setup.py").write_text("import setuptools\nsetuptools.setup()")
    (root / "README.md").write_text("# Example Package")
    (root / "LICENSE").write_text("Copyright (c) 2018")
    _write_setupcfg(root, options)
    paths = (root / f for f in files)
    for path in paths:
        path.parent.mkdir(exist_ok=True, parents=True)
        path.touch()


def _write_setupcfg(root, options):
    if not options:
        print("~~~~~ **NO** setup.cfg ~~~~~")
        return
    setupcfg = ConfigParser()
    setupcfg.add_section("options")
    for key, value in options.items():
        if isinstance(value, list):
            setupcfg["options"][key] = ", ".join(value)
        elif isinstance(value, dict):
            str_value = "\n".join(f"\t{k} = {v}" for k, v in value.items())
            setupcfg["options"][key] = "\n" + str_value
        else:
            setupcfg["options"][key] = str(value)
    with open(root / "setup.cfg", "w") as f:
        setupcfg.write(f)
    print("~~~~~ setup.cfg ~~~~~")
    print((root / "setup.cfg").read_text())


def _run_build(path, *flags):
    cmd = [sys.executable, "-m", "build", "--no-isolation", *flags, str(path)]
    return run(cmd, env={'DISTUTILS_DEBUG': '1'})
