"""
Finalize the repo for a release. Invokes towncrier.
"""

__requires__ = ['towncrier', 'jaraco.develop>=7.23']

import subprocess
from pathlib import Path

from jaraco.develop import towncrier
from jaraco.develop.finalize import finalize


def main():
    version = towncrier.semver(towncrier.get_version())
    version = version.lstrip("v")  # Compatibility with setuptools-scm
    Path("(meta)/latest.txt").unlink()  # Remove "unstable"/development version
    Path("(meta)/stable.txt").write_text(version, encoding="utf-8")
    subprocess.check_output(['git', 'add', "(meta)/stable.txt"])
    finalize()


__name__ == '__main__' and main()
