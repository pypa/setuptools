"""Tests for distutils.util."""
import os
import sys
import unittest
import sysconfig as stdlib_sysconfig
from copy import copy
from unittest import mock

import pytest

from distutils.util import (
    get_platform,
    convert_path,
    change_root,
    check_environ,
    split_quoted,
    strtobool,
    rfc822_escape,
    byte_compile,
    grok_environment_error,
    get_host_platform,
)
from distutils import util  # used to patch _environ_checked
from distutils import sysconfig
from distutils.errors import DistutilsPlatformError, DistutilsByteCompileError


@pytest.mark.usefixtures('save_env')
class UtilTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        # saving the environment
        self.name = os.name
        self.platform = sys.platform
        self.version = sys.version
        self.sep = os.sep
        self.join = os.path.join
        self.isabs = os.path.isabs
        self.splitdrive = os.path.splitdrive
        self._config_vars = copy(sysconfig._config_vars)

        # patching os.uname
        if hasattr(os, 'uname'):
            self.uname = os.uname
            self._uname = os.uname()
        else:
            self.uname = None
            self._uname = None

        os.uname = self._get_uname

    def tearDown(self):
        # getting back the environment
        os.name = self.name
        sys.platform = self.platform
        sys.version = self.version
        os.sep = self.sep
        os.path.join = self.join
        os.path.isabs = self.isabs
        os.path.splitdrive = self.splitdrive
        if self.uname is not None:
            os.uname = self.uname
        else:
            del os.uname
        sysconfig._config_vars = copy(self._config_vars)
        super().tearDown()

    def _set_uname(self, uname):
        self._uname = uname

    def _get_uname(self):
        return self._uname

    def test_get_host_platform(self):
        with unittest.mock.patch('os.name', 'nt'):
            with unittest.mock.patch('sys.version', '... [... (ARM64)]'):
                assert get_host_platform() == 'win-arm64'
            with unittest.mock.patch('sys.version', '... [... (ARM)]'):
                assert get_host_platform() == 'win-arm32'

        with unittest.mock.patch('sys.version_info', (3, 9, 0, 'final', 0)):
            assert get_host_platform() == stdlib_sysconfig.get_platform()

    def test_get_platform(self):
        with unittest.mock.patch('os.name', 'nt'):
            with unittest.mock.patch.dict('os.environ', {'VSCMD_ARG_TGT_ARCH': 'x86'}):
                assert get_platform() == 'win32'
            with unittest.mock.patch.dict('os.environ', {'VSCMD_ARG_TGT_ARCH': 'x64'}):
                assert get_platform() == 'win-amd64'
            with unittest.mock.patch.dict('os.environ', {'VSCMD_ARG_TGT_ARCH': 'arm'}):
                assert get_platform() == 'win-arm32'
            with unittest.mock.patch.dict(
                'os.environ', {'VSCMD_ARG_TGT_ARCH': 'arm64'}
            ):
                assert get_platform() == 'win-arm64'

    def test_convert_path(self):
        # linux/mac
        os.sep = '/'

        def _join(path):
            return '/'.join(path)

        os.path.join = _join

        assert convert_path('/home/to/my/stuff') == '/home/to/my/stuff'

        # win
        os.sep = '\\'

        def _join(*path):
            return '\\'.join(path)

        os.path.join = _join

        with pytest.raises(ValueError):
            convert_path('/home/to/my/stuff')
        with pytest.raises(ValueError):
            convert_path('home/to/my/stuff/')

        assert convert_path('home/to/my/stuff') == 'home\\to\\my\\stuff'
        assert convert_path('.') == os.curdir

    def test_change_root(self):
        # linux/mac
        os.name = 'posix'

        def _isabs(path):
            return path[0] == '/'

        os.path.isabs = _isabs

        def _join(*path):
            return '/'.join(path)

        os.path.join = _join

        assert change_root('/root', '/old/its/here') == '/root/old/its/here'
        assert change_root('/root', 'its/here') == '/root/its/here'

        # windows
        os.name = 'nt'

        def _isabs(path):
            return path.startswith('c:\\')

        os.path.isabs = _isabs

        def _splitdrive(path):
            if path.startswith('c:'):
                return ('', path.replace('c:', ''))
            return ('', path)

        os.path.splitdrive = _splitdrive

        def _join(*path):
            return '\\'.join(path)

        os.path.join = _join

        assert (
            change_root('c:\\root', 'c:\\old\\its\\here') == 'c:\\root\\old\\its\\here'
        )
        assert change_root('c:\\root', 'its\\here') == 'c:\\root\\its\\here'

        # BugsBunny os (it's a great os)
        os.name = 'BugsBunny'
        with pytest.raises(DistutilsPlatformError):
            change_root('c:\\root', 'its\\here')

        # XXX platforms to be covered: mac

    def test_check_environ(self):
        util._environ_checked = 0
        os.environ.pop('HOME', None)

        check_environ()

        assert os.environ['PLAT'] == get_platform()
        assert util._environ_checked == 1

    @unittest.skipUnless(os.name == 'posix', 'specific to posix')
    def test_check_environ_getpwuid(self):
        util._environ_checked = 0
        os.environ.pop('HOME', None)

        import pwd

        # only set pw_dir field, other fields are not used
        result = pwd.struct_passwd(
            (None, None, None, None, None, '/home/distutils', None)
        )
        with mock.patch.object(pwd, 'getpwuid', return_value=result):
            check_environ()
            assert os.environ['HOME'] == '/home/distutils'

        util._environ_checked = 0
        os.environ.pop('HOME', None)

        # bpo-10496: Catch pwd.getpwuid() error
        with mock.patch.object(pwd, 'getpwuid', side_effect=KeyError):
            check_environ()
            assert 'HOME' not in os.environ

    def test_split_quoted(self):
        assert split_quoted('""one"" "two" \'three\' \\four') == [
            'one',
            'two',
            'three',
            'four',
        ]

    def test_strtobool(self):
        yes = ('y', 'Y', 'yes', 'True', 't', 'true', 'True', 'On', 'on', '1')
        no = ('n', 'no', 'f', 'false', 'off', '0', 'Off', 'No', 'N')

        for y in yes:
            assert strtobool(y)

        for n in no:
            assert not strtobool(n)

    def test_rfc822_escape(self):
        header = 'I am a\npoor\nlonesome\nheader\n'
        res = rfc822_escape(header)
        wanted = ('I am a%(8s)spoor%(8s)slonesome%(8s)s' 'header%(8s)s') % {
            '8s': '\n' + 8 * ' '
        }
        assert res == wanted

    def test_dont_write_bytecode(self):
        # makes sure byte_compile raise a DistutilsError
        # if sys.dont_write_bytecode is True
        old_dont_write_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            with pytest.raises(DistutilsByteCompileError):
                byte_compile([])
        finally:
            sys.dont_write_bytecode = old_dont_write_bytecode

    def test_grok_environment_error(self):
        # test obsolete function to ensure backward compat (#4931)
        exc = IOError("Unable to find batch file")
        msg = grok_environment_error(exc)
        assert msg == "error: Unable to find batch file"
