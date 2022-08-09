import os
import sys
import platform
import textwrap
import sysconfig

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
    gen_headers = ('Python.h',)
    is_windows = platform.system() == "Windows"
    plat_headers = ('windows.h',) * is_windows
    all_headers = gen_headers + plat_headers
    headers = '\n'.join(f'#include <{header}>\n' for header in all_headers)
    payload = (
        textwrap.dedent(
            """
        #headers
        void PyInit_foo(void) {}
        """
        )
        .lstrip()
        .replace('#headers', headers)
    )
    c_file.write_text(payload)
    return c_file


def test_set_include_dirs(c_file):
    """
    Extensions should build even if set_include_dirs is invoked.
    In particular, compiler-specific paths should not be overridden.
    """
    compiler = ccompiler.new_compiler()
    python = sysconfig.get_paths()['include']
    compiler.set_include_dirs([python])
    compiler.compile(_make_strs([c_file]))

    # do it again, setting include dirs after any initialization
    compiler.set_include_dirs([python])
    compiler.compile(_make_strs([c_file]))
