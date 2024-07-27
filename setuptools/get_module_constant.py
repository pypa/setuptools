from _distutils_hack import extract_constant
from setuptools import _imp
from setuptools._imp import PY_FROZEN, PY_SOURCE, find_module
from setuptools.depends import maybe_close


import marshal


def get_module_constant(module, symbol, default=-1, paths=None):
    """Find 'module' by searching 'paths', and extract 'symbol'

    Return 'None' if 'module' does not exist on 'paths', or it does not define
    'symbol'.  If the module defines 'symbol' as a constant, return the
    constant.  Otherwise, return 'default'."""

    try:
        f, path, (suffix, mode, kind) = info = find_module(module, paths)
    except ImportError:
        # Module doesn't exist
        return None

    with maybe_close(f):
        if kind == PY_COMPILED:
            f.read(8)  # skip magic & date
            code = marshal.load(f)
        elif kind == PY_FROZEN:
            code = _imp.get_frozen_object(module, paths)
        elif kind == PY_SOURCE:
            code = compile(f.read(), path, 'exec')
        else:
            # Not something we can parse; we'll have to import it.  :(
            imported = _imp.get_module(module, paths, info)
            return getattr(imported, symbol, None)

    return extract_constant(code, symbol, default)