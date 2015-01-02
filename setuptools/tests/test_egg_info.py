import os
import tempfile
import shutil
import stat

from . import environment


class TestEggInfo:

    def _create_project(self):
        with open('setup.py', 'w') as f:
            f.write('from setuptools import setup\n')
            f.write('\n')
            f.write('setup(\n')
            f.write("    name='foo',\n")
            f.write("    py_modules=['hello'],\n")
            f.write("    entry_points={'console_scripts': ['hi = hello.run']},\n")
            f.write('    zip_safe=False,\n')
            f.write('    )\n')
        with open('hello.py', 'w') as f:
            f.write('def run():\n')
            f.write("    print('hello')\n")

    def test_egg_base_installed_egg_info(self, tmpdir_cwd):
        self._create_project()
        temp_dir = tempfile.mkdtemp(prefix='setuptools-test.')
        os.chmod(temp_dir, stat.S_IRWXU)
        try:
            paths = {}
            for dirname in ['home', 'lib', 'scripts', 'data', 'egg-base']:
                paths[dirname] = os.path.join(temp_dir, dirname)
                os.mkdir(paths[dirname])
            config = os.path.join(paths['home'], '.pydistutils.cfg')
            with open(config, 'w') as f:
                f.write('[egg_info]\n')
                f.write('egg-base = %s\n' % paths['egg-base'])
            environ = os.environ.copy()
            environ['HOME'] = paths['home']
            code, data = environment.run_setup_py(
                cmd=[
                    'install', '--home', paths['home'],
                    '--install-lib', paths['lib'],
                    '--install-scripts', paths['scripts'],
                    '--install-data', paths['data']],
                pypath=os.pathsep.join([paths['lib'], str(tmpdir_cwd)]),
                data_stream=1,
                env=environ)
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
        finally:
            shutil.rmtree(temp_dir)
