"""Generate distutils stub files inside the source directory before packaging.
We have to do this as a custom build backend for PEP 660 editable installs.
Doing it this way also allows us to point local type-checkers to types/distutils,
overriding the stdlib types even on Python < 3.12."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from setuptools._path import StrPath
from setuptools.build_meta import *  # noqa: F403 # expose everything
from setuptools.build_meta import (
    _ConfigSettings,
    build_editable as _build_editable,
    build_sdist as _build_sdist,
    build_wheel as _build_wheel,
)

_vendored_distutils_path = Path(__file__).parent / "setuptools" / "_distutils"
_distutils_stubs_path = Path(__file__).parent / "distutils-stubs"


def _regenerate_distutils_stubs() -> None:
    shutil.rmtree(_distutils_stubs_path, ignore_errors=True)
    _distutils_stubs_path.mkdir(parents=True)
    (_distutils_stubs_path / ".gitignore").write_text("*")
    (_distutils_stubs_path / "ruff.toml").write_text('[lint]\nignore = ["F403"]')
    for path in _vendored_distutils_path.rglob("*.py"):
        relative_path = path.relative_to(_vendored_distutils_path)
        if relative_path.parts[0] == "tests":
            continue
        # if str(relative_path) == "__init__.py":
        #     # Work around a mypy issue with types/distutils/__init__.pyi:
        #     # error: Source file found twice under different module names: "setuptools._distutils.__init__" and "setuptools._distutils"
        #     (_distutils_stubs_path / "py.typed").write_text('partial')
        #     continue
        stub_path = _distutils_stubs_path / relative_path.with_suffix(".pyi")
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        module = "setuptools._distutils." + str(relative_path.with_suffix("")).replace(
            os.sep, "."
        ).removesuffix(".__init__")
        stub_path.write_text(f"from {module} import *\n")


def build_wheel(  # type: ignore[no-redef]
    wheel_directory: StrPath,
    config_settings: _ConfigSettings = None,
    metadata_directory: StrPath | None = None,
) -> str:
    _regenerate_distutils_stubs()
    return _build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(  # type: ignore[no-redef]
    sdist_directory: StrPath,
    config_settings: _ConfigSettings = None,
) -> str:
    _regenerate_distutils_stubs()
    return _build_sdist(sdist_directory, config_settings)


def build_editable(  # type: ignore[no-redef]
    wheel_directory: StrPath,
    config_settings: _ConfigSettings = None,
    metadata_directory: StrPath | None = None,
) -> str:
    _regenerate_distutils_stubs()
    return _build_editable(wheel_directory, config_settings, metadata_directory)
