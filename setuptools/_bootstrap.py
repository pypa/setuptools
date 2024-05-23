from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
import tempfile
from functools import partial
from pathlib import Path

__all__: list[str] = []  # No public function, only CLI is provided.


def _install(wheel: Path, target_dir: Path) -> Path:
    print(f"Installing {wheel} into {target_dir}")
    subprocess.run([sys.executable, "-m", "zipfile", "-e", str(wheel), str(target_dir)])
    dist_info = _find_or_halt(target_dir, "setuptools*.dist-info", "Error installing")
    _finalize_install(wheel, dist_info)
    return dist_info


def _finalize_install(wheel: Path, dist_info: Path) -> None:
    buffering = 4096  # 4K
    sha = hashlib.sha256()
    with wheel.open("rb") as f:
        for block in iter(partial(f.read, buffering), b""):
            sha.update(block)

    direct_url = {
        "url": wheel.absolute().as_uri(),
        "archive_info": {"hashes": {"sha256": sha.hexdigest()}},
    }
    text = json.dumps(direct_url, indent=2)
    (dist_info / "direct_url.json").write_text(text, encoding="utf-8")


def _build(output_dir: Path) -> Path:
    """Emulate as close as possible the way a build frontend works"""
    cmd = [sys.executable, "-m", "setuptools._bootstrap"]
    store_dir = str(output_dir.absolute())

    # Sanity check
    assert Path("pyproject.toml").exists()
    assert Path("bootstrap.egg-info/entry_points.txt").exists()

    # Call build_sdist hook (PEP 517)
    subprocess.run([*cmd, "_private", "build_sdist", store_dir])
    sdist = _find_or_halt(output_dir, "setuptools*.tar.gz", "Error building sdist")
    print(f"**** sdist created in `{sdist}` ****")

    # Call build_wheel hook (PEP 517)
    kw1 = {"ignore_cleanup_errors": True} if sys.version_info >= (3, 10) else {}
    with tempfile.TemporaryDirectory(**kw1) as tmp:  # type: ignore[call-overload]
        subprocess.run([sys.executable, "-m", "tarfile", "-e", str(sdist), tmp])
        root = _find_or_halt(Path(tmp), "setuptools-*", "Error finding sdist root")
        _find_or_halt(root, "pyproject.toml", "Error extracting sdist")
        subprocess.run([*cmd, "_private", "build_wheel", store_dir], cwd=str(root))
        wheel = _find_or_halt(output_dir, "setuptools*.whl", "Error building wheel")

    print(f"**** wheel created in `{wheel}` ****")
    return wheel


def _find_or_halt(parent: Path, pattern: str, error: str) -> Path:
    file = next(parent.glob(pattern), None)
    if not file:
        raise SystemExit(f"{error}. Cannot find `{parent / pattern}`")
    return file


def _cli():
    parser = argparse.ArgumentParser(
        description="**EXPERIMENTAL** bootstrapping script for setuptools. "
        "Note that this script will perform a **simplified** procedure and may not "
        "provide all the guarantees of full-blown Python build-frontend and installer."
    )
    parser.add_argument(
        "--install-dir",
        type=Path,
        help="Where to install setuptools, e.g. `.venv/lib/python3.12/site-packages`, "
        "when this option is not passed, the bootstrap script will skip installation "
        "steps and stop after building a wheel.",
    )
    parser.add_argument(
        "--wheel-in-path",
        action="store_true",
        help="Skip build step. Setuptools wheel MUST BE the first entry in PYTHONPATH.",
    )
    parser.add_argument(
        "--build-output-dir",
        type=Path,
        default="./dist",
        help="Where to store the build artifacts",
    )
    params = parser.parse_args()

    if params.wheel_in_path:
        try:
            wheel = next(
                path
                for path in map(Path, sys.path)
                if path.name.startswith("setuptools") and path.suffix == ".whl"
            )
        except StopIteration:
            raise SystemExit(f"Setuptools wheel is not present in {sys.path=}")
        print(f"**** wheel found in `{wheel}` ****")
    else:
        output_dir = params.build_output_dir
        if output_dir.exists() and len(list(output_dir.iterdir())) > 0:
            # Let's avoid accidents by preventing multiple wheels in the directory
            raise SystemExit(f'--build-output-dir="{output_dir}" must be empty.')
        wheel = _build(output_dir)

    if params.install_dir is None:
        print("Skipping instal, `--install-dir` option not passed")
    elif not params.install_dir.is_dir():
        # Let's enforce install dir must be present to avoid accidents
        raise SystemError(f'`--install-dir="{params.install_dir}"` does not exist.')
    else:
        dist_info = _install(wheel, params.install_dir)
        print(f"Installation complete. Distribution metadata in `{dist_info}`.")


def _private(guard: str = "_private") -> None:
    """Private CLI that only calls a build hook in the simplest way possible."""
    parser = argparse.ArgumentParser()
    private = parser.add_subparsers().add_parser(guard)
    private.add_argument("hook", choices=["build_sdist", "build_wheel"])
    private.add_argument("output_dir", type=Path)
    params = parser.parse_args()
    hook = getattr(importlib.import_module("setuptools.build_meta"), params.hook)
    hook(params.output_dir)


if __name__ == "__main__":
    _private() if "_private" in sys.argv else _cli()
