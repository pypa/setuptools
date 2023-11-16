import os
import contextlib
import sys
import subprocess
from pathlib import Path

import pytest
import path

from . import contexts, environment


@pytest.fixture
def user_override(monkeypatch):
    """
    Override site.USER_BASE and site.USER_SITE with temporary directories in
    a context.
    """
    with contexts.tempdir() as user_base:
        monkeypatch.setattr('site.USER_BASE', user_base)
        with contexts.tempdir() as user_site:
            monkeypatch.setattr('site.USER_SITE', user_site)
            with contexts.save_user_site_setting():
                yield


@pytest.fixture
def tmpdir_cwd(tmpdir):
    with tmpdir.as_cwd() as orig:
        yield orig


@pytest.fixture(autouse=True, scope="session")
def workaround_xdist_376(request):
    """
    Workaround pytest-dev/pytest-xdist#376

    ``pytest-xdist`` tends to inject '' into ``sys.path``,
    which may break certain isolation expectations.
    Remove the entry so the import
    machinery behaves the same irrespective of xdist.
    """
    if not request.config.pluginmanager.has_plugin('xdist'):
        return

    with contextlib.suppress(ValueError):
        sys.path.remove('')


@pytest.fixture
def sample_project(tmp_path):
    """
    Clone the 'sampleproject' and return a path to it.
    """
    cmd = ['git', 'clone', 'https://github.com/pypa/sampleproject']
    try:
        subprocess.check_call(cmd, cwd=str(tmp_path))
    except Exception:
        pytest.skip("Unable to clone sampleproject")
    return tmp_path / 'sampleproject'


# sdist and wheel artifacts should be stable across a round of tests
# so we can build them once per session and use the files as "readonly"


@pytest.fixture(scope="session")
def setuptools_sdist(tmp_path_factory, request, _debug_subprocess):
    prebuilt = os.getenv("PRE_BUILT_SETUPTOOLS_SDIST")
    if prebuilt and os.path.exists(prebuilt):
        return Path(prebuilt).resolve()

    with contexts.session_locked_tmp_dir(
        request, tmp_path_factory, "sdist_build"
    ) as tmp:
        dist = next(tmp.glob("*.tar.gz"), None)
        if dist:
            return dist

        subprocess.check_output(
            [
                sys.executable,
                "-m",
                "build",
                "--sdist",
                "--outdir",
                str(tmp),
                str(request.config.rootdir),
            ]
        )
        return next(tmp.glob("*.tar.gz"))


@pytest.fixture(scope="session")
def setuptools_wheel(tmp_path_factory, request, _debug_subprocess):
    prebuilt = os.getenv("PRE_BUILT_SETUPTOOLS_WHEEL")
    if prebuilt and os.path.exists(prebuilt):
        return Path(prebuilt).resolve()

    with contexts.session_locked_tmp_dir(
        request, tmp_path_factory, "wheel_build"
    ) as tmp:
        dist = next(tmp.glob("*.whl"), None)
        if dist:
            return dist

        subprocess.check_output(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                str(tmp),
                str(request.config.rootdir),
            ]
        )
        return next(tmp.glob("*.whl"))


@pytest.fixture
def venv(tmp_path, setuptools_wheel):
    """Virtual env with the version of setuptools under test installed"""
    env = environment.VirtualEnv()
    env.root = path.Path(tmp_path / 'venv')
    env.create_opts = ['--no-setuptools', '--wheel=bundle']
    # TODO: Use `--no-wheel` when setuptools implements its own bdist_wheel
    env.req = str(setuptools_wheel)
    # In some environments (eg. downstream distro packaging),
    # where tox isn't used to run tests and PYTHONPATH is set to point to
    # a specific setuptools codebase, PYTHONPATH will leak into the spawned
    # processes.
    # env.create() should install the just created setuptools
    # wheel, but it doesn't if it finds another existing matching setuptools
    # installation present on PYTHONPATH:
    # `setuptools is already installed with the same version as the provided
    # wheel. Use --force-reinstall to force an installation of the wheel.`
    # This prevents leaking PYTHONPATH to the created environment.
    with contexts.environment(PYTHONPATH=None):
        return env.create()


@pytest.fixture
def venv_without_setuptools(tmp_path):
    """Virtual env without any version of setuptools installed"""
    env = environment.VirtualEnv()
    env.root = path.Path(tmp_path / 'venv_without_setuptools')
    env.create_opts = ['--no-setuptools', '--no-wheel']
    env.ensure_env()
    return env


@pytest.fixture
def bare_venv(tmp_path):
    """Virtual env without any common packages installed"""
    env = environment.VirtualEnv()
    env.root = path.Path(tmp_path / 'bare_venv')
    env.create_opts = ['--no-setuptools', '--no-pip', '--no-wheel', '--no-seed']
    env.ensure_env()
    return env


@pytest.fixture
def _debug_venv(venv, setuptools_wheel):
    try:
        yield
    except Exception:
        from pprint import pprint
        from zipfile import ZipFile

        print(f"{setuptools_wheel=}", file=sys.stderr)
        with ZipFile(setuptools_wheel) as zipfile:
            pprint(set(zipfile.namelist()), stream=sys.stderr, indent=4)

        venv_lib = next(Path(venv.root).rglob("site-packages/"))
        pprint(f"{venv.root=}", stream=sys.stderr)
        pprint(list(venv_lib.iterdir()), stream=sys.stderr, indent=4)

        raise


@pytest.fixture
def _debug_subprocess():
    try:
        yield
    except subprocess.CalledProcessError as ex:
        print(f"{ex.cmd=}", file=sys.stderr)
        print(f"{ex.stdout=}", file=sys.stderr)
        print(f"{ex.stderr=}", file=sys.stderr)
        print(f"{ex.returncode=}", file=sys.stderr)
        raise
