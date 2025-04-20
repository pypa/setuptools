import subprocess
import sys

from setuptools import Command


class develop(Command):
    """Set up package for development"""

    user_options = [
        ("install-dir=", "d", "install package to DIR"),
    ]

    install_dir = None

    def run(self):
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', '.', '--use-pep517'] + [
            '--target',
            self.install_dir,
        ] * bool(self.install_dir)
        subprocess.check_call(cmd)

    def initialize_options(self):
        pass

    def finalize_options(self) -> None:
        pass
