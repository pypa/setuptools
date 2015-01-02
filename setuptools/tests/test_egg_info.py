import os
import stat

from . import environment
from .textwrap import DALS
from . import contexts


class TestEggInfo:

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
        with open('setup.py', 'w') as f:
            f.write(self.setup_script)

        with open('hello.py', 'w') as f:
            f.write(DALS("""
                def run():
                    print('hello')
                """))

    def test_egg_base_installed_egg_info(self, tmpdir_cwd):
        self._create_project()
        with contexts.tempdir(prefix='setuptools-test.') as temp_dir:
            os.chmod(temp_dir, stat.S_IRWXU)
            subs = 'home', 'lib', 'scripts', 'data', 'egg-base'
            paths = dict(
                (dirname, os.path.join(temp_dir, dirname))
                for dirname in subs
            )
            list(map(os.mkdir, paths.values()))
            config = os.path.join(paths['home'], '.pydistutils.cfg')
            with open(config, 'w') as f:
                f.write(DALS("""
                    [egg_info]
                    egg-base = %(egg-base)s
                    """ % paths
                ))
            environ = os.environ.copy()
            environ['HOME'] = paths['home']
            cmd = [
                'install',
                '--home', paths['home'],
                '--install-lib', paths['lib'],
                '--install-scripts', paths['scripts'],
                '--install-data', paths['data'],
            ]
            code, data = environment.run_setup_py(
                cmd=cmd,
                pypath=os.pathsep.join([paths['lib'], str(tmpdir_cwd)]),
                data_stream=1,
                env=environ,
            )
            if code:
                raise AssertionError(data)
            egg_info = None
            for dirpath, dirnames, filenames in os.walk(paths['lib']):
                if os.path.basename(dirpath) == 'EGG-INFO':
                    egg_info = sorted(filenames)

            expected = [
                'PKG-INFO',
                'SOURCES.txt',
                'dependency_links.txt',
                'entry_points.txt',
                'not-zip-safe',
                'top_level.txt',
            ]
            assert egg_info == expected
