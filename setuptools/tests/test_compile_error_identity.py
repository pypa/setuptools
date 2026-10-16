"""CompileError raised via setuptools._distutils must match setuptools.errors."""

from setuptools.errors import CompileError as public_error
from setuptools._distutils.ccompiler import new_compiler


def test_private_compiler_compile_error_matches_public():
    """Regression for pypa/setuptools#5294.

    Compilers obtained from ``setuptools._distutils.ccompiler.new_compiler``
    must raise the same ``CompileError`` class object that
    ``setuptools.errors.CompileError`` names, so ``except CompileError``
    handlers against the public name catch compile failures.
    """
    compiler_error = type(new_compiler())._compile.__globals__["CompileError"]
    assert compiler_error is public_error
    try:
        raise compiler_error("boom")
    except public_error:
        pass
    else:
        raise AssertionError("public CompileError did not catch private raise")
