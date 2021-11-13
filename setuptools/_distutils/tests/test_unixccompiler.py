"""Tests for distutils.unixccompiler."""
import os
import sys
import unittest
from test.support import run_unittest

from .py38compat import EnvironmentVarGuard

from distutils import sysconfig
from distutils.errors import DistutilsPlatformError
from distutils.unixccompiler import UnixCCompiler
from distutils.util import _clear_cached_macosx_ver

class UnixCCompilerTestCase(unittest.TestCase):

    def setUp(self):
        self._backup_platform = sys.platform
        self._backup_get_config_var = sysconfig.get_config_var
        self._backup_get_config_vars = sysconfig.get_config_vars
        class CompilerWrapper(UnixCCompiler):
            def rpath_foo(self):
                return self.runtime_library_dir_option('/foo')
        self.cc = CompilerWrapper()

    def tearDown(self):
        sys.platform = self._backup_platform
        sysconfig.get_config_var = self._backup_get_config_var
        sysconfig.get_config_vars = self._backup_get_config_vars

    @unittest.skipIf(sys.platform == 'win32', "can't test on Windows")
    def test_runtime_libdir_option(self):
        # Issue #5900; GitHub Issue #37
        #
        # Ensure RUNPATH is added to extension modules with RPATH if
        # GNU ld is used

        # darwin
        sys.platform = 'darwin'
        darwin_ver_var = 'MACOSX_DEPLOYMENT_TARGET'
        darwin_rpath_flag = '-Wl,-rpath,/foo'
        darwin_lib_flag = '-L/foo'

        # (macOS version from syscfg, macOS version from env var) -> flag
        # Version value of None generates two tests: as None and as empty string
        # Expected flag value of None means an mismatch exception is expected
        darwin_test_cases = [
            ((None    , None    ), darwin_lib_flag),
            ((None    , '11'    ), darwin_rpath_flag),
            (('10'    , None    ), darwin_lib_flag),
            (('10.3'  , None    ), darwin_lib_flag),
            (('10.3.1', None    ), darwin_lib_flag),
            (('10.5'  , None    ), darwin_rpath_flag),
            (('10.5.1', None    ), darwin_rpath_flag),
            (('10.3'  , '10.3'  ), darwin_lib_flag),
            (('10.3'  , '10.5'  ), darwin_rpath_flag),
            (('10.5'  , '10.3'  ), darwin_lib_flag),
            (('10.5'  , '11'    ), darwin_rpath_flag),
            (('10.4'  , '10'    ), None),
        ]

        def make_darwin_gcv(syscfg_macosx_ver):
            def gcv(var):
                if var == darwin_ver_var:
                    return syscfg_macosx_ver
                return "xxx"
            return gcv

        def do_darwin_test(syscfg_macosx_ver, env_macosx_ver, expected_flag):
            env = os.environ
            msg = "macOS version = (sysconfig=%r, env=%r)" % \
                    (syscfg_macosx_ver, env_macosx_ver)

            # Save
            old_gcv = sysconfig.get_config_var
            old_env_macosx_ver = env.get(darwin_ver_var)

            # Setup environment
            _clear_cached_macosx_ver()
            sysconfig.get_config_var = make_darwin_gcv(syscfg_macosx_ver)
            if env_macosx_ver is not None:
                env[darwin_ver_var] = env_macosx_ver
            elif darwin_ver_var in env:
                env.pop(darwin_ver_var)

            # Run the test
            if expected_flag is not None:
                self.assertEqual(self.cc.rpath_foo(), expected_flag, msg=msg)
            else:
                with self.assertRaisesRegex(DistutilsPlatformError,
                        darwin_ver_var + r' mismatch', msg=msg):
                    self.cc.rpath_foo()

            # Restore
            if old_env_macosx_ver is not None:
                env[darwin_ver_var] = old_env_macosx_ver
            elif darwin_ver_var in env:
                env.pop(darwin_ver_var)
            sysconfig.get_config_var = old_gcv
            _clear_cached_macosx_ver()

        for macosx_vers, expected_flag in darwin_test_cases:
            syscfg_macosx_ver, env_macosx_ver = macosx_vers
            do_darwin_test(syscfg_macosx_ver, env_macosx_ver, expected_flag)
            # Bonus test cases with None interpreted as empty string
            if syscfg_macosx_ver is None:
                do_darwin_test("", env_macosx_ver, expected_flag)
            if env_macosx_ver is None:
                do_darwin_test(syscfg_macosx_ver, "", expected_flag)
            if syscfg_macosx_ver is None and env_macosx_ver is None:
                do_darwin_test("", "", expected_flag)

        old_gcv = sysconfig.get_config_var

        # hp-ux
        sys.platform = 'hp-ux'
        def gcv(v):
            return 'xxx'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), ['+s', '-L/foo'])

        def gcv(v):
            return 'gcc'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), ['-Wl,+s', '-L/foo'])

        def gcv(v):
            return 'g++'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), ['-Wl,+s', '-L/foo'])

        sysconfig.get_config_var = old_gcv

        # GCC GNULD
        sys.platform = 'bar'
        def gcv(v):
            if v == 'CC':
                return 'gcc'
            elif v == 'GNULD':
                return 'yes'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), '-Wl,--enable-new-dtags,-R/foo')

        def gcv(v):
            if v == 'CC':
                return 'gcc -pthread -B /bar'
            elif v == 'GNULD':
                return 'yes'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), '-Wl,--enable-new-dtags,-R/foo')

        # GCC non-GNULD
        sys.platform = 'bar'
        def gcv(v):
            if v == 'CC':
                return 'gcc'
            elif v == 'GNULD':
                return 'no'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), '-Wl,-R/foo')

        # GCC GNULD with fully qualified configuration prefix
        # see #7617
        sys.platform = 'bar'
        def gcv(v):
            if v == 'CC':
                return 'x86_64-pc-linux-gnu-gcc-4.4.2'
            elif v == 'GNULD':
                return 'yes'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), '-Wl,--enable-new-dtags,-R/foo')

        # non-GCC GNULD
        sys.platform = 'bar'
        def gcv(v):
            if v == 'CC':
                return 'cc'
            elif v == 'GNULD':
                return 'yes'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), '-Wl,--enable-new-dtags,-R/foo')

        # non-GCC non-GNULD
        sys.platform = 'bar'
        def gcv(v):
            if v == 'CC':
                return 'cc'
            elif v == 'GNULD':
                return 'no'
        sysconfig.get_config_var = gcv
        self.assertEqual(self.cc.rpath_foo(), '-Wl,-R/foo')

    @unittest.skipIf(sys.platform == 'win32', "can't test on Windows")
    def test_cc_overrides_ldshared(self):
        # Issue #18080:
        # ensure that setting CC env variable also changes default linker
        def gcv(v):
            if v == 'LDSHARED':
                return 'gcc-4.2 -bundle -undefined dynamic_lookup '
            return 'gcc-4.2'

        def gcvs(*args, _orig=sysconfig.get_config_vars):
            if args:
                return list(map(sysconfig.get_config_var, args))
            return _orig()
        sysconfig.get_config_var = gcv
        sysconfig.get_config_vars = gcvs
        with EnvironmentVarGuard() as env:
            env['CC'] = 'my_cc'
            del env['LDSHARED']
            sysconfig.customize_compiler(self.cc)
        self.assertEqual(self.cc.linker_so[0], 'my_cc')

    @unittest.skipIf(sys.platform == 'win32', "can't test on Windows")
    def test_explicit_ldshared(self):
        # Issue #18080:
        # ensure that setting CC env variable does not change
        #   explicit LDSHARED setting for linker
        def gcv(v):
            if v == 'LDSHARED':
                return 'gcc-4.2 -bundle -undefined dynamic_lookup '
            return 'gcc-4.2'

        def gcvs(*args, _orig=sysconfig.get_config_vars):
            if args:
                return list(map(sysconfig.get_config_var, args))
            return _orig()
        sysconfig.get_config_var = gcv
        sysconfig.get_config_vars = gcvs
        with EnvironmentVarGuard() as env:
            env['CC'] = 'my_cc'
            env['LDSHARED'] = 'my_ld -bundle -dynamic'
            sysconfig.customize_compiler(self.cc)
        self.assertEqual(self.cc.linker_so[0], 'my_ld')

    def test_has_function(self):
        # Issue https://github.com/pypa/distutils/issues/64:
        # ensure that setting output_dir does not raise
        # FileNotFoundError: [Errno 2] No such file or directory: 'a.out'
        self.cc.output_dir = 'scratch'
        self.cc.has_function('abort', includes=['stdlib.h'])


def test_suite():
    return unittest.makeSuite(UnixCCompilerTestCase)

if __name__ == "__main__":
    run_unittest(test_suite())
