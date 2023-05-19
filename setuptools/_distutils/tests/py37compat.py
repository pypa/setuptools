import os
import sys
import platform


def subprocess_args_compat(*args):
    return list(map(os.fspath, args))


def subprocess_args_passthrough(*args):
    return list(args)


subprocess_args = (
    subprocess_args_compat
    if platform.system() == "Windows" and sys.version_info < (3, 8)
    else subprocess_args_passthrough
)
