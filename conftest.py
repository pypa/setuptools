import os
import sys
import platform
import shutil

import pytest


collect_ignore = []


if platform.system() != 'Windows':
    collect_ignore.extend(
        [
            'distutils/command/bdist_msi.py',
            'distutils/msvc9compiler.py',
        ]
    )


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


@pytest.fixture
def distutils_logging_silencer(request):
    from distutils import log

    self = request.instance
    self.threshold = log.set_threshold(log.FATAL)
    # catching warnings
    # when log will be replaced by logging
    # we won't need such monkey-patch anymore
    self._old_log = log.Log._log
    log.Log._log = self._log
    self.logs = []

    try:
        yield
    finally:
        log.set_threshold(self.threshold)
        log.Log._log = self._old_log


@pytest.fixture
def distutils_managed_tempdir(request):
    from distutils.tests import py38compat as os_helper

    self = request.instance
    self.old_cwd = os.getcwd()
    self.tempdirs = []
    try:
        yield
    finally:
        # Restore working dir, for Solaris and derivatives, where rmdir()
        # on the current directory fails.
        os.chdir(self.old_cwd)
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
    orig = os.getcwd()
    try:
        yield
    finally:
        os.chdir(orig)


@pytest.fixture
def threshold_warn():
    from distutils.log import set_threshold, WARN

    orig = set_threshold(WARN)
    yield
    set_threshold(orig)


@pytest.fixture
def pypirc(request, save_env, distutils_managed_tempdir):
    from distutils.core import PyPIRCCommand
    from distutils.core import Distribution

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


@pytest.fixture
def cleanup_testfn():
    from distutils.tests import py38compat as os_helper

    yield
    path = os_helper.TESTFN
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


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
        ccompiler.CCompiler, '_mangle_base', staticmethod(lambda x: x)
    )
