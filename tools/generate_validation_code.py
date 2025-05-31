from __future__ import annotations

import itertools
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path


def generate_pyproject_validation(dest: Path, schemas: Iterable[Path]) -> bool:
    """
    Generates validation code for ``pyproject.toml`` based on JSON schemas and the
    ``validate-pyproject`` library.
    """
    schema_args = (("-t", f"{f.name.partition('.')[0]}={f}") for f in schemas)
    cmd = [
        sys.executable,
        "-m",
        "validate_pyproject.pre_compile",
        f"--output-dir={dest}",
        "--enable-plugins",
        "setuptools",
        "distutils",
        "--very-verbose",
        *itertools.chain.from_iterable(schema_args),
    ]
    subprocess.check_call(cmd)
    print(f"Validation code generated at: {dest}")
    return True


def main() -> bool:
    return generate_pyproject_validation(
        Path("setuptools/config/_validate_pyproject"),
        schemas=Path("setuptools/config").glob("*.schema.json"),
    )


__name__ == '__main__' and main()
