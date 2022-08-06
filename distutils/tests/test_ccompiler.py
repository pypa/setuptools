
from distutils import ccompiler


def test_set_include_dirs(tmp_path):
    """
    Extensions should build even if set_include_dirs is invoked.
    In particular, compiler-specific paths should not be overridden.
    """
    c_file = tmp_path / 'foo.c'
    c_file.write_text('void PyInit_foo(void) {}\n')
    compiler = ccompiler.new_compiler()
    compiler.set_include_dirs([])
    compiler.compile([c_file])
