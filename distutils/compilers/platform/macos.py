"""macOS-specific compiler support."""

from __future__ import annotations

import os
import platform
from collections.abc import Mapping
from typing import TypeVar

_MappingT = TypeVar("_MappingT", bound=Mapping)


def _inject_ver(env: _MappingT | None) -> _MappingT | dict[str, str | int] | None:
    """
    Ensure a subprocess inherits the deployment target the build was
    configured with, so extensions link against a consistent macOS version.
    """
    if platform.system() != 'Darwin':
        return env

    # the platform/util helpers still live in distutils pending
    # pypa/setuptools#5268.
    from ...util import MACOSX_VERSION_VAR, get_macosx_target_ver

    target_ver = get_macosx_target_ver()
    update = {MACOSX_VERSION_VAR: target_ver} if target_ver else {}
    resolved = os.environ if env is None else env
    return {**resolved, **update}
