import os
import shutil

import pytest
from setuptools.archive_util import unpack_archive


CMD = ["python", "-m", "setuptools._bootstrap"]


def bootstrap_run(venv, tmp_path, options=(), **kwargs):
    target = tmp_path / "target"
    target.mkdir()
    venv.run([*CMD, *options, "--install-dir", str(target)], **kwargs)
    return target


def verify_install(target):
    # Included in wheel:
    assert (target / "distutils-precedence.pth").is_file()
    assert (target / "setuptools/__init__.py").is_file()
    assert (target / "pkg_resources/__init__.py").is_file()
    # Excluded from wheel:
    assert not (target / "setuptools/tests").is_dir()
    assert not (target / "pkg_resources/tests").is_dir()


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
    target = bootstrap_run(bare_venv, tmp_path, cwd=str(setuptools_sourcetree))
    verify_install(target)


def test_bootstrap_pythonpath(tmp_path, setuptools_wheel, bare_venv):
    env = {"PYTHONPATH": str(setuptools_wheel)}
    if use_distutils := os.getenv("SETUPTOOLS_USE_DISTUTILS", ""):
        env["SETUPTOOLS_USE_DISTUTILS"] = use_distutils

    target = bootstrap_run(
        bare_venv, tmp_path, ["--wheel-in-path"], env=env, cwd=str(tmp_path)
    )
    verify_install(target)
