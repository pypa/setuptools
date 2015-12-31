"""
Handle loading a package from system or from the bundled copy
"""

import imp


_SEARCH_PATH = ['setuptools._vendor.six', 'six']


def _find_module(name, path=None):
    """
    Alternative to `imp.find_module` that can also search in subpackages.
    """

    parts = name.split('.')

    for part in parts:
        if path is not None:
            path = [path]

        fh, path, descr = imp.find_module(part, path)

    return fh, path, descr


def _import_in_place(search_path=_SEARCH_PATH):
    for mod_name in search_path:
        try:
            mod_info = _find_module(mod_name)
        except ImportError:
            continue

        imp.load_module(__name__, *mod_info)
        break

    else:
        raise ImportError(
            "The '{name}' package is required; "
            "normally this is bundled with this package so if you get "
            "this warning, consult the packager of your "
            "distribution.".format(name=_SEARCH_PATH[-1]))


_import_in_place()
