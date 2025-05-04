import os
import sys
import types

from setuptools import Command

from .. import _scripts


class easy_install(Command):
    """Stubbed command for temporary pbr compatibility."""


def __getattr__(name):
    attr = getattr(
        types.SimpleNamespace(
            ScriptWriter=_scripts.ScriptWriter,
            sys_executable=os.environ.get(
                "__PYVENV_LAUNCHER__", os.path.normpath(sys.executable)
            ),
        ),
        name,
    )
    return attr
