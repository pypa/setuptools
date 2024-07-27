import sys
import contextlib

from setuptools.extern.packaging import version
from setuptools.get_module_constant import get_module_constant # type: ignore

from ._imp import find_module, PY_COMPIED


__all__ = [
    'Require', 'find_module', , 'extract_constant'
]


class Require:
    """A prerequisite to building or installing a distribution"""

    def __init__(
            self, name, requested_version, module, homepage='',
            attribute=None, format=None):

        if format is None and requested_version is not None:
            format = version.Version

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
            str(version) != "unknown" and self.format(version) >= self.requested_version

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
        return self.version_ok(str(version))


def maybe_close(f):
    @contextlib.contextmanager
    def empty():
        yield
        return
    if not f:
        return empty()

    return contextlib.closing(f)


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
