import os
import subprocess
import sys
import tarfile
from configparser import ConfigParser
from pathlib import Path
from subprocess import CalledProcessError
from zipfile import ZipFile

import pytest

from setuptools.command.sdist import sdist
from setuptools.dist import Distribution

from .contexts import quiet


class TestDefaultPackagesAndPyModules:
    """Make sure default values for ``packages`` and ``py_modules`` work
    similarly to explicit configuration for the simple scenarios.
    """

    METADATA = {
        "name": "example",
        "version": "0.0.1",
        "author": "Example Author"
    }
    OPTIONS = {
        # Different options according to the circumstance being tested
        "explicit-src": {
            "package_dir": {"": "src"},
            "packages": ["example"]
        },
        "explicit-flat": {
            "packages": ["example"]
        },
        "explicit-single_module": {
            "py_modules": ["example"]
        },
        "explicit-namespace": {
            "packages": ["ns", "ns.example"]
        },
        "automatic-src": {},
        "automatic-flat": {},
        "automatic-single_module": {},
        "automatic-namespace": {}
    }
    FILES = {
        "src": ["src/example/__init__.py", "src/example/main.py"],
        "flat": ["example/__init__.py", "example/main.py"],
        "single_module": ["example.py"],
        "namespace": ["ns/example/__init__.py"]
    }

    def _get_info(self, circumstance):
        _, _, layout = circumstance.partition("-")
        files = self.FILES[layout]
        options = self.OPTIONS[circumstance]
        metadata = self.METADATA
        if layout == "namespace":
            metadata = {**metadata, "name": "ns.example"}
        return files, metadata, options

    @pytest.mark.parametrize("circumstance", OPTIONS.keys())
    def test_sdist_filelist(self, tmp_path, circumstance):
        files, metadata, options = self._get_info(circumstance)
        _populate_project_dir(tmp_path, files, metadata, options)

        here = os.getcwd()
        try:
            os.chdir(tmp_path)
            dist = Distribution({**metadata, **options, "src_root": tmp_path})
            dist.script_name = 'setup.py'
            dist.set_option_defaults()
            cmd = sdist(dist)
            cmd.ensure_finalized()
            assert cmd.distribution.packages or cmd.distribution.py_modules

            with quiet():
                cmd.run()
        finally:
            os.chdir(here)

        manifest = [f.replace(os.sep, "/") for f in cmd.filelist.files]
        for file in files:
            assert any(f.endswith(file) for f in manifest)

    @pytest.mark.parametrize("circumstance", OPTIONS.keys())
    def test_project(self, tmp_path, circumstance):
        files, metadata, options = self._get_info(circumstance)
        _populate_project_dir(tmp_path, files, metadata, options)

        _run_build(tmp_path)

        sdist_files = _get_sdist_members(next(tmp_path.glob("dist/*.tar.gz")))
        print("~~~~~ sdist_members ~~~~~")
        print('\n'.join(sdist_files))
        assert sdist_files >= set(files)

        wheel_files = _get_wheel_members(next(tmp_path.glob("dist/*.whl")))
        print("~~~~~ wheel_members ~~~~~")
        print('\n'.join(wheel_files))
        assert wheel_files >= {f.replace("src/", "") for f in files}


def _populate_project_dir(root, files, metadata, options):
    (root / "setup.py").write_text("import setuptools\nsetuptools.setup()")
    (root / "README.md").write_text("# Example Package")
    (root / "LICENSE").write_text("Copyright (c) 2018")
    _write_setupcfg(root, metadata, options)

    for file in files:
        path = root / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('"hello world"')


def _write_setupcfg(root, metadata, options):
    setupcfg = ConfigParser()
    setupcfg.add_section("metadata")
    setupcfg["metadata"].update(metadata)
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
    assert setupcfg["metadata"]["name"]
    print("~~~~~ setup.cfg ~~~~~")
    print((root / "setup.cfg").read_text())


def _get_sdist_members(sdist_path):
    with tarfile.open(sdist_path, "r:gz") as tar:
        files = [Path(f) for f in tar.getnames()]
    relative_files = ("/".join(f.parts[1:]) for f in files)
    # remove root folder
    return {f for f in relative_files if f}


def _get_wheel_members(wheel_path):
    with ZipFile(wheel_path) as zipfile:
        return set(zipfile.namelist())


def _run_build(path):
    cmd = [sys.executable, "-m", "build", "--no-isolation", str(path)]
    r = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={**os.environ, 'DISTUTILS_DEBUG': '1'}
    )
    out = r.stdout + "\n" + r.stderr
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Command", repr(cmd), "returncode", r.returncode)
    print(out)

    if r.returncode != 0:
        raise CalledProcessError(r.returncode, cmd, r.stdout, r.stderr)
    return out
