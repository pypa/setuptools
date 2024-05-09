"""
Test suite for distutils.

Tests for the command classes in the distutils.command package are
included in distutils.tests as well, instead of using a separate
distutils.command.tests package, since command identification is done
by import rather than matching pre-defined names.
"""

from typing import Sequence


def missing_compiler_executable(cmd_names: Sequence[str] = []):  # pragma: no cover
    """Check if the compiler components used to build the interpreter exist.

    Check for the existence of the compiler executables whose names are listed
    in 'cmd_names' or all the compiler executables when 'cmd_names' is empty
    and return the first missing executable or None when none is found
    missing.

    """
    from distutils import ccompiler, errors, spawn, sysconfig

    compiler = ccompiler.new_compiler()
    sysconfig.customize_compiler(compiler)
    if compiler.compiler_type == "msvc":
        # MSVC has no executables, so check whether initialization succeeds
        try:
            compiler.initialize()
        except errors.DistutilsPlatformError:
            return "msvc"
    for name in compiler.executables:
        if cmd_names and name not in cmd_names:
            continue
        cmd = getattr(compiler, name)
        if cmd_names:
            assert cmd is not None, "the '%s' executable is not configured" % name
        elif not cmd:
            continue
        if spawn.find_executable(cmd[0]) is None:
            return cmd[0]
