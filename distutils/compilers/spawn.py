"""
Run a command in a subprocess, the primitive underlying compiler and
linker invocations.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from collections.abc import Mapping, MutableSequence
from typing import TYPE_CHECKING, TypeVar

from ..errors import DistutilsExecError
from .logging import get_logger

if TYPE_CHECKING:
    from subprocess import _ENV

log = get_logger(__name__)

_MappingT = TypeVar("_MappingT", bound=Mapping)


def _inject_macos_ver(env: _MappingT | None) -> _MappingT | dict[str, str | int] | None:
    """
    Ensure a subprocess inherits the deployment target the build was
    configured with, so extensions link against a consistent macOS version.
    """
    if platform.system() != 'Darwin':
        return env

    # imported lazily; the platform/macOS utilities remain in distutils
    # until that layer is decoupled (pypa/setuptools#5268).
    from ..util import MACOSX_VERSION_VAR, get_macosx_target_ver

    target_ver = get_macosx_target_ver()
    update = {MACOSX_VERSION_VAR: target_ver} if target_ver else {}
    resolved = os.environ if env is None else env
    return {**resolved, **update}


def spawn(
    cmd: MutableSequence[bytes | str | os.PathLike[str]],
    *,
    env: _ENV | None = None,
) -> None:
    """Run another program, specified as a command list 'cmd', in a new process.

    'cmd' is just the argument list for the new process, ie.
    cmd[0] is the program to run and cmd[1:] are the rest of its arguments.
    cmd[0] is resolved against the executable search path.

    Raise DistutilsExecError if running the program fails in any way; just
    return on success.
    """
    log.info(subprocess.list2cmdline(cmd))

    executable = shutil.which(cmd[0])
    if executable is not None:
        cmd[0] = executable

    try:
        subprocess.check_call(cmd, env=_inject_macos_ver(env))
    except OSError as exc:
        raise DistutilsExecError(f"command {cmd[0]!r} failed: {exc.args[-1]}") from exc
    except subprocess.CalledProcessError as err:
        raise DistutilsExecError(
            f"command {cmd[0]!r} failed with exit code {err.returncode}"
        ) from err
