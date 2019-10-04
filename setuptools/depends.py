import sys
import marshal
from distutils.version import StrictVersion
from setuptools.extern import six

from .py33compat import Bytecode

if six.PY2:
    import imp
    from imp import PKG_DIRECTORY, PY_COMPILED, PY_SOURCE, PY_FROZEN
else:
    import os.path
    from importlib.util import find_spec, spec_from_loader
    from importlib.machinery import SOURCE_SUFFIXES, BYTECODE_SUFFIXES, EXTENSION_SUFFIXES, BuiltinImporter, FrozenImporter
    PY_SOURCE = 1
    PY_COMPILED = 2
    C_EXTENSION = 3
    C_BUILTIN = 6
    PY_FROZEN = 7


__all__ = [
    'Require', 'find_module', 'get_module_constant', 'extract_constant'
]


class Require:
    """A prerequisite to building or installing a distribution"""

    def __init__(self, name, requested_version, module, homepage='',
            attribute=None, format=None):

        if format is None and requested_version is not None:
            format = StrictVersion

        if format is not None:
            requested_version = format(requested_version)
            if attribute is None:
                attribute = '__version__'

        self.__dict__.update(locals())
        del self.self

    def full_name(self):
        """Return full package/distribution name, w/version"""
        if self.requested_version is not None:
            return '%s-%s' % (self.name, self.requested_version)
        return self.name

    def version_ok(self, version):
        """Is 'version' sufficiently up-to-date?"""
        return self.attribute is None or self.format is None or \
            str(version) != "unknown" and version >= self.requested_version

    def get_version(self, paths=None, default="unknown"):
        """Get version number of installed module, 'None', or 'default'

        Search 'paths' for module.  If not found, return 'None'.  If found,
        return the extracted version attribute, or 'default' if no version
        attribute was specified, or the value cannot be determined without
        importing the module.  The version is formatted according to the
        requirement's version format (if any), unless it is 'None' or the
        supplied 'default'.
        """

        if self.attribute is None:
            try:
                f, p, i = find_module(self.module, paths)
                if f:
                    f.close()
                return default
            except ImportError:
                return None

        v = get_module_constant(self.module, self.attribute, default, paths)

        if v is not None and v is not default and self.format is not None:
            return self.format(v)

        return v

    def is_present(self, paths=None):
        """Return true if dependency is present on 'paths'"""
        return self.get_version(paths) is not None

    def is_current(self, paths=None):
        """Return true if dependency is present and up-to-date on 'paths'"""
        version = self.get_version(paths)
        if version is None:
            return False
        return self.version_ok(version)


def find_module(module, paths=None):
    """Just like 'imp.find_module()', but with package support"""
    if six.PY3:
        spec = find_spec(module, paths)
        if spec is None:
            raise ImportError("Can't find %s" % module)
        if not spec.has_location and hasattr(spec, 'submodule_search_locations'):
            spec = spec_from_loader('__init__.py', spec.loader)

        kind = -1
        file = None
        static = isinstance(spec.loader, type)
        if spec.origin == 'frozen' or static and issubclass(spec.loader, FrozenImporter):
            kind = PY_FROZEN
            path = None # imp compabilty
            suffix = mode = '' # imp compability
        elif spec.origin == 'built-in' or static and issubclass(spec.loader, BuiltinImporter):
            kind = C_BUILTIN
            path = None # imp compabilty
            suffix = mode = '' # imp compability
        elif spec.has_location:
            frozen = False
            path = spec.origin
            suffix = os.path.splitext(path)[1]
            mode = 'r' if suffix in SOURCE_SUFFIXES else 'rb'

            if suffix in SOURCE_SUFFIXES:
                kind = PY_SOURCE
            elif suffix in BYTECODE_SUFFIXES:
                kind = PY_COMPILED
            elif suffix in EXTENSION_SUFFIXES:
                kind = C_EXTENSION

            if kind in {PY_SOURCE, PY_COMPILED}:
                file = open(path, mode)
        else:
            path = None
            suffix = mode= ''

        return file, path, (suffix, mode, kind)

    else:
        parts = module.split('.')
        while parts:
            part = parts.pop(0)
            f, path, (suffix, mode, kind) = info = imp.find_module(part, paths)

            if kind == PKG_DIRECTORY:
                parts = parts or ['__init__']
                paths = [path]

            elif parts:
                raise ImportError("Can't find %r in %s" % (parts, module))

        return info


def get_module_constant(module, symbol, default=-1, paths=None):
    """Find 'module' by searching 'paths', and extract 'symbol'

    Return 'None' if 'module' does not exist on 'paths', or it does not define
    'symbol'.  If the module defines 'symbol' as a constant, return the
    constant.  Otherwise, return 'default'."""

    try:
        f, path, (suffix, mode, kind) = find_module(module, paths)
    except ImportError:
        # Module doesn't exist
        return None

    if six.PY3:
        spec = find_spec(module, paths)
        if hasattr(spec, 'submodule_search_locations'):
            spec = spec_from_loader('__init__.py', spec.loader)

    try:
        if kind == PY_COMPILED:
            f.read(8)  # skip magic & date
            code = marshal.load(f)
        elif kind == PY_FROZEN:
            if six.PY2:
                code = imp.get_frozen_object(module)
            else:
                code = spec.loader.get_code(module)
        elif kind == PY_SOURCE:
            code = compile(f.read(), path, 'exec')
        else:
            # Not something we can parse; we'll have to import it.  :(
            if module not in sys.modules:
                if six.PY2:
                    imp.load_module(module, f, path, (suffix, mode, kind))
                else:
                    sys.modules[module] = module_from_spec(spec)
            return getattr(sys.modules[module], symbol, None)

    finally:
        if f:
            f.close()

    return extract_constant(code, symbol, default)


def extract_constant(code, symbol, default=-1):
    """Extract the constant value of 'symbol' from 'code'

    If the name 'symbol' is bound to a constant value by the Python code
    object 'code', return that value.  If 'symbol' is bound to an expression,
    return 'default'.  Otherwise, return 'None'.

    Return value is based on the first assignment to 'symbol'.  'symbol' must
    be a global, or at least a non-"fast" local in the code block.  That is,
    only 'STORE_NAME' and 'STORE_GLOBAL' opcodes are checked, and 'symbol'
    must be present in 'code.co_names'.
    """
    if symbol not in code.co_names:
        # name's not there, can't possibly be an assignment
        return None

    name_idx = list(code.co_names).index(symbol)

    STORE_NAME = 90
    STORE_GLOBAL = 97
    LOAD_CONST = 100

    const = default

    for byte_code in Bytecode(code):
        op = byte_code.opcode
        arg = byte_code.arg

        if op == LOAD_CONST:
            const = code.co_consts[arg]
        elif arg == name_idx and (op == STORE_NAME or op == STORE_GLOBAL):
            return const
        else:
            const = default


def _update_globals():
    """
    Patch the globals to remove the objects not available on some platforms.

    XXX it'd be better to test assertions about bytecode instead.
    """

    if not sys.platform.startswith('java') and sys.platform != 'cli':
        return
    incompatible = 'extract_constant', 'get_module_constant'
    for name in incompatible:
        del globals()[name]
        __all__.remove(name)


_update_globals()
