from __future__ import unicode_literals

import os
import shutil
import tarfile

import pytest

from .files import build_files
from .textwrap import DALS
from . import py2_only

__metaclass__ = type

# Backports on Python 2.7
import importlib
from concurrent import futures


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
    def __init__(self, *args, **kwargs):
        super(BuildBackendCaller, self).__init__(*args, **kwargs)

        (self.backend_name, _,
         self.backend_obj) = self.backend_name.partition(':')

    def __call__(self, name, *args, **kw):
        """Handles aribrary function invocations on the build backend."""
        os.chdir(self.cwd)
        os.environ.update(self.env)
        mod = importlib.import_module(self.backend_name)

        if self.backend_obj:
            backend = getattr(mod, self.backend_obj)
        else:
            backend = mod

        return getattr(backend, name)(*args, **kw)


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
    {
        'setup.cfg': DALS("""
        [metadata]
        name = foo
        version='0.0.0'

        [options]
        py_modules=hello
        setup_requires=six
        """),
        'hello.py': DALS("""
        def run():
            print('hello')
        """)
    },
]


class TestBuildMetaBackend:
    backend_name = 'setuptools.build_meta'

    def get_build_backend(self):
        return BuildBackend(cwd='.', backend_name=self.backend_name)

    @pytest.fixture(params=defns)
    def build_backend(self, tmpdir, request):
        build_files(request.param, prefix=str(tmpdir))
        with tmpdir.as_cwd():
            yield self.get_build_backend()

    def test_get_requires_for_build_wheel(self, build_backend):
        actual = build_backend.get_requires_for_build_wheel()
        expected = ['six', 'wheel']
        assert sorted(actual) == sorted(expected)

    def test_get_requires_for_build_sdist(self, build_backend):
        actual = build_backend.get_requires_for_build_sdist()
        expected = ['six']
        assert sorted(actual) == sorted(expected)

    def test_build_wheel(self, build_backend):
        dist_dir = os.path.abspath('pip-wheel')
        os.makedirs(dist_dir)
        wheel_name = build_backend.build_wheel(dist_dir)

        assert os.path.isfile(os.path.join(dist_dir, wheel_name))

    def test_build_sdist(self, build_backend):
        dist_dir = os.path.abspath('pip-sdist')
        os.makedirs(dist_dir)
        sdist_name = build_backend.build_sdist(dist_dir)

        assert os.path.isfile(os.path.join(dist_dir, sdist_name))

    def test_prepare_metadata_for_build_wheel(self, build_backend):
        dist_dir = os.path.abspath('pip-dist-info')
        os.makedirs(dist_dir)

        dist_info = build_backend.prepare_metadata_for_build_wheel(dist_dir)

        assert os.path.isfile(os.path.join(dist_dir, dist_info, 'METADATA'))

    @py2_only
    def test_prepare_metadata_for_build_wheel_with_str(self, build_backend):
        dist_dir = os.path.abspath(str('pip-dist-info'))
        os.makedirs(dist_dir)

        dist_info = build_backend.prepare_metadata_for_build_wheel(dist_dir)

        assert os.path.isfile(os.path.join(dist_dir, dist_info, 'METADATA'))

    def test_build_sdist_explicit_dist(self, build_backend):
        # explicitly specifying the dist folder should work
        # the folder sdist_directory and the ``--dist-dir`` can be the same
        dist_dir = os.path.abspath('dist')
        sdist_name = build_backend.build_sdist(dist_dir)
        assert os.path.isfile(os.path.join(dist_dir, sdist_name))

    def test_build_sdist_version_change(self, build_backend):
        sdist_into_directory = os.path.abspath("out_sdist")
        os.makedirs(sdist_into_directory)

        sdist_name = build_backend.build_sdist(sdist_into_directory)
        assert os.path.isfile(os.path.join(sdist_into_directory, sdist_name))

        # if the setup.py changes subsequent call of the build meta
        # should still succeed, given the
        # sdist_directory the frontend specifies is empty
        setup_loc = os.path.abspath("setup.py")
        if not os.path.exists(setup_loc):
            setup_loc = os.path.abspath("setup.cfg")

        with open(setup_loc, 'rt') as file_handler:
            content = file_handler.read()
        with open(setup_loc, 'wt') as file_handler:
            file_handler.write(
                content.replace("version='0.0.0'", "version='0.0.1'"))

        shutil.rmtree(sdist_into_directory)
        os.makedirs(sdist_into_directory)

        sdist_name = build_backend.build_sdist("out_sdist")
        assert os.path.isfile(
            os.path.join(os.path.abspath("out_sdist"), sdist_name))

    def test_build_sdist_setup_py_exists(self, tmpdir_cwd):
        # If build_sdist is called from a script other than setup.py,
        # ensure setup.py is included
        build_files(defns[0])

        build_backend = self.get_build_backend()
        targz_path = build_backend.build_sdist("temp")
        with tarfile.open(os.path.join("temp", targz_path)) as tar:
            assert any('setup.py' in name for name in tar.getnames())

    def test_build_sdist_setup_py_manifest_excluded(self, tmpdir_cwd):
        # Ensure that MANIFEST.in can exclude setup.py
        files = {
            'setup.py': DALS("""
        __import__('setuptools').setup(
            name='foo',
            version='0.0.0',
            py_modules=['hello']
        )"""),
            'hello.py': '',
            'MANIFEST.in': DALS("""
        exclude setup.py
        """)
        }

        build_files(files)

        build_backend = self.get_build_backend()
        targz_path = build_backend.build_sdist("temp")
        with tarfile.open(os.path.join("temp", targz_path)) as tar:
            assert not any('setup.py' in name for name in tar.getnames())

    def test_build_sdist_builds_targz_even_if_zip_indicated(self, tmpdir_cwd):
        files = {
            'setup.py': DALS("""
                __import__('setuptools').setup(
                    name='foo',
                    version='0.0.0',
                    py_modules=['hello']
                )"""),
            'hello.py': '',
            'setup.cfg': DALS("""
                [sdist]
                formats=zip
                """)
        }

        build_files(files)

        build_backend = self.get_build_backend()
        build_backend.build_sdist("temp")

    _relative_path_import_files = {
        'setup.py': DALS("""
            __import__('setuptools').setup(
                name='foo',
                version=__import__('hello').__version__,
                py_modules=['hello']
            )"""),
        'hello.py': '__version__ = "0.0.0"',
        'setup.cfg': DALS("""
            [sdist]
            formats=zip
            """)
    }

    def test_build_sdist_relative_path_import(self, tmpdir_cwd):
        build_files(self._relative_path_import_files)
        build_backend = self.get_build_backend()
        with pytest.raises(ImportError):
            build_backend.build_sdist("temp")

    @pytest.mark.parametrize('setup_literal, requirements', [
        ("'foo'", ['foo']),
        ("['foo']", ['foo']),
        (r"'foo\n'", ['foo']),
        (r"'foo\n\n'", ['foo']),
        ("['foo', 'bar']", ['foo', 'bar']),
        (r"'# Has a comment line\nfoo'", ['foo']),
        (r"'foo # Has an inline comment'", ['foo']),
        (r"'foo \\\n >=3.0'", ['foo>=3.0']),
        (r"'foo\nbar'", ['foo', 'bar']),
        (r"'foo\nbar\n'", ['foo', 'bar']),
        (r"['foo\n', 'bar\n']", ['foo', 'bar']),
    ])
    @pytest.mark.parametrize('use_wheel', [True, False])
    def test_setup_requires(self, setup_literal, requirements, use_wheel,
                            tmpdir_cwd):

        files = {
            'setup.py': DALS("""
                from setuptools import setup

                setup(
                    name="qux",
                    version="0.0.0",
                    py_modules=["hello.py"],
                    setup_requires={setup_literal},
                )
            """).format(setup_literal=setup_literal),
            'hello.py': DALS("""
            def run():
                print('hello')
            """),
        }

        build_files(files)

        build_backend = self.get_build_backend()

        if use_wheel:
            base_requirements = ['wheel']
            get_requires = build_backend.get_requires_for_build_wheel
        else:
            base_requirements = []
            get_requires = build_backend.get_requires_for_build_sdist

        # Ensure that the build requirements are properly parsed
        expected = sorted(base_requirements + requirements)
        actual = get_requires()

        assert expected == sorted(actual)


class TestBuildMetaLegacyBackend(TestBuildMetaBackend):
    backend_name = 'setuptools.build_meta:__legacy__'

    # build_meta_legacy-specific tests
    def test_build_sdist_relative_path_import(self, tmpdir_cwd):
        # This must fail in build_meta, but must pass in build_meta_legacy
        build_files(self._relative_path_import_files)

        build_backend = self.get_build_backend()
        build_backend.build_sdist("temp")
