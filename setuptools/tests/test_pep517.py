import pytest
import os

# Only test the backend on Python 3
# because we don't want to require
# a concurrent.futures backport for testing
pytest.importorskip('concurrent.futures')

from contextlib import contextmanager
from importlib import import_module
from tempfile import mkdtemp
from concurrent.futures import ProcessPoolExecutor
from .files import build_files
from .textwrap import DALS
from . import contexts


class BuildBackend(object):
    """PEP 517 Build Backend"""
    def __init__(self, cwd=None, env={}, backend_name='setuptools.pep517'):
        self.cwd = cwd
        self.env = env
        self.backend_name = backend_name
        self.pool = ProcessPoolExecutor()

    def __getattr__(self, name):
        """Handles aribrary function invokations on the build backend."""

        def method(*args, **kw):
            return self.pool.submit(
                BuildBackendCaller(self.cwd, self.env, self.backend_name),
                (name, args, kw)).result()

        return method


class BuildBackendCaller(object):
    def __init__(self, cwd, env, backend_name):
        self.cwd = cwd
        self.env = env
        self.backend_name = backend_name

    def __call__(self, info):
        """Handles aribrary function invokations on the build backend."""
        os.chdir(self.cwd)
        os.environ.update(self.env)
        name, args, kw = info
        return getattr(import_module(self.backend_name), name)(*args, **kw)


@contextmanager
def enter_directory(dir, val=None):
    original_dir = os.getcwd()
    os.chdir(dir)
    yield val
    os.chdir(original_dir)


@pytest.fixture
def build_backend():
    tmpdir = mkdtemp()
    with enter_directory(tmpdir):
        setup_script = DALS("""
        from setuptools import setup

        setup(
            name='foo',
            py_modules=['hello'],
            setup_requires=['test-package'],
            entry_points={'console_scripts': ['hi = hello.run']},
            zip_safe=False,
        )
        """)

        build_files({
            'setup.py': setup_script,
            'hello.py': DALS("""
                def run():
                    print('hello')
                """)
        })

    return enter_directory(tmpdir, BuildBackend(cwd='.'))


def test_get_requires_for_build_wheel(build_backend):
    with build_backend as b:
        assert list(sorted(b.get_requires_for_build_wheel())) == \
            list(sorted(['test-package', 'setuptools', 'wheel']))
