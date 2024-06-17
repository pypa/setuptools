from __future__ import annotations

from os import PathLike
import subprocess
import sys

from pathlib import Path


def generate_pyproject_validation(dest: str | PathLike[str]):
    """
    Generates validation code for ``pyproject.toml`` based on JSON schemas and the
    ``validate-pyproject`` library.
    """
    cmd = [
        sys.executable,
        "-m",
        "validate_pyproject.pre_compile",
        f"--output-dir={dest}",
        "--enable-plugins",
        "setuptools",
        "distutils",
        "--very-verbose",
    ]
    subprocess.check_call(cmd)
    print(f"Validation code generated at: {dest}")


def main():
    generate_pyproject_validation(Path("setuptools/config/_validate_pyproject"))


__name__ == '__main__' and main()
