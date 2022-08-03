"""Tests for distutils._msvccompiler."""
import sys
import unittest
import os
import threading

import pytest

from distutils.errors import DistutilsPlatformError
from distutils.tests import support
from distutils import _msvccompiler


needs_winreg = pytest.mark.skipif('not hasattr(_msvccompiler, "winreg")')


class Testmsvccompiler(support.TempdirManager):
    def test_no_compiler(self):
        # makes sure query_vcvarsall raises
        # a DistutilsPlatformError if the compiler
        # is not found
        def _find_vcvarsall(plat_spec):
            return None, None

        old_find_vcvarsall = _msvccompiler._find_vcvarsall
        _msvccompiler._find_vcvarsall = _find_vcvarsall
        try:
            with pytest.raises(DistutilsPlatformError):
                _msvccompiler._get_vc_env(
                    'wont find this version',
                )
        finally:
            _msvccompiler._find_vcvarsall = old_find_vcvarsall

    @needs_winreg
    def test_get_vc_env_unicode(self):
        test_var = 'ṰḖṤṪ┅ṼẨṜ'
        test_value = '₃⁴₅'

        # Ensure we don't early exit from _get_vc_env
        old_distutils_use_sdk = os.environ.pop('DISTUTILS_USE_SDK', None)
        os.environ[test_var] = test_value
        try:
            env = _msvccompiler._get_vc_env('x86')
            assert test_var.lower() in env
            assert test_value == env[test_var.lower()]
        finally:
            os.environ.pop(test_var)
            if old_distutils_use_sdk:
                os.environ['DISTUTILS_USE_SDK'] = old_distutils_use_sdk

    @needs_winreg
    def test_get_vc2017(self):
        # This function cannot be mocked, so pass it if we find VS 2017
        # and mark it skipped if we do not.
        version, path = _msvccompiler._find_vc2017()
        if version:
            assert version >= 15
            assert os.path.isdir(path)
        else:
            raise unittest.SkipTest("VS 2017 is not installed")

    @needs_winreg
    def test_get_vc2015(self):
        # This function cannot be mocked, so pass it if we find VS 2015
        # and mark it skipped if we do not.
        version, path = _msvccompiler._find_vc2015()
        if version:
            assert version >= 14
            assert os.path.isdir(path)
        else:
            raise unittest.SkipTest("VS 2015 is not installed")


class CheckThread(threading.Thread):
    exc_info = None

    def run(self):
        try:
            super().run()
        except Exception:
            self.exc_info = sys.exc_info()

    def __bool__(self):
        return not self.exc_info


class TestSpawn:
    def test_concurrent_safe(self):
        """
        Concurrent calls to spawn should have consistent results.
        """
        compiler = _msvccompiler.MSVCCompiler()
        compiler._paths = "expected"
        inner_cmd = 'import os; assert os.environ["PATH"] == "expected"'
        command = [sys.executable, '-c', inner_cmd]

        threads = [
            CheckThread(target=compiler.spawn, args=[command]) for n in range(100)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert all(threads)

    def test_concurrent_safe_fallback(self):
        """
        If CCompiler.spawn has been monkey-patched without support
        for an env, it should still execute.
        """
        from distutils import ccompiler

        compiler = _msvccompiler.MSVCCompiler()
        compiler._paths = "expected"

        def CCompiler_spawn(self, cmd):
            "A spawn without an env argument."
            assert os.environ["PATH"] == "expected"

        with unittest.mock.patch.object(ccompiler.CCompiler, 'spawn', CCompiler_spawn):
            compiler.spawn(["n/a"])

        assert os.environ.get("PATH") != "expected"
