"""Tests for distutils.dist."""
import os
import io
import sys
import unittest
import warnings
import textwrap
import functools

from unittest import mock

import pytest

from distutils.dist import Distribution, fix_help_options
from distutils.cmd import Command

from test.support import captured_stdout, captured_stderr
from .py38compat import TESTFN
from distutils.tests import support
from distutils import log


class test_dist(Command):
    """Sample distutils extension command."""

    user_options = [
        ("sample-option=", "S", "help text"),
    ]

    def initialize_options(self):
        self.sample_option = None


class TestDistribution(Distribution):
    """Distribution subclasses that avoids the default search for
    configuration files.

    The ._config_files attribute must be set before
    .parse_config_files() is called.
    """

    def find_config_files(self):
        return self._config_files


@pytest.fixture
def clear_argv():
    del sys.argv[1:]


@support.combine_markers
@pytest.mark.usefixtures('save_env')
@pytest.mark.usefixtures('save_argv')
class TestDistributionBehavior(
    support.LoggingSilencer,
    support.TempdirManager,
):
    def create_distribution(self, configfiles=()):
        d = TestDistribution()
        d._config_files = configfiles
        d.parse_config_files()
        d.parse_command_line()
        return d

    def test_command_packages_unspecified(self, clear_argv):
        sys.argv.append("build")
        d = self.create_distribution()
        assert d.get_command_packages() == ["distutils.command"]

    def test_command_packages_cmdline(self, clear_argv):
        from distutils.tests.test_dist import test_dist

        sys.argv.extend(
            [
                "--command-packages",
                "foo.bar,distutils.tests",
                "test_dist",
                "-Ssometext",
            ]
        )
        d = self.create_distribution()
        # let's actually try to load our test command:
        assert d.get_command_packages() == [
            "distutils.command",
            "foo.bar",
            "distutils.tests",
        ]
        cmd = d.get_command_obj("test_dist")
        assert isinstance(cmd, test_dist)
        assert cmd.sample_option == "sometext"

    @unittest.skipIf(
        'distutils' not in Distribution.parse_config_files.__module__,
        'Cannot test when virtualenv has monkey-patched Distribution.',
    )
    def test_venv_install_options(self, request):
        sys.argv.append("install")
        request.addfinalizer(functools.partial(os.unlink, TESTFN))

        fakepath = '/somedir'

        with open(TESTFN, "w") as f:
            print(
                (
                    "[install]\n"
                    "install-base = {0}\n"
                    "install-platbase = {0}\n"
                    "install-lib = {0}\n"
                    "install-platlib = {0}\n"
                    "install-purelib = {0}\n"
                    "install-headers = {0}\n"
                    "install-scripts = {0}\n"
                    "install-data = {0}\n"
                    "prefix = {0}\n"
                    "exec-prefix = {0}\n"
                    "home = {0}\n"
                    "user = {0}\n"
                    "root = {0}"
                ).format(fakepath),
                file=f,
            )

        # Base case: Not in a Virtual Environment
        with mock.patch.multiple(sys, prefix='/a', base_prefix='/a'):
            d = self.create_distribution([TESTFN])

        option_tuple = (TESTFN, fakepath)

        result_dict = {
            'install_base': option_tuple,
            'install_platbase': option_tuple,
            'install_lib': option_tuple,
            'install_platlib': option_tuple,
            'install_purelib': option_tuple,
            'install_headers': option_tuple,
            'install_scripts': option_tuple,
            'install_data': option_tuple,
            'prefix': option_tuple,
            'exec_prefix': option_tuple,
            'home': option_tuple,
            'user': option_tuple,
            'root': option_tuple,
        }

        assert sorted(d.command_options.get('install').keys()) == sorted(
            result_dict.keys()
        )

        for (key, value) in d.command_options.get('install').items():
            assert value == result_dict[key]

        # Test case: In a Virtual Environment
        with mock.patch.multiple(sys, prefix='/a', base_prefix='/b'):
            d = self.create_distribution([TESTFN])

        for key in result_dict.keys():
            assert key not in d.command_options.get('install', {})

    def test_command_packages_configfile(self, request, clear_argv):
        sys.argv.append("build")
        request.addfinalizer(functools.partial(os.unlink, TESTFN))
        f = open(TESTFN, "w")
        try:
            print("[global]", file=f)
            print("command_packages = foo.bar, splat", file=f)
        finally:
            f.close()

        d = self.create_distribution([TESTFN])
        assert d.get_command_packages() == ["distutils.command", "foo.bar", "splat"]

        # ensure command line overrides config:
        sys.argv[1:] = ["--command-packages", "spork", "build"]
        d = self.create_distribution([TESTFN])
        assert d.get_command_packages() == ["distutils.command", "spork"]

        # Setting --command-packages to '' should cause the default to
        # be used even if a config file specified something else:
        sys.argv[1:] = ["--command-packages", "", "build"]
        d = self.create_distribution([TESTFN])
        assert d.get_command_packages() == ["distutils.command"]

    def test_empty_options(self, request):
        # an empty options dictionary should not stay in the
        # list of attributes

        # catching warnings
        warns = []

        def _warn(msg):
            warns.append(msg)

        request.addfinalizer(
            functools.partial(setattr, warnings, 'warn', warnings.warn)
        )
        warnings.warn = _warn
        dist = Distribution(
            attrs={
                'author': 'xxx',
                'name': 'xxx',
                'version': 'xxx',
                'url': 'xxxx',
                'options': {},
            }
        )

        assert len(warns) == 0
        assert 'options' not in dir(dist)

    def test_finalize_options(self):
        attrs = {'keywords': 'one,two', 'platforms': 'one,two'}

        dist = Distribution(attrs=attrs)
        dist.finalize_options()

        # finalize_option splits platforms and keywords
        assert dist.metadata.platforms == ['one', 'two']
        assert dist.metadata.keywords == ['one', 'two']

        attrs = {'keywords': 'foo bar', 'platforms': 'foo bar'}
        dist = Distribution(attrs=attrs)
        dist.finalize_options()
        assert dist.metadata.platforms == ['foo bar']
        assert dist.metadata.keywords == ['foo bar']

    def test_get_command_packages(self):
        dist = Distribution()
        assert dist.command_packages is None
        cmds = dist.get_command_packages()
        assert cmds == ['distutils.command']
        assert dist.command_packages == ['distutils.command']

        dist.command_packages = 'one,two'
        cmds = dist.get_command_packages()
        assert cmds == ['distutils.command', 'one', 'two']

    def test_announce(self):
        # make sure the level is known
        dist = Distribution()
        args = ('ok',)
        kwargs = {'level': 'ok2'}
        with pytest.raises(ValueError):
            dist.announce(args, kwargs)

    def test_find_config_files_disable(self):
        # Ticket #1180: Allow user to disable their home config file.
        temp_home = self.mkdtemp()
        if os.name == 'posix':
            user_filename = os.path.join(temp_home, ".pydistutils.cfg")
        else:
            user_filename = os.path.join(temp_home, "pydistutils.cfg")

        with open(user_filename, 'w') as f:
            f.write('[distutils]\n')

        def _expander(path):
            return temp_home

        old_expander = os.path.expanduser
        os.path.expanduser = _expander
        try:
            d = Distribution()
            all_files = d.find_config_files()

            d = Distribution(attrs={'script_args': ['--no-user-cfg']})
            files = d.find_config_files()
        finally:
            os.path.expanduser = old_expander

        # make sure --no-user-cfg disables the user cfg file
        assert len(all_files) - 1 == len(files)


@pytest.mark.usefixtures('save_env')
@pytest.mark.usefixtures('save_argv')
class MetadataTestCase(support.TempdirManager):
    def format_metadata(self, dist):
        sio = io.StringIO()
        dist.metadata.write_pkg_file(sio)
        return sio.getvalue()

    def test_simple_metadata(self):
        attrs = {"name": "package", "version": "1.0"}
        dist = Distribution(attrs)
        meta = self.format_metadata(dist)
        assert "Metadata-Version: 1.0" in meta
        assert "provides:" not in meta.lower()
        assert "requires:" not in meta.lower()
        assert "obsoletes:" not in meta.lower()

    def test_provides(self):
        attrs = {
            "name": "package",
            "version": "1.0",
            "provides": ["package", "package.sub"],
        }
        dist = Distribution(attrs)
        assert dist.metadata.get_provides() == ["package", "package.sub"]
        assert dist.get_provides() == ["package", "package.sub"]
        meta = self.format_metadata(dist)
        assert "Metadata-Version: 1.1" in meta
        assert "requires:" not in meta.lower()
        assert "obsoletes:" not in meta.lower()

    def test_provides_illegal(self):
        with pytest.raises(ValueError):
            Distribution(
                {"name": "package", "version": "1.0", "provides": ["my.pkg (splat)"]},
            )

    def test_requires(self):
        attrs = {
            "name": "package",
            "version": "1.0",
            "requires": ["other", "another (==1.0)"],
        }
        dist = Distribution(attrs)
        assert dist.metadata.get_requires() == ["other", "another (==1.0)"]
        assert dist.get_requires() == ["other", "another (==1.0)"]
        meta = self.format_metadata(dist)
        assert "Metadata-Version: 1.1" in meta
        assert "provides:" not in meta.lower()
        assert "Requires: other" in meta
        assert "Requires: another (==1.0)" in meta
        assert "obsoletes:" not in meta.lower()

    def test_requires_illegal(self):
        with pytest.raises(ValueError):
            Distribution(
                {"name": "package", "version": "1.0", "requires": ["my.pkg (splat)"]},
            )

    def test_requires_to_list(self):
        attrs = {"name": "package", "requires": iter(["other"])}
        dist = Distribution(attrs)
        assert isinstance(dist.metadata.requires, list)

    def test_obsoletes(self):
        attrs = {
            "name": "package",
            "version": "1.0",
            "obsoletes": ["other", "another (<1.0)"],
        }
        dist = Distribution(attrs)
        assert dist.metadata.get_obsoletes() == ["other", "another (<1.0)"]
        assert dist.get_obsoletes() == ["other", "another (<1.0)"]
        meta = self.format_metadata(dist)
        assert "Metadata-Version: 1.1" in meta
        assert "provides:" not in meta.lower()
        assert "requires:" not in meta.lower()
        assert "Obsoletes: other" in meta
        assert "Obsoletes: another (<1.0)" in meta

    def test_obsoletes_illegal(self):
        with pytest.raises(ValueError):
            Distribution(
                {"name": "package", "version": "1.0", "obsoletes": ["my.pkg (splat)"]},
            )

    def test_obsoletes_to_list(self):
        attrs = {"name": "package", "obsoletes": iter(["other"])}
        dist = Distribution(attrs)
        assert isinstance(dist.metadata.obsoletes, list)

    def test_classifier(self):
        attrs = {
            'name': 'Boa',
            'version': '3.0',
            'classifiers': ['Programming Language :: Python :: 3'],
        }
        dist = Distribution(attrs)
        assert dist.get_classifiers() == ['Programming Language :: Python :: 3']
        meta = self.format_metadata(dist)
        assert 'Metadata-Version: 1.1' in meta

    def test_classifier_invalid_type(self):
        attrs = {
            'name': 'Boa',
            'version': '3.0',
            'classifiers': ('Programming Language :: Python :: 3',),
        }
        with captured_stderr() as error:
            d = Distribution(attrs)
        # should have warning about passing a non-list
        assert 'should be a list' in error.getvalue()
        # should be converted to a list
        assert isinstance(d.metadata.classifiers, list)
        assert d.metadata.classifiers == list(attrs['classifiers'])

    def test_keywords(self):
        attrs = {
            'name': 'Monty',
            'version': '1.0',
            'keywords': ['spam', 'eggs', 'life of brian'],
        }
        dist = Distribution(attrs)
        assert dist.get_keywords() == ['spam', 'eggs', 'life of brian']

    def test_keywords_invalid_type(self):
        attrs = {
            'name': 'Monty',
            'version': '1.0',
            'keywords': ('spam', 'eggs', 'life of brian'),
        }
        with captured_stderr() as error:
            d = Distribution(attrs)
        # should have warning about passing a non-list
        assert 'should be a list' in error.getvalue()
        # should be converted to a list
        assert isinstance(d.metadata.keywords, list)
        assert d.metadata.keywords == list(attrs['keywords'])

    def test_platforms(self):
        attrs = {
            'name': 'Monty',
            'version': '1.0',
            'platforms': ['GNU/Linux', 'Some Evil Platform'],
        }
        dist = Distribution(attrs)
        assert dist.get_platforms() == ['GNU/Linux', 'Some Evil Platform']

    def test_platforms_invalid_types(self):
        attrs = {
            'name': 'Monty',
            'version': '1.0',
            'platforms': ('GNU/Linux', 'Some Evil Platform'),
        }
        with captured_stderr() as error:
            d = Distribution(attrs)
        # should have warning about passing a non-list
        assert 'should be a list' in error.getvalue()
        # should be converted to a list
        assert isinstance(d.metadata.platforms, list)
        assert d.metadata.platforms == list(attrs['platforms'])

    def test_download_url(self):
        attrs = {
            'name': 'Boa',
            'version': '3.0',
            'download_url': 'http://example.org/boa',
        }
        dist = Distribution(attrs)
        meta = self.format_metadata(dist)
        assert 'Metadata-Version: 1.1' in meta

    def test_long_description(self):
        long_desc = textwrap.dedent(
            """\
        example::
              We start here
            and continue here
          and end here."""
        )
        attrs = {"name": "package", "version": "1.0", "long_description": long_desc}

        dist = Distribution(attrs)
        meta = self.format_metadata(dist)
        meta = meta.replace('\n' + 8 * ' ', '\n')
        assert long_desc in meta

    def test_custom_pydistutils(self):
        # fixes #2166
        # make sure pydistutils.cfg is found
        if os.name == 'posix':
            user_filename = ".pydistutils.cfg"
        else:
            user_filename = "pydistutils.cfg"

        temp_dir = self.mkdtemp()
        user_filename = os.path.join(temp_dir, user_filename)
        f = open(user_filename, 'w')
        try:
            f.write('.')
        finally:
            f.close()

        try:
            dist = Distribution()

            # linux-style
            if sys.platform in ('linux', 'darwin'):
                os.environ['HOME'] = temp_dir
                files = dist.find_config_files()
                assert user_filename in files

            # win32-style
            if sys.platform == 'win32':
                # home drive should be found
                os.environ['USERPROFILE'] = temp_dir
                files = dist.find_config_files()
                assert user_filename in files, '{!r} not found in {!r}'.format(
                    user_filename, files
                )
        finally:
            os.remove(user_filename)

    def test_fix_help_options(self):
        help_tuples = [('a', 'b', 'c', 'd'), (1, 2, 3, 4)]
        fancy_options = fix_help_options(help_tuples)
        assert fancy_options[0] == ('a', 'b', 'c')
        assert fancy_options[1] == (1, 2, 3)

    def test_show_help(self):
        # smoke test, just makes sure some help is displayed
        self.addCleanup(log.set_threshold, log._global_log.threshold)
        dist = Distribution()
        sys.argv = []
        dist.help = 1
        dist.script_name = 'setup.py'
        with captured_stdout() as s:
            dist.parse_command_line()

        output = [line for line in s.getvalue().split('\n') if line.strip() != '']
        assert output

    def test_read_metadata(self):
        attrs = {
            "name": "package",
            "version": "1.0",
            "long_description": "desc",
            "description": "xxx",
            "download_url": "http://example.com",
            "keywords": ['one', 'two'],
            "requires": ['foo'],
        }

        dist = Distribution(attrs)
        metadata = dist.metadata

        # write it then reloads it
        PKG_INFO = io.StringIO()
        metadata.write_pkg_file(PKG_INFO)
        PKG_INFO.seek(0)
        metadata.read_pkg_file(PKG_INFO)

        assert metadata.name == "package"
        assert metadata.version == "1.0"
        assert metadata.description == "xxx"
        assert metadata.download_url == 'http://example.com'
        assert metadata.keywords == ['one', 'two']
        assert metadata.platforms is None
        assert metadata.obsoletes is None
        assert metadata.requires == ['foo']
