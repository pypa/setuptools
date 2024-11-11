import os
import shutil

import pytest

from setuptools.archive_util import unpack_archive

CMD = ["python", "-m", "setuptools._bootstrap"]


@pytest.fixture
def setuptools_sourcetree(tmp_path, setuptools_sdist, request):
    """
    Recreate the setuptools source tree.
    We use sdist in a temporary directory to avoid race conditions with build/dist dirs.
    """
    unpack_archive(setuptools_sdist, tmp_path)
    root = next(tmp_path.glob("setuptools-*"))
    # Remove sdist's metadata/cache/artifacts to simulate fresh repo
    shutil.rmtree(root / "setuptools.egg-info", ignore_errors=True)
    (root / "PKG-INFO").unlink()
    # We need the bootstrap folder (not included in the sdist)
    shutil.copytree(
        os.path.join(request.config.rootdir, "bootstrap.egg-info"),
        os.path.join(root, "bootstrap.egg-info"),
    )
    return root


def test_bootstrap_sourcetree(tmp_path, bare_venv, setuptools_sourcetree):
    bare_venv.run(CMD, cwd=str(setuptools_sourcetree))
    wheel = next((setuptools_sourcetree / "dist").glob("*.whl"))
    assert wheel.name.startswith("setuptools")

    target = tmp_path / "target"
    target.mkdir()
    bare_venv.run(["python", "-m", "zipfile", "-e", str(wheel), str(target)])

    # Included in wheel:
    assert (target / "distutils-precedence.pth").is_file()
    assert (target / "setuptools/__init__.py").is_file()
    assert (target / "pkg_resources/__init__.py").is_file()
    # Excluded from wheel:
    assert not (target / "setuptools/tests").is_dir()
    assert not (target / "pkg_resources/tests").is_dir()

    # Avoid errors on Windows by copying env before modifying
    # https://stackoverflow.com/questions/58997105
    env = {**os.environ, "PYTHONPATH": str(target)}
    test = ["python", "-c", "print(__import__('setuptools').__version__)"]
    bare_venv.run(test, env=env)
