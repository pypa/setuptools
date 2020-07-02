"""
Backward compatibility support for Python 3.5
"""

import sys
import test.support
import subprocess


# copied from Python 3.9 test.support module
def _missing_compiler_executable(cmd_names=[]):
    """Check if the compiler components used to build the interpreter exist.

    Check for the existence of the compiler executables whose names are listed
    in 'cmd_names' or all the compiler executables when 'cmd_names' is empty
    and return the first missing executable or None when none is found
    missing.

    """
    from distutils import ccompiler, sysconfig, spawn
    compiler = ccompiler.new_compiler()
    sysconfig.customize_compiler(compiler)
    for name in compiler.executables:
        if cmd_names and name not in cmd_names:
            continue
        cmd = getattr(compiler, name)
        if cmd_names:
            assert cmd is not None, \
                    "the '%s' executable is not configured" % name
        elif not cmd:
            continue
        if spawn.find_executable(cmd[0]) is None:
            return cmd[0]


missing_compiler_executable = vars(test.support).setdefault(
    'missing_compiler_executable',
    _missing_compiler_executable,
)


try:
    from test.support import unix_shell
except ImportError:
    # Adapted from Python 3.9 test.support module
    is_android = hasattr(sys, 'getandroidapilevel')
    unix_shell = (
        None if sys.platform == 'win32' else
        '/system/bin/sh' if is_android else
        '/bin/sh'
    )


# copied from Python 3.9 subprocess module
def _optim_args_from_interpreter_flags():
    """Return a list of command-line arguments reproducing the current
    optimization settings in sys.flags."""
    args = []
    value = sys.flags.optimize
    if value > 0:
        args.append('-' + 'O' * value)
    return args


vars(subprocess).setdefault(
    '_optim_args_from_interpreter_flags',
    _optim_args_from_interpreter_flags,
)


def adapt_glob(regex):
    """
    Supply legacy expectation on Python 3.5
    """
    if sys.version_info > (3, 6):
        return regex
    return regex.replace('(?s:', '').replace(r')\Z', r'\Z(?ms)')
