import os
import sys
import platform

import pytest

from distutils import ccompiler


def _make_strs(paths):
    """
    Convert paths to strings for legacy compatibility.
    """
    if sys.version_info > (3, 8) and platform.system() != "Windows":
        return paths
    return list(map(os.fspath, paths))


@pytest.fixture
def c_file(tmp_path):
    c_file = tmp_path / 'foo.c'
    c_file.write_text('void PyInit_foo(void) {}\n')
    return c_file


def test_set_include_dirs(c_file):
    """
    Extensions should build even if set_include_dirs is invoked.
    In particular, compiler-specific paths should not be overridden.
    """
    compiler = ccompiler.new_compiler()
    compiler.set_include_dirs([])
    compiler.compile(_make_strs([c_file]))


def test_set_library_dirs(c_file):
    """
    Extensions should build even if set_library_dirs is invoked.
    In particular, compiler-specific paths should not be overridden.
    """
    compiler = ccompiler.new_compiler()
    compiler.set_library_dirs([])
    compiler.compile(_make_strs([c_file]))
