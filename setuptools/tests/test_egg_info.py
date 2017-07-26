import os
import glob
import re
import stat
import sys

from setuptools.command.egg_info import egg_info, manifest_maker
from setuptools.dist import Distribution
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

    dict_order_fails = pytest.mark.skipif(
        sys.version_info < (2, 7),
        reason="Intermittent failures on Python 2.6",
    )

    @dict_order_fails
    def test_egg_info_save_version_info_setup_empty(self, tmpdir_cwd, env):
        """
        When the egg_info section is empty or not present, running
        save_version_info should add the settings to the setup.cfg
        in a deterministic order, consistent with the ordering found
        on Python 2.7 with PYTHONHASHSEED=0.
        """
        setup_cfg = os.path.join(env.paths['home'], 'setup.cfg')
        dist = Distribution()
        ei = egg_info(dist)
        ei.initialize_options()
        ei.save_version_info(setup_cfg)

        with open(setup_cfg, 'r') as f:
            content = f.read()

        assert '[egg_info]' in content
        assert 'tag_build =' in content
        assert 'tag_date = 0' in content

        expected_order = 'tag_build', 'tag_date',

        self._validate_content_order(content, expected_order)

    @staticmethod
    def _validate_content_order(content, expected):
        """
        Assert that the strings in expected appear in content
        in order.
        """
        pattern = '.*'.join(expected)
        flags = re.MULTILINE | re.DOTALL
        assert re.search(pattern, content, flags)

    @dict_order_fails
    def test_egg_info_save_version_info_setup_defaults(self, tmpdir_cwd, env):
        """
        When running save_version_info on an existing setup.cfg
        with the 'default' values present from a previous run,
        the file should remain unchanged.
        """
        setup_cfg = os.path.join(env.paths['home'], 'setup.cfg')
        build_files({
            setup_cfg: DALS("""
            [egg_info]
            tag_build =
            tag_date = 0
            """),
        })
        dist = Distribution()
        ei = egg_info(dist)
        ei.initialize_options()
        ei.save_version_info(setup_cfg)

        with open(setup_cfg, 'r') as f:
            content = f.read()

        assert '[egg_info]' in content
        assert 'tag_build =' in content
        assert 'tag_date = 0' in content

        expected_order = 'tag_build', 'tag_date',

        self._validate_content_order(content, expected_order)

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

    def _setup_script_with_requires(self, requires_line):
        setup_script = DALS("""
            from setuptools import setup

            setup(
                name='foo',
                %s
                zip_safe=False,
            )
            """ % requires_line)
        build_files({
            'setup.py': setup_script,
        })

    mismatch_marker = "python_version<'{this_ver}'".format(
        this_ver=sys.version_info[0],
    )
    # Alternate equivalent syntax.
    mismatch_marker_alternate = 'python_version < "{this_ver}"'.format(
        this_ver=sys.version_info[0],
    )
    invalid_marker = "<=>++"

    def test_install_requires_with_marker(self, tmpdir_cwd, env):
        tmpl = 'install_requires=["barbazquux;{marker}"],'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [:{marker}]
             barbazquux
             ''').format(marker=self.mismatch_marker_alternate)
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_install_requires_with_extra(self, tmpdir_cwd, env):
        req = 'install_requires=["barbazquux [test]"],'
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env, cmd=['egg_info'])
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             barbazquux[test]
             ''')
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_install_requires_with_extra_and_marker(self, tmpdir_cwd, env):
        tmpl = 'install_requires=["barbazquux [test]; {marker}"],'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [:{marker}]
             barbazquux[test]
             ''').format(marker=self.mismatch_marker_alternate)
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_setup_requires_with_markers(self, tmpdir_cwd, env):
        tmpl = 'setup_requires=["barbazquux;{marker}"],'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_tests_require_with_markers(self, tmpdir_cwd, env):
        tmpl = 'tests_require=["barbazquux;{marker}"],'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(
            tmpdir_cwd, env, cmd=['test'], output="Ran 0 tests in")
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_extra(self, tmpdir_cwd, env):
        req = 'extras_require={"extra": ["barbazquux [test]"]},'
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env, cmd=['egg_info'])
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [extra]
             barbazquux[test]
             ''')
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_extra_and_marker_in_req(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{"extra": ["barbazquux [test]; {marker}"]}},'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [extra]

             [extra:{marker}]
             barbazquux[test]
             ''').format(marker=self.mismatch_marker_alternate)
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_marker(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{":{marker}": ["barbazquux"]}},'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [:{marker}]
             barbazquux
             ''').format(marker=self.mismatch_marker)
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_marker_in_req(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{"extra": ["barbazquux; {marker}"]}},'
        req = tmpl.format(marker=self.mismatch_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [extra]

             [extra:{marker}]
             barbazquux
             ''').format(marker=self.mismatch_marker_alternate)
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_invalid_marker(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{":{marker}": ["barbazquux"]}},'
        req = tmpl.format(marker=self.invalid_marker)
        self._setup_script_with_requires(req)
        with pytest.raises(AssertionError):
            self._run_install_command(tmpdir_cwd, env)
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_invalid_marker_in_req(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{"extra": ["barbazquux; {marker}"]}},'
        req = tmpl.format(marker=self.invalid_marker)
        self._setup_script_with_requires(req)
        with pytest.raises(AssertionError):
            self._run_install_command(tmpdir_cwd, env)
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_empty_section(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{"empty": []}},'
        req = tmpl.format(marker=self.invalid_marker)
        self._setup_script_with_requires(req)
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        with open(requires_txt) as fp:
            install_requires = fp.read()
        expected_requires = DALS('''
             [empty]
             ''').format(marker=self.mismatch_marker_alternate)
        assert install_requires.lstrip() == expected_requires

    def test_python_requires_egg_info(self, tmpdir_cwd, env):
        self._setup_script_with_requires(
            """python_requires='>=2.7.12',""")
        environ = os.environ.copy().update(
            HOME=env.paths['home'],
        )
        code, data = environment.run_setup_py(
            cmd=['egg_info'],
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)]),
            data_stream=1,
            env=environ,
        )
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        with open(os.path.join(egg_info_dir, 'PKG-INFO')) as pkginfo_file:
            pkg_info_lines = pkginfo_file.read().split('\n')
        assert 'Requires-Python: >=2.7.12' in pkg_info_lines
        assert 'Metadata-Version: 1.2' in pkg_info_lines

    def test_python_requires_install(self, tmpdir_cwd, env):
        self._setup_script_with_requires(
            """python_requires='>=1.2.3',""")
        self._run_install_command(tmpdir_cwd, env)
        egg_info_dir = self._find_egg_info_files(env.paths['lib']).base
        pkginfo = os.path.join(egg_info_dir, 'PKG-INFO')
        assert 'Requires-Python: >=1.2.3' in open(pkginfo).read().split('\n')

    def test_manifest_maker_warning_suppression(self):
        fixtures = [
            "standard file not found: should have one of foo.py, bar.py",
            "standard file 'setup.py' not found"
        ]

        for msg in fixtures:
            assert manifest_maker._should_suppress_warning(msg)

    def _run_install_command(self, tmpdir_cwd, env, cmd=None, output=None):
        environ = os.environ.copy().update(
            HOME=env.paths['home'],
        )
        if cmd is None:
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
        if output:
            assert output in data

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
