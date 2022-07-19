# Expose a subset of distutils as public API
# to help with migration to Python 3.12

from distutils.ccompiler import CCompiler
from distutils.ccompiler import new_compiler


def customize_compiler(compiler: CCompiler):
    """Do any platform-specific customization of a CCompiler instance.

    Mainly needed on Unix, so we can plug in the information that
    varies across Unices and is stored in Python's Makefile.
    """
    # Importing `distutils.sysconfig` directly may change the global state.
    # We adopt a lazy approach instead.
    from distutils.sysconfig import customize_compiler as _customize

    return _customize(compiler)
