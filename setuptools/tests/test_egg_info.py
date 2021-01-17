import sys
import ast
import os
import glob
import re
import stat
import time

from setuptools.command.egg_info import (
    egg_info, manifest_maker, EggInfoDeprecationWarning, get_pkg_info_revision,
)
from setuptools.dist import Distribution

import pytest

from . import environment
from .files import build_files
from .textwrap import DALS
from . import contexts


class Environment(str):
    pass


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
        build_files({
            'setup.py': self.setup_script,
            'hello.py': DALS("""
                def run():
                    print('hello')
                """)
        })

    @pytest.fixture
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

    def test_egg_info_save_version_info_setup_empty(self, tmpdir_cwd, env):
        """
        When the egg_info section is empty or not present, running
        save_version_info should add the settings to the setup.cfg
        in a deterministic order.
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

    def test_expected_files_produced(self, tmpdir_cwd, env):
        self._create_project()

        self._run_egg_info_command(tmpdir_cwd, env)
        actual = os.listdir('foo.egg-info')

        expected = [
            'PKG-INFO',
            'SOURCES.txt',
            'dependency_links.txt',
            'entry_points.txt',
            'not-zip-safe',
            'top_level.txt',
        ]
        assert sorted(actual) == expected

    def test_license_is_a_string(self, tmpdir_cwd, env):
        setup_config = DALS("""
            [metadata]
            name=foo
            version=0.0.1
            license=file:MIT
            """)

        setup_script = DALS("""
            from setuptools import setup

            setup()
            """)

        build_files({'setup.py': setup_script,
                     'setup.cfg': setup_config})

        # This command should fail with a ValueError, but because it's
        # currently configured to use a subprocess, the actual traceback
        # object is lost and we need to parse it from stderr
        with pytest.raises(AssertionError) as exc:
            self._run_egg_info_command(tmpdir_cwd, env)

        # Hopefully this is not too fragile: the only argument to the
        # assertion error should be a traceback, ending with:
        #     ValueError: ....
        #
        #     assert not 1
        tb = exc.value.args[0].split('\n')
        assert tb[-3].lstrip().startswith('ValueError')

    def test_rebuilt(self, tmpdir_cwd, env):
        """Ensure timestamps are updated when the command is re-run."""
        self._create_project()

        self._run_egg_info_command(tmpdir_cwd, env)
        timestamp_a = os.path.getmtime('foo.egg-info')

        # arbitrary sleep just to handle *really* fast systems
        time.sleep(.001)

        self._run_egg_info_command(tmpdir_cwd, env)
        timestamp_b = os.path.getmtime('foo.egg-info')

        assert timestamp_a != timestamp_b

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
        self._run_egg_info_command(tmpdir_cwd, env)
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        sources_txt = os.path.join(egg_info_dir, 'SOURCES.txt')
        with open(sources_txt) as f:
            assert 'docs/usage.rst' in f.read().split('\n')

    def _setup_script_with_requires(self, requires, use_setup_cfg=False):
        setup_script = DALS(
            '''
            from setuptools import setup

            setup(name='foo', zip_safe=False, %s)
            '''
        ) % ('' if use_setup_cfg else requires)
        setup_config = requires if use_setup_cfg else ''
        build_files({'setup.py': setup_script,
                     'setup.cfg': setup_config})

    mismatch_marker = "python_version<'{this_ver}'".format(
        this_ver=sys.version_info[0],
    )
    # Alternate equivalent syntax.
    mismatch_marker_alternate = 'python_version < "{this_ver}"'.format(
        this_ver=sys.version_info[0],
    )
    invalid_marker = "<=>++"

    class RequiresTestHelper:

        @staticmethod
        def parametrize(*test_list, **format_dict):
            idlist = []
            argvalues = []
            for test in test_list:
                test_params = test.lstrip().split('\n\n', 3)
                name_kwargs = test_params.pop(0).split('\n')
                if len(name_kwargs) > 1:
                    val = name_kwargs[1].strip()
                    install_cmd_kwargs = ast.literal_eval(val)
                else:
                    install_cmd_kwargs = {}
                name = name_kwargs[0].strip()
                setup_py_requires, setup_cfg_requires, expected_requires = (
                    DALS(a).format(**format_dict) for a in test_params
                )
                for id_, requires, use_cfg in (
                    (name, setup_py_requires, False),
                    (name + '_in_setup_cfg', setup_cfg_requires, True),
                ):
                    idlist.append(id_)
                    marks = ()
                    if requires.startswith('@xfail\n'):
                        requires = requires[7:]
                        marks = pytest.mark.xfail
                    argvalues.append(pytest.param(requires, use_cfg,
                                                  expected_requires,
                                                  install_cmd_kwargs,
                                                  marks=marks))
            return pytest.mark.parametrize(
                'requires,use_setup_cfg,'
                'expected_requires,install_cmd_kwargs',
                argvalues, ids=idlist,
            )

    @RequiresTestHelper.parametrize(
        # Format of a test:
        #
        # id
        # install_cmd_kwargs [optional]
        #
        # requires block (when used in setup.py)
        #
        # requires block (when used in setup.cfg)
        #
        # expected contents of requires.txt

        '''
        install_requires_deterministic

        install_requires=["wheel>=0.5", "pytest"]

        [options]
        install_requires =
            wheel>=0.5
            pytest

        wheel>=0.5
        pytest
        ''',

        '''
        install_requires_ordered

        install_requires=["pytest>=3.0.2,!=10.9999"]

        [options]
        install_requires =
            pytest>=3.0.2,!=10.9999

        pytest!=10.9999,>=3.0.2
        ''',

        '''
        install_requires_with_marker

        install_requires=["barbazquux;{mismatch_marker}"],

        [options]
        install_requires =
            barbazquux; {mismatch_marker}

        [:{mismatch_marker_alternate}]
        barbazquux
        ''',

        '''
        install_requires_with_extra
        {'cmd': ['egg_info']}

        install_requires=["barbazquux [test]"],

        [options]
        install_requires =
            barbazquux [test]

        barbazquux[test]
        ''',

        '''
        install_requires_with_extra_and_marker

        install_requires=["barbazquux [test]; {mismatch_marker}"],

        [options]
        install_requires =
            barbazquux [test]; {mismatch_marker}

        [:{mismatch_marker_alternate}]
        barbazquux[test]
        ''',

        '''
        setup_requires_with_markers

        setup_requires=["barbazquux;{mismatch_marker}"],

        [options]
        setup_requires =
            barbazquux; {mismatch_marker}

        ''',

        '''
        tests_require_with_markers
        {'cmd': ['test'], 'output': "Ran 0 tests in"}

        tests_require=["barbazquux;{mismatch_marker}"],

        [options]
        tests_require =
            barbazquux; {mismatch_marker}

        ''',

        '''
        extras_require_with_extra
        {'cmd': ['egg_info']}

        extras_require={{"extra": ["barbazquux [test]"]}},

        [options.extras_require]
        extra = barbazquux [test]

        [extra]
        barbazquux[test]
        ''',

        '''
        extras_require_with_extra_and_marker_in_req

        extras_require={{"extra": ["barbazquux [test]; {mismatch_marker}"]}},

        [options.extras_require]
        extra =
            barbazquux [test]; {mismatch_marker}

        [extra]

        [extra:{mismatch_marker_alternate}]
        barbazquux[test]
        ''',

        # FIXME: ConfigParser does not allow : in key names!
        '''
        extras_require_with_marker

        extras_require={{":{mismatch_marker}": ["barbazquux"]}},

        @xfail
        [options.extras_require]
        :{mismatch_marker} = barbazquux

        [:{mismatch_marker}]
        barbazquux
        ''',

        '''
        extras_require_with_marker_in_req

        extras_require={{"extra": ["barbazquux; {mismatch_marker}"]}},

        [options.extras_require]
        extra =
            barbazquux; {mismatch_marker}

        [extra]

        [extra:{mismatch_marker_alternate}]
        barbazquux
        ''',

        '''
        extras_require_with_empty_section

        extras_require={{"empty": []}},

        [options.extras_require]
        empty =

        [empty]
        ''',
        # Format arguments.
        invalid_marker=invalid_marker,
        mismatch_marker=mismatch_marker,
        mismatch_marker_alternate=mismatch_marker_alternate,
    )
    def test_requires(
            self, tmpdir_cwd, env, requires, use_setup_cfg,
            expected_requires, install_cmd_kwargs):
        self._setup_script_with_requires(requires, use_setup_cfg)
        self._run_egg_info_command(tmpdir_cwd, env, **install_cmd_kwargs)
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        requires_txt = os.path.join(egg_info_dir, 'requires.txt')
        if os.path.exists(requires_txt):
            with open(requires_txt) as fp:
                install_requires = fp.read()
        else:
            install_requires = ''
        assert install_requires.lstrip() == expected_requires
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_install_requires_unordered_disallowed(self, tmpdir_cwd, env):
        """
        Packages that pass unordered install_requires sequences
        should be rejected as they produce non-deterministic
        builds. See #458.
        """
        req = 'install_requires={"fake-factory==0.5.2", "pytz"}'
        self._setup_script_with_requires(req)
        with pytest.raises(AssertionError):
            self._run_egg_info_command(tmpdir_cwd, env)

    def test_extras_require_with_invalid_marker(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{":{marker}": ["barbazquux"]}},'
        req = tmpl.format(marker=self.invalid_marker)
        self._setup_script_with_requires(req)
        with pytest.raises(AssertionError):
            self._run_egg_info_command(tmpdir_cwd, env)
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_extras_require_with_invalid_marker_in_req(self, tmpdir_cwd, env):
        tmpl = 'extras_require={{"extra": ["barbazquux; {marker}"]}},'
        req = tmpl.format(marker=self.invalid_marker)
        self._setup_script_with_requires(req)
        with pytest.raises(AssertionError):
            self._run_egg_info_command(tmpdir_cwd, env)
        assert glob.glob(os.path.join(env.paths['lib'], 'barbazquux*')) == []

    def test_provides_extra(self, tmpdir_cwd, env):
        self._setup_script_with_requires(
            'extras_require={"foobar": ["barbazquux"]},')
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
        assert 'Provides-Extra: foobar' in pkg_info_lines
        assert 'Metadata-Version: 2.1' in pkg_info_lines

    def test_doesnt_provides_extra(self, tmpdir_cwd, env):
        self._setup_script_with_requires(
            '''install_requires=["spam ; python_version<'3.6'"]''')
        environ = os.environ.copy().update(
            HOME=env.paths['home'],
        )
        environment.run_setup_py(
            cmd=['egg_info'],
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)]),
            data_stream=1,
            env=environ,
        )
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        with open(os.path.join(egg_info_dir, 'PKG-INFO')) as pkginfo_file:
            pkg_info_text = pkginfo_file.read()
        assert 'Provides-Extra:' not in pkg_info_text

    @pytest.mark.parametrize("files, license_in_sources", [
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE
                              """),
            'LICENSE': "Test license"
        }, True),  # with license
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = INVALID_LICENSE
                              """),
            'LICENSE': "Test license"
        }, False),  # with an invalid license
        ({
            'setup.cfg': DALS("""
                              """),
            'LICENSE': "Test license"
        }, False),  # no license_file attribute
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE
                              """),
            'MANIFEST.in': "exclude LICENSE",
            'LICENSE': "Test license"
        }, False)  # license file is manually excluded
    ])
    def test_setup_cfg_license_file(
            self, tmpdir_cwd, env, files, license_in_sources):
        self._create_project()
        build_files(files)

        environment.run_setup_py(
            cmd=['egg_info'],
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)])
        )
        egg_info_dir = os.path.join('.', 'foo.egg-info')

        with open(os.path.join(egg_info_dir, 'SOURCES.txt')) as sources_file:
            sources_text = sources_file.read()

        if license_in_sources:
            assert 'LICENSE' in sources_text
        else:
            assert 'LICENSE' not in sources_text
            # for invalid license test
            assert 'INVALID_LICENSE' not in sources_text

    @pytest.mark.parametrize("files, incl_licenses, excl_licenses", [
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files =
                                  LICENSE-ABC
                                  LICENSE-XYZ
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, ['LICENSE-ABC', 'LICENSE-XYZ'], []),  # with licenses
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files = LICENSE-ABC, LICENSE-XYZ
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, ['LICENSE-ABC', 'LICENSE-XYZ'], []),  # with commas
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files =
                                  LICENSE-ABC
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, ['LICENSE-ABC'], ['LICENSE-XYZ']),  # with one license
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files =
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, [], ['LICENSE-ABC', 'LICENSE-XYZ']),  # empty
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files = LICENSE-XYZ
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, ['LICENSE-XYZ'], ['LICENSE-ABC']),  # on same line
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files =
                                  LICENSE-ABC
                                  INVALID_LICENSE
                              """),
            'LICENSE-ABC': "Test license"
        }, ['LICENSE-ABC'], ['INVALID_LICENSE']),  # with an invalid license
        ({
            'setup.cfg': DALS("""
                              """),
            'LICENSE': "Test license"
        }, [], ['LICENSE']),  # no license_files attribute
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files = LICENSE
                              """),
            'MANIFEST.in': "exclude LICENSE",
            'LICENSE': "Test license"
        }, [], ['LICENSE']),  # license file is manually excluded
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_files =
                                  LICENSE-ABC
                                  LICENSE-XYZ
                              """),
            'MANIFEST.in': "exclude LICENSE-XYZ",
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, ['LICENSE-ABC'], ['LICENSE-XYZ'])  # subset is manually excluded
    ])
    def test_setup_cfg_license_files(
            self, tmpdir_cwd, env, files, incl_licenses, excl_licenses):
        self._create_project()
        build_files(files)

        environment.run_setup_py(
            cmd=['egg_info'],
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)])
        )
        egg_info_dir = os.path.join('.', 'foo.egg-info')

        with open(os.path.join(egg_info_dir, 'SOURCES.txt')) as sources_file:
            sources_lines = list(line.strip() for line in sources_file)

        for lf in incl_licenses:
            assert sources_lines.count(lf) == 1

        for lf in excl_licenses:
            assert sources_lines.count(lf) == 0

    @pytest.mark.parametrize("files, incl_licenses, excl_licenses", [
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file =
                              license_files =
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
        }, [], ['LICENSE-ABC', 'LICENSE-XYZ']),  # both empty
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file =
                                  LICENSE-ABC
                                  LICENSE-XYZ
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-XYZ': "XYZ license"
            # license_file is still singular
        }, [], ['LICENSE-ABC', 'LICENSE-XYZ']),
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE-ABC
                              license_files =
                                  LICENSE-XYZ
                                  LICENSE-PQR
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-PQR': "PQR license",
            'LICENSE-XYZ': "XYZ license"
        }, ['LICENSE-ABC', 'LICENSE-PQR', 'LICENSE-XYZ'], []),  # combined
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE-ABC
                              license_files =
                                  LICENSE-ABC
                                  LICENSE-XYZ
                                  LICENSE-PQR
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-PQR': "PQR license",
            'LICENSE-XYZ': "XYZ license"
            # duplicate license
        }, ['LICENSE-ABC', 'LICENSE-PQR', 'LICENSE-XYZ'], []),
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE-ABC
                              license_files =
                                  LICENSE-XYZ
                              """),
            'LICENSE-ABC': "ABC license",
            'LICENSE-PQR': "PQR license",
            'LICENSE-XYZ': "XYZ license"
            # combined subset
        }, ['LICENSE-ABC', 'LICENSE-XYZ'], ['LICENSE-PQR']),
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE-ABC
                              license_files =
                                  LICENSE-XYZ
                                  LICENSE-PQR
                              """),
            'LICENSE-PQR': "Test license"
            # with invalid licenses
        }, ['LICENSE-PQR'], ['LICENSE-ABC', 'LICENSE-XYZ']),
        ({
            'setup.cfg': DALS("""
                              [metadata]
                              license_file = LICENSE-ABC
                              license_files =
                                LICENSE-PQR
                                LICENSE-XYZ
                              """),
            'MANIFEST.in': "exclude LICENSE-ABC\nexclude LICENSE-PQR",
            'LICENSE-ABC': "ABC license",
            'LICENSE-PQR': "PQR license",
            'LICENSE-XYZ': "XYZ license"
            # manually excluded
        }, ['LICENSE-XYZ'], ['LICENSE-ABC', 'LICENSE-PQR'])
    ])
    def test_setup_cfg_license_file_license_files(
            self, tmpdir_cwd, env, files, incl_licenses, excl_licenses):
        self._create_project()
        build_files(files)

        environment.run_setup_py(
            cmd=['egg_info'],
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)])
        )
        egg_info_dir = os.path.join('.', 'foo.egg-info')

        with open(os.path.join(egg_info_dir, 'SOURCES.txt')) as sources_file:
            sources_lines = list(line.strip() for line in sources_file)

        for lf in incl_licenses:
            assert sources_lines.count(lf) == 1

        for lf in excl_licenses:
            assert sources_lines.count(lf) == 0

    def test_long_description_content_type(self, tmpdir_cwd, env):
        # Test that specifying a `long_description_content_type` keyword arg to
        # the `setup` function results in writing a `Description-Content-Type`
        # line to the `PKG-INFO` file in the `<distribution>.egg-info`
        # directory.
        # `Description-Content-Type` is described at
        # https://github.com/pypa/python-packaging-user-guide/pull/258

        self._setup_script_with_requires(
            """long_description_content_type='text/markdown',""")
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
        expected_line = 'Description-Content-Type: text/markdown'
        assert expected_line in pkg_info_lines
        assert 'Metadata-Version: 2.1' in pkg_info_lines

    def test_project_urls(self, tmpdir_cwd, env):
        # Test that specifying a `project_urls` dict to the `setup`
        # function results in writing multiple `Project-URL` lines to
        # the `PKG-INFO` file in the `<distribution>.egg-info`
        # directory.
        # `Project-URL` is described at https://packaging.python.org
        #     /specifications/core-metadata/#project-url-multiple-use

        self._setup_script_with_requires(
            """project_urls={
                'Link One': 'https://example.com/one/',
                'Link Two': 'https://example.com/two/',
                },""")
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
        expected_line = 'Project-URL: Link One, https://example.com/one/'
        assert expected_line in pkg_info_lines
        expected_line = 'Project-URL: Link Two, https://example.com/two/'
        assert expected_line in pkg_info_lines
        assert 'Metadata-Version: 1.2' in pkg_info_lines

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

    def test_manifest_maker_warning_suppression(self):
        fixtures = [
            "standard file not found: should have one of foo.py, bar.py",
            "standard file 'setup.py' not found"
        ]

        for msg in fixtures:
            assert manifest_maker._should_suppress_warning(msg)

    def test_egg_info_includes_setup_py(self, tmpdir_cwd):
        self._create_project()
        dist = Distribution({"name": "foo", "version": "0.0.1"})
        dist.script_name = "non_setup.py"
        egg_info_instance = egg_info(dist)
        egg_info_instance.finalize_options()
        egg_info_instance.run()

        assert 'setup.py' in egg_info_instance.filelist.files

        with open(egg_info_instance.egg_info + "/SOURCES.txt") as f:
            sources = f.read().split('\n')
            assert 'setup.py' in sources

    def _run_egg_info_command(self, tmpdir_cwd, env, cmd=None, output=None):
        environ = os.environ.copy().update(
            HOME=env.paths['home'],
        )
        if cmd is None:
            cmd = [
                'egg_info',
            ]
        code, data = environment.run_setup_py(
            cmd=cmd,
            pypath=os.pathsep.join([env.paths['lib'], str(tmpdir_cwd)]),
            data_stream=1,
            env=environ,
        )
        assert not code, data

        if output:
            assert output in data

    def test_egg_info_tag_only_once(self, tmpdir_cwd, env):
        self._create_project()
        build_files({
            'setup.cfg': DALS("""
                              [egg_info]
                              tag_build = dev
                              tag_date = 0
                              tag_svn_revision = 0
                              """),
        })
        self._run_egg_info_command(tmpdir_cwd, env)
        egg_info_dir = os.path.join('.', 'foo.egg-info')
        with open(os.path.join(egg_info_dir, 'PKG-INFO')) as pkginfo_file:
            pkg_info_lines = pkginfo_file.read().split('\n')
        assert 'Version: 0.0.0.dev0' in pkg_info_lines

    def test_get_pkg_info_revision_deprecated(self):
        pytest.warns(EggInfoDeprecationWarning, get_pkg_info_revision)
