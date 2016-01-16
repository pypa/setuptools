import os
import stat

from setuptools.extern.six.moves import map

import pytest

from . import environment
from .files import build_files
from .textwrap import DALS
from . import contexts


class Environment(str):
    pass


class TestEggInfo(object):

    setup_script = DALS("""
        from setuptools import setup

        setup(
            name='foo',
            py_modules=['hello'],
            entry_points={'console_scripts': ['hi = hello.run']},
            zip_safe=False,
        )
        """)

    def _create_project(self):
        build_files({
            'setup.py': self.setup_script,
            'hello.py': DALS("""
                def run():
                    print('hello')
                """)
        })

    @pytest.yield_fixture
    def env(self):
        with contexts.tempdir(prefix='setuptools-test.') as env_dir:
            env = Environment(env_dir)
            os.chmod(env_dir, stat.S_IRWXU)
            subs = 'home', 'lib', 'scripts', 'data', 'egg-base'
            env.paths = dict(
                (dirname, os.path.join(env_dir, dirname))
                for dirname in subs
            )
            list(map(os.mkdir, env.paths.values()))
            build_files({
                env.paths['home']: {
                    '.pydistutils.cfg': DALS("""
                    [egg_info]
                    egg-base = %(egg-base)s
                    """ % env.paths)
                }
            })
            yield env

    def test_egg_base_installed_egg_info(self, tmpdir_cwd, env):
        self._create_project()

        self._run_install_command(tmpdir_cwd, env)
        actual = self._find_egg_info_files(env.paths['lib'])

        expected = [
            'PKG-INFO',
            'SOURCES.txt',
            'dependency_links.txt',
            'entry_points.txt',
            'not-zip-safe',
            'top_level.txt',
        ]
        assert sorted(actual) == expected

    def test_manifest_template_is_read(self, tmpdir_cwd, env):
        self._create_project()
        build_files({
            'MANIFEST.in': DALS("""
                recursive-include docs *.rst
            """),
            'docs': {
                'usage.rst': "Run 'hi'",
            }
        })
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        sources_txt = os.path.join(egg_info_dir, 'SOURCES.txt')
        assert 'docs/usage.rst' in open(sources_txt).read().split('\n')

    def _run_install_command(self, tmpdir_cwd, env):
        environ = os.environ.copy().update(
            HOME=env.paths['home'],
        )
        cmd = [
            'install',
            '--home', env.paths['home'],
            '--install-lib', env.paths['lib'],
            '--install-scripts', env.paths['scripts'],
            '--install-data', env.paths['data'],
        ]
        code, data = environment.run_setup_py(
            cmd=cmd,
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)]),
            data_stream=1,
            env=environ,
        )
        if code:
            raise AssertionError(data)

    def _find_egg_info_files(self, root):
        class DirList(list):
            def __init__(self, files, base):
                super(DirList, self).__init__(files)
                self.base = base

        results = (
            DirList(filenames, dirpath)
            for dirpath, dirnames, filenames in os.walk(root)
            if os.path.basename(dirpath) == 'EGG-INFO'
        )
        # expect exactly one result
        result, = results
        return result
