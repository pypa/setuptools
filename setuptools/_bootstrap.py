from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path

__all__: list[str] = []  # No public function, only CLI is provided.

_PRIVATE = "_private._dont_call_directly"


def _build(output_dir: Path) -> None:
    """Emulate as close as possible the way a build frontend would work."""
    cmd = [sys.executable, "-m", "setuptools._bootstrap"]
    store_dir = str(output_dir.absolute())

    # Call build_sdist hook
    subprocess.run([*cmd, _PRIVATE, "build_sdist", store_dir])
    sdist = _find_or_halt(output_dir, "setuptools*.tar.gz", "Error building sdist")
    print(f"**** sdist created in `{sdist}` ****")

    # Call build_wheel hook from the sdist
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "tarfile", "-e", str(sdist), tmp])

        root = _find_or_halt(Path(tmp), "setuptools-*", "Error finding sdist root")
        subprocess.run([*cmd, _PRIVATE, "build_wheel", store_dir], cwd=str(root))

    wheel = _find_or_halt(output_dir, "setuptools*.whl", "Error building wheel")
    print(f"**** wheel created in `{wheel}` ****")


def _find_or_halt(parent: Path, pattern: str, error: str) -> Path:
    if file := next(parent.glob(pattern), None):
        return file
    raise SystemExit(f"{error}. Cannot find `{parent / pattern}`")


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


def _private(guard: str = _PRIVATE) -> None:
    """Private CLI that only calls a build hook in the simplest way possible."""
    parser = argparse.ArgumentParser()
    private = parser.add_subparsers().add_parser(guard)
    private.add_argument("hook", choices=["build_sdist", "build_wheel"])
    private.add_argument("output_dir", type=Path)
    params = parser.parse_args()
    hook = getattr(importlib.import_module("setuptools.build_meta"), params.hook)
    hook(params.output_dir)


if __name__ == "__main__":
    _private() if _PRIVATE in sys.argv else _cli()
