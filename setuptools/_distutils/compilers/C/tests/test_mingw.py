from distutils import sysconfig
from distutils.errors import DistutilsPlatformError
from distutils.util import is_mingw, split_quoted

import pytest

from .. import cygwin, errors


class TestMinGW32Compiler:
    @pytest.mark.skipif(not is_mingw(), reason='not on mingw')
    def test_compiler_type(self):
        compiler = cygwin.MinGW32Compiler()
        assert compiler.compiler_type == 'mingw32'

    @pytest.mark.skipif(not is_mingw(), reason='not on mingw')
    def test_set_executables(self, monkeypatch):
        monkeypatch.setenv('CC', 'cc')
        monkeypatch.setenv('CXX', 'c++')

        compiler = cygwin.MinGW32Compiler()

        assert compiler.compiler == split_quoted('cc -O1 -Wall')
        assert compiler.compiler_so == split_quoted('cc -shared -O1 -Wall')
        assert compiler.compiler_cxx == split_quoted('c++ -O1 -Wall')
        assert compiler.linker_exe == split_quoted('cc')
        assert compiler.linker_so == split_quoted('cc -shared')

    @pytest.mark.skipif(not is_mingw(), reason='not on mingw')
    def test_runtime_library_dir_option(self):
        compiler = cygwin.MinGW32Compiler()
        with pytest.raises(DistutilsPlatformError):
            compiler.runtime_library_dir_option('/usr/lib')

    @pytest.mark.skipif(not is_mingw(), reason='not on mingw')
    def test_cygwincc_error(self, monkeypatch):
        monkeypatch.setattr(cygwin, 'is_cygwincc', lambda _: True)

        with pytest.raises(errors.Error):
            cygwin.MinGW32Compiler()

    @pytest.mark.skipif('sys.platform == "cygwin"')
    def test_customize_compiler_with_msvc_python(self):
        # In case we have an MSVC Python build, but still want to use
        # MinGW32Compiler, then customize_compiler() shouldn't fail at least.
        # https://github.com/pypa/setuptools/issues/4456
        compiler = cygwin.MinGW32Compiler()
        sysconfig.customize_compiler(compiler)


    def test_default_optimize_flag_is_o1(self, monkeypatch):
        """Bare -O is rejected by cc1 under -m32; defaults must use -O1 (#4873)."""
        monkeypatch.setattr(cygwin, 'is_cygwincc', lambda _: False)
        monkeypatch.setenv('CC', 'gcc')
        monkeypatch.setenv('CXX', 'g++')
        compiler = cygwin.MinGW32Compiler()
        joined = ' '.join(compiler.compiler + compiler.compiler_so + compiler.compiler_cxx)
        assert ' -O ' not in f' {joined} '
        assert '-O1' in compiler.compiler
