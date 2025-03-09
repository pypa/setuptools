import logging
import os
import pathlib
import platform
import sys

import path
import pytest


@pytest.fixture
def save_env():
    orig = os.environ.copy()
    try:
        yield
    finally:
        for key in set(os.environ) - set(orig):
            del os.environ[key]
        for key, value in orig.items():
            if os.environ.get(key) != value:
                os.environ[key] = value


@pytest.fixture
def needs_zlib():
    pytest.importorskip('zlib')


@pytest.fixture(autouse=True)
def log_everything():
    """
    For tests, set the level on the logger to log everything.
    """
    logging.getLogger('distutils').setLevel(0)


@pytest.fixture(autouse=True)
def capture_log_at_info(caplog):
    """
    By default, capture logs at INFO and greater.
    """
    caplog.set_level(logging.INFO)


def _save_cwd():
    return path.Path('.')


@pytest.fixture
def distutils_managed_tempdir(request):
    from distutils.tests.compat import py39 as os_helper

    self = request.instance
    self.tempdirs = []
    try:
        with _save_cwd():
            yield
    finally:
        while self.tempdirs:
            tmpdir = self.tempdirs.pop()
            os_helper.rmtree(tmpdir)


@pytest.fixture
def save_argv():
    orig = sys.argv[:]
    try:
        yield
    finally:
        sys.argv[:] = orig


@pytest.fixture
def save_cwd():
    with _save_cwd():
        yield


@pytest.fixture
def temp_cwd(tmp_path):
    with path.Path(tmp_path):
        yield


# from pytest-dev/pytest#363
@pytest.fixture(scope="session")
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="module")
def suppress_path_mangle(monkeysession):
    """
    Disable the path mangling in CCompiler. Workaround for #169.
    """
    from distutils import ccompiler

    monkeysession.setattr(
        ccompiler.CCompiler, '_make_relative', staticmethod(lambda x: x)
    )


def _set_home(monkeypatch, path):
    var = 'USERPROFILE' if platform.system() == 'Windows' else 'HOME'
    monkeypatch.setenv(var, str(path))
    return path


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    return _set_home(monkeypatch, tmp_path)


@pytest.fixture
def fake_home(fs, monkeypatch):
    home = fs.create_dir('/fakehome')
    return _set_home(monkeypatch, pathlib.Path(home.path))


@pytest.fixture
def disable_macos_customization(monkeypatch):
    from distutils import sysconfig

    monkeypatch.setattr(sysconfig, '_customize_macos', lambda: None)


@pytest.fixture(autouse=True, scope="session")
def monkey_patch_get_default_compiler(monkeysession):
    """
    Monkey patch distutils get_default_compiler to allow overriding the
    default compiler. Mainly to test mingw32 with a MSVC Python.
    """
    from distutils import ccompiler

    default_compiler = os.environ.get("DISTUTILS_TEST_DEFAULT_COMPILER")

    if default_compiler is None:
        return

    def patched_getter(*args, **kwargs):
        return default_compiler

    monkeysession.setattr(ccompiler, 'get_default_compiler', patched_getter)
