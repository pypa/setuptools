import os
import sys

from setuptools import Command

from .. import _scripts


class easy_install(Command):
    """Stubbed command for temporary pbr compatibility."""


ScriptWriter = _scripts.ScriptWriter
sys_executable = os.environ.get("__PYVENV_LAUNCHER__", os.path.normpath(sys.executable))
