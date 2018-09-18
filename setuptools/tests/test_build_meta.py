from __future__ import unicode_literals

import os
import shutil

import pytest

from .files import build_files
from .textwrap import DALS

__metaclass__ = type

futures = pytest.importorskip('concurrent.futures')
importlib = pytest.importorskip('importlib')


class BuildBackendBase:
    def __init__(self, cwd=None, env={}, backend_name='setuptools.build_meta'):
        self.cwd = cwd
        self.env = env
        self.backend_name = backend_name


class BuildBackend(BuildBackendBase):
    """PEP 517 Build Backend"""

    def __init__(self, *args, **kwargs):
        super(BuildBackend, self).__init__(*args, **kwargs)
        self.pool = futures.ProcessPoolExecutor()

    def __getattr__(self, name):
        """Handles aribrary function invocations on the build backend."""

        def method(*args, **kw):
            root = os.path.abspath(self.cwd)
            caller = BuildBackendCaller(root, self.env, self.backend_name)
            return self.pool.submit(caller, name, *args, **kw).result()

        return method


class BuildBackendCaller(BuildBackendBase):
    def __call__(self, name, *args, **kw):
        """Handles aribrary function invocations on the build backend."""
        os.chdir(self.cwd)
        os.environ.update(self.env)
        mod = importlib.import_module(self.backend_name)
        return getattr(mod, name)(*args, **kw)


defns = [
    {
        'setup.py': DALS("""
            __import__('setuptools').setup(
                name='foo',
                version='0.0.0',
                py_modules=['hello'],
                setup_requires=['six'],
            )
            """),
        'hello.py': DALS("""
            def run():
                print('hello')
            """),
    },
    {
        'setup.py': DALS("""
            assert __name__ == '__main__'
            __import__('setuptools').setup(
                name='foo',
                version='0.0.0',
                py_modules=['hello'],
                setup_requires=['six'],
            )
            """),
        'hello.py': DALS("""
            def run():
                print('hello')
            """),
    },
    {
        'setup.py': DALS("""
            variable = True
            def function():
                return variable
            assert variable
            __import__('setuptools').setup(
                name='foo',
                version='0.0.0',
                py_modules=['hello'],
                setup_requires=['six'],
            )
            """),
        'hello.py': DALS("""
            def run():
                print('hello')
            """),
    },
]


@pytest.fixture(params=defns)
def build_backend(tmpdir, request):
    build_files(request.param, prefix=str(tmpdir))
    with tmpdir.as_cwd():
        yield BuildBackend(cwd='.')


def test_get_requires_for_build_wheel(build_backend):
    actual = build_backend.get_requires_for_build_wheel()
    expected = ['six', 'setuptools', 'wheel']
    assert sorted(actual) == sorted(expected)


def test_get_requires_for_build_sdist(build_backend):
    actual = build_backend.get_requires_for_build_sdist()
    expected = ['six', 'setuptools']
    assert sorted(actual) == sorted(expected)


def test_build_wheel(build_backend):
    dist_dir = os.path.abspath('pip-wheel')
    os.makedirs(dist_dir)
    wheel_name = build_backend.build_wheel(dist_dir)

    assert os.path.isfile(os.path.join(dist_dir, wheel_name))


def test_build_sdist(build_backend):
    dist_dir = os.path.abspath('pip-sdist')
    os.makedirs(dist_dir)
    sdist_name = build_backend.build_sdist(dist_dir)

    assert os.path.isfile(os.path.join(dist_dir, sdist_name))


def test_prepare_metadata_for_build_wheel(build_backend):
    dist_dir = os.path.abspath('pip-dist-info')
    os.makedirs(dist_dir)

    dist_info = build_backend.prepare_metadata_for_build_wheel(dist_dir)

    assert os.path.isfile(os.path.join(dist_dir, dist_info, 'METADATA'))


@pytest.mark.skipif('sys.version_info > (3,)')
def test_prepare_metadata_for_build_wheel_with_str(build_backend):
    dist_dir = os.path.abspath(str('pip-dist-info'))
    os.makedirs(dist_dir)

    dist_info = build_backend.prepare_metadata_for_build_wheel(dist_dir)

    assert os.path.isfile(os.path.join(dist_dir, dist_info, 'METADATA'))


def test_build_sdist_explicit_dist(build_backend):
    # explicitly specifying the dist folder should work
    # the folder sdist_directory and the ``--dist-dir`` can be the same
    dist_dir = os.path.abspath('dist')
    sdist_name = build_backend.build_sdist(dist_dir)
    assert os.path.isfile(os.path.join(dist_dir, sdist_name))


def test_build_sdist_version_change(build_backend):
    sdist_into_directory = os.path.abspath("out_sdist")
    os.makedirs(sdist_into_directory)

    sdist_name = build_backend.build_sdist(sdist_into_directory)
    assert os.path.isfile(os.path.join(sdist_into_directory, sdist_name))

    # if the setup.py changes subsequent call of the build meta should still succeed, given the
    # sdist_directory the frontend specifies is empty
    with open(os.path.abspath("setup.py"), 'rt') as file_handler:
        content = file_handler.read()
    with open(os.path.abspath("setup.py"), 'wt') as file_handler:
        file_handler.write(content.replace("version='0.0.0'", "version='0.0.1'"))

    shutil.rmtree(sdist_into_directory)
    os.makedirs(sdist_into_directory)

    sdist_name = build_backend.build_sdist("out_sdist")
    assert os.path.isfile(os.path.join(os.path.abspath("out_sdist"), sdist_name))
