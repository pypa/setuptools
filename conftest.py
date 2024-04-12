import logging
import os
import pathlib
import platform
import sys

import path
import pytest

collect_ignore = []


if platform.system() != 'Windows':
    collect_ignore.extend([
        'distutils/msvc9compiler.py',
    ])


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
    from distutils.tests import py38compat as os_helper

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


@pytest.fixture
def pypirc(request, save_env, distutils_managed_tempdir):
    from distutils.core import Distribution, PyPIRCCommand

    self = request.instance
    self.tmp_dir = self.mkdtemp()
    os.environ['HOME'] = self.tmp_dir
    os.environ['USERPROFILE'] = self.tmp_dir
    self.rc = os.path.join(self.tmp_dir, '.pypirc')
    self.dist = Distribution()

    class command(PyPIRCCommand):
        def __init__(self, dist):
            super().__init__(dist)

        def initialize_options(self):
            pass

        finalize_options = initialize_options

    self._cmd = command


# from pytest-dev/pytest#363
@pytest.fixture(scope="session")
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(autouse=True, scope="session")
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
