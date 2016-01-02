import sys

_VENDORED_NAMES = 'six',
_SEARCH_PATH = 'setuptools._vendor.', ''

class VendorImporter:
    """
    A PEP 302 meta path importer for finding optionally-vendored
    or otherwise naturally-installed packages from __name__.
    """
    def find_module(self, fullname, path=None):
        root, base, target = fullname.partition(__name__ + '.')
        if root:
            return
        if not any(map(target.startswith, _VENDORED_NAMES)):
            return
        return self

    def load_module(self, fullname):
        root, base, target = fullname.partition(__name__ + '.')
        for prefix in _SEARCH_PATH:
            try:
                __import__(prefix + target)
                mod = sys.modules[prefix + target]
                sys.modules[fullname] = mod
                return mod
            except ImportError:
                pass
        else:
            raise ImportError(
                "The '{target}' package is required; "
                "normally this is bundled with this package so if you get "
                "this warning, consult the packager of your "
                "distribution.".format(**locals())
            )

    @classmethod
    def install(cls):
        if not any(isinstance(imp, cls) for imp in sys.meta_path):
            sys.meta_path.append(cls())

VendorImporter.install()
