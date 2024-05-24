from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

__all__: list[str] = []  # No public function, only CLI is provided.


def _build(output_dir: Path) -> None:
    """Emulate as close as possible the way a build frontend would work."""
    # Call build_wheel hook from CWD
    _hook("build_sdist", Path.cwd(), output_dir)
    sdist = _find_or_halt(output_dir, "setuptools*.tar.gz", "Error building sdist")
    print(f"**** sdist created in `{sdist}` ****")

    # Call build_wheel hook from the sdist
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "tarfile", "-e", str(sdist), tmp])

        root = _find_or_halt(Path(tmp), "setuptools-*", "Error finding sdist root")
        _hook("build_wheel", root, output_dir)

    wheel = _find_or_halt(output_dir, "setuptools*.whl", "Error building wheel")
    print(f"**** wheel created in `{wheel}` ****")


def _find_or_halt(parent: Path, pattern: str, error: str) -> Path:
    if file := next(parent.glob(pattern), None):
        return file
    raise SystemExit(f"{error}. Cannot find `{parent / pattern}`")


def _hook(name: str, source_dir: Path, output_dir: Path) -> None:
    # Call each hook in a fresh subprocess as required by PEP 517
    out = str(output_dir.absolute())
    script = f"from setuptools.build_meta import {name}; {name}({out!r})"
    subprocess.run([sys.executable, "-c", script], cwd=source_dir)


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="**EXPERIMENTAL** bootstrapping script for setuptools. "
        "Note that this script will perform a **simplified** procedure and may not "
        "provide all the guarantees of full-blown Python build-frontend.\n"
        "To install the created wheel, please extract it into the relevant directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="./dist",
        help="Where to store the build artifacts",
    )
    params = parser.parse_args()
    if params.output_dir.exists() and len(list(params.output_dir.iterdir())) > 0:
        # Let's avoid accidents by preventing multiple wheels in the directory
        raise SystemExit(f'--output-dir="{params.output_dir}" must be empty.')
    _build(params.output_dir)


if __name__ == "__main__":
    _cli()
