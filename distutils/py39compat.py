import sys
import platform


def ext_suffix(vars):
    """
    Ensure vars contains 'EXT_SUFFIX'. pypa/distutils#130
    """
    if sys.version_info < (3, 10):
        return
    if platform.system() != 'Windows':
        return
    import _imp
    ext_suffix = _imp.extension_suffixes()[0]
    vars.update(
        EXT_SUFFIX=ext_suffix,
        # sysconfig sets SO to match EXT_SUFFIX, so maintain
        # that expectation.
        # https://github.com/python/cpython/blob/785cc6770588de087d09e89a69110af2542be208/Lib/sysconfig.py#L671-L673
        SO=ext_suffix,
    )
