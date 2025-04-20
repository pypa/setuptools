import subprocess
import sys

from setuptools import Command
from setuptools.warnings import SetuptoolsDeprecationWarning


class develop(Command):
    """Set up package for development"""

    user_options = [
        ("install-dir=", "d", "install package to DIR"),
        ('no-deps', 'N', "don't install dependencies"),
    ]
    boolean_options = [
        'no-deps',
    ]

    install_dir = None
    no_deps = False

    def run(self):
        cmd = (
            [sys.executable, '-m', 'pip', 'install', '-e', '.', '--use-pep517']
            + [
                '--target',
                self.install_dir,
            ]
            * bool(self.install_dir)
            + ['--no-deps'] * self.no_deps
        )
        subprocess.check_call(cmd)

    def initialize_options(self):
        DevelopDeprecationWarning.emit()

    def finalize_options(self) -> None:
        pass


class DevelopDeprecationWarning(SetuptoolsDeprecationWarning):
    _SUMMARY = "develop command is deprecated."
    _DETAILS = """
    Please avoid running ``setup.py`` and ``develop``.
    Instead, use standards-based tools like pip or uv.
    """
    _SEE_URL = "https://github.com/pypa/setuptools/issues/917"
    # _DUE_DATE = (TBD)
