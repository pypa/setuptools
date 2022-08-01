"""Tests for distutils.sysconfig."""
import contextlib
import os
import shutil
import subprocess
import sys
import textwrap
import unittest

import pytest
import jaraco.envs

import distutils
from distutils import sysconfig
from distutils.ccompiler import get_default_compiler
from distutils.unixccompiler import UnixCCompiler
from test.support import swap_item

from .py38compat import TESTFN


@pytest.mark.usefixtures('save_env')
class SysconfigTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.makefile = None

    def tearDown(self):
        if self.makefile is not None:
            os.unlink(self.makefile)
        self.cleanup_testfn()
        super().tearDown()

    def cleanup_testfn(self):
        if os.path.isfile(TESTFN):
            os.remove(TESTFN)
        elif os.path.isdir(TESTFN):
            shutil.rmtree(TESTFN)

    def test_get_config_h_filename(self):
        config_h = sysconfig.get_config_h_filename()
        assert os.path.isfile(config_h), config_h

    @unittest.skipIf(
        sys.platform == 'win32', 'Makefile only exists on Unix like systems'
    )
    @unittest.skipIf(
        sys.implementation.name != 'cpython', 'Makefile only exists in CPython'
    )
    def test_get_makefile_filename(self):
        makefile = sysconfig.get_makefile_filename()
        assert os.path.isfile(makefile), makefile

    def test_get_python_lib(self):
        # XXX doesn't work on Linux when Python was never installed before
        # self.assertTrue(os.path.isdir(lib_dir), lib_dir)
        # test for pythonxx.lib?
        assert sysconfig.get_python_lib() != sysconfig.get_python_lib(prefix=TESTFN)

    def test_get_config_vars(self):
        cvars = sysconfig.get_config_vars()
        assert isinstance(cvars, dict)
        assert cvars

    @unittest.skip('sysconfig.IS_PYPY')
    def test_srcdir(self):
        # See Issues #15322, #15364.
        srcdir = sysconfig.get_config_var('srcdir')

        assert os.path.isabs(srcdir), srcdir
        assert os.path.isdir(srcdir), srcdir

        if sysconfig.python_build:
            # The python executable has not been installed so srcdir
            # should be a full source checkout.
            Python_h = os.path.join(srcdir, 'Include', 'Python.h')
            assert os.path.exists(Python_h), Python_h
            assert sysconfig._is_python_source_dir(srcdir)
        elif os.name == 'posix':
            assert os.path.dirname(sysconfig.get_makefile_filename()) == srcdir

    def test_srcdir_independent_of_cwd(self):
        # srcdir should be independent of the current working directory
        # See Issues #15322, #15364.
        srcdir = sysconfig.get_config_var('srcdir')
        cwd = os.getcwd()
        try:
            os.chdir('..')
            srcdir2 = sysconfig.get_config_var('srcdir')
        finally:
            os.chdir(cwd)
        assert srcdir == srcdir2

    def customize_compiler(self):
        # make sure AR gets caught
        class compiler:
            compiler_type = 'unix'
            executables = UnixCCompiler.executables

            def __init__(self):
                self.exes = {}

            def set_executables(self, **kw):
                for k, v in kw.items():
                    self.exes[k] = v

        sysconfig_vars = {
            'AR': 'sc_ar',
            'CC': 'sc_cc',
            'CXX': 'sc_cxx',
            'ARFLAGS': '--sc-arflags',
            'CFLAGS': '--sc-cflags',
            'CCSHARED': '--sc-ccshared',
            'LDSHARED': 'sc_ldshared',
            'SHLIB_SUFFIX': 'sc_shutil_suffix',
            # On macOS, disable _osx_support.customize_compiler()
            'CUSTOMIZED_OSX_COMPILER': 'True',
        }

        comp = compiler()
        with contextlib.ExitStack() as cm:
            for key, value in sysconfig_vars.items():
                cm.enter_context(swap_item(sysconfig._config_vars, key, value))
            sysconfig.customize_compiler(comp)

        return comp

    @unittest.skipUnless(
        get_default_compiler() == 'unix', 'not testing if default compiler is not unix'
    )
    def test_customize_compiler(self):
        # Make sure that sysconfig._config_vars is initialized
        sysconfig.get_config_vars()

        os.environ['AR'] = 'env_ar'
        os.environ['CC'] = 'env_cc'
        os.environ['CPP'] = 'env_cpp'
        os.environ['CXX'] = 'env_cxx --env-cxx-flags'
        os.environ['LDSHARED'] = 'env_ldshared'
        os.environ['LDFLAGS'] = '--env-ldflags'
        os.environ['ARFLAGS'] = '--env-arflags'
        os.environ['CFLAGS'] = '--env-cflags'
        os.environ['CPPFLAGS'] = '--env-cppflags'
        os.environ['RANLIB'] = 'env_ranlib'

        comp = self.customize_compiler()
        assert comp.exes['archiver'] == 'env_ar --env-arflags'
        assert comp.exes['preprocessor'] == 'env_cpp --env-cppflags'
        assert comp.exes['compiler'] == 'env_cc --sc-cflags --env-cflags --env-cppflags'
        assert comp.exes['compiler_so'] == (
            'env_cc --sc-cflags ' '--env-cflags ' '--env-cppflags --sc-ccshared'
        )
        assert comp.exes['compiler_cxx'] == 'env_cxx --env-cxx-flags'
        assert comp.exes['linker_exe'] == 'env_cc'
        assert comp.exes['linker_so'] == (
            'env_ldshared --env-ldflags --env-cflags' ' --env-cppflags'
        )
        assert comp.shared_lib_extension == 'sc_shutil_suffix'

        if sys.platform == "darwin":
            assert comp.exes['ranlib'] == 'env_ranlib'
        else:
            assert 'ranlib' not in comp.exes

        del os.environ['AR']
        del os.environ['CC']
        del os.environ['CPP']
        del os.environ['CXX']
        del os.environ['LDSHARED']
        del os.environ['LDFLAGS']
        del os.environ['ARFLAGS']
        del os.environ['CFLAGS']
        del os.environ['CPPFLAGS']
        del os.environ['RANLIB']

        comp = self.customize_compiler()
        assert comp.exes['archiver'] == 'sc_ar --sc-arflags'
        assert comp.exes['preprocessor'] == 'sc_cc -E'
        assert comp.exes['compiler'] == 'sc_cc --sc-cflags'
        assert comp.exes['compiler_so'] == 'sc_cc --sc-cflags --sc-ccshared'
        assert comp.exes['compiler_cxx'] == 'sc_cxx'
        assert comp.exes['linker_exe'] == 'sc_cc'
        assert comp.exes['linker_so'] == 'sc_ldshared'
        assert comp.shared_lib_extension == 'sc_shutil_suffix'
        assert 'ranlib' not in comp.exes

    def test_parse_makefile_base(self):
        self.makefile = TESTFN
        fd = open(self.makefile, 'w')
        try:
            fd.write(r"CONFIG_ARGS=  '--arg1=optarg1' 'ENV=LIB'" '\n')
            fd.write('VAR=$OTHER\nOTHER=foo')
        finally:
            fd.close()
        d = sysconfig.parse_makefile(self.makefile)
        assert d == {'CONFIG_ARGS': "'--arg1=optarg1' 'ENV=LIB'", 'OTHER': 'foo'}

    def test_parse_makefile_literal_dollar(self):
        self.makefile = TESTFN
        fd = open(self.makefile, 'w')
        try:
            fd.write(r"CONFIG_ARGS=  '--arg1=optarg1' 'ENV=\$$LIB'" '\n')
            fd.write('VAR=$OTHER\nOTHER=foo')
        finally:
            fd.close()
        d = sysconfig.parse_makefile(self.makefile)
        assert d == {'CONFIG_ARGS': r"'--arg1=optarg1' 'ENV=\$LIB'", 'OTHER': 'foo'}

    def test_sysconfig_module(self):
        import sysconfig as global_sysconfig

        assert global_sysconfig.get_config_var('CFLAGS') == sysconfig.get_config_var(
            'CFLAGS'
        )
        assert global_sysconfig.get_config_var('LDFLAGS') == sysconfig.get_config_var(
            'LDFLAGS'
        )

    @unittest.skipIf(
        sysconfig.get_config_var('CUSTOMIZED_OSX_COMPILER'), 'compiler flags customized'
    )
    def test_sysconfig_compiler_vars(self):
        # On OS X, binary installers support extension module building on
        # various levels of the operating system with differing Xcode
        # configurations.  This requires customization of some of the
        # compiler configuration directives to suit the environment on
        # the installed machine.  Some of these customizations may require
        # running external programs and, so, are deferred until needed by
        # the first extension module build.  With Python 3.3, only
        # the Distutils version of sysconfig is used for extension module
        # builds, which happens earlier in the Distutils tests.  This may
        # cause the following tests to fail since no tests have caused
        # the global version of sysconfig to call the customization yet.
        # The solution for now is to simply skip this test in this case.
        # The longer-term solution is to only have one version of sysconfig.

        import sysconfig as global_sysconfig

        if sysconfig.get_config_var('CUSTOMIZED_OSX_COMPILER'):
            self.skipTest('compiler flags customized')
        assert global_sysconfig.get_config_var('LDSHARED') == sysconfig.get_config_var(
            'LDSHARED'
        )
        assert global_sysconfig.get_config_var('CC') == sysconfig.get_config_var('CC')

    @unittest.skipIf(
        sysconfig.get_config_var('EXT_SUFFIX') is None,
        'EXT_SUFFIX required for this test',
    )
    def test_SO_deprecation(self):
        with pytest.warns(DeprecationWarning):
            sysconfig.get_config_var('SO')

    def test_customize_compiler_before_get_config_vars(self):
        # Issue #21923: test that a Distribution compiler
        # instance can be called without an explicit call to
        # get_config_vars().
        with open(TESTFN, 'w') as f:
            f.writelines(
                textwrap.dedent(
                    '''\
                from distutils.core import Distribution
                config = Distribution().get_command_obj('config')
                # try_compile may pass or it may fail if no compiler
                # is found but it should not raise an exception.
                rc = config.try_compile('int x;')
                '''
                )
            )
        p = subprocess.Popen(
            [str(sys.executable), TESTFN],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        outs, errs = p.communicate()
        assert 0 == p.returncode, "Subprocess failed: " + outs

    def test_parse_config_h(self):
        config_h = sysconfig.get_config_h_filename()
        input = {}
        with open(config_h, encoding="utf-8") as f:
            result = sysconfig.parse_config_h(f, g=input)
        assert input is result
        with open(config_h, encoding="utf-8") as f:
            result = sysconfig.parse_config_h(f)
        assert isinstance(result, dict)

    @unittest.skipUnless(sys.platform == 'win32', 'Testing windows pyd suffix')
    @unittest.skipUnless(
        sys.implementation.name == 'cpython', 'Need cpython for this test'
    )
    def test_win_ext_suffix(self):
        assert sysconfig.get_config_var("EXT_SUFFIX").endswith(".pyd")
        assert sysconfig.get_config_var("EXT_SUFFIX") != ".pyd"

    @unittest.skipUnless(sys.platform == 'win32', 'Testing Windows build layout')
    @unittest.skipUnless(
        sys.implementation.name == 'cpython', 'Need cpython for this test'
    )
    @unittest.skipUnless(
        '\\PCbuild\\'.casefold() in sys.executable.casefold(),
        'Need sys.executable to be in a source tree',
    )
    def test_win_build_venv_from_source_tree(self):
        """Ensure distutils.sysconfig detects venvs from source tree builds."""
        env = jaraco.envs.VEnv()
        env.create_opts = env.clean_opts
        env.root = TESTFN
        env.ensure_env()
        cmd = [
            env.exe(),
            "-c",
            "import distutils.sysconfig; print(distutils.sysconfig.python_build)",
        ]
        distutils_path = os.path.dirname(os.path.dirname(distutils.__file__))
        out = subprocess.check_output(
            cmd, env={**os.environ, "PYTHONPATH": distutils_path}
        )
        assert out == "True"
