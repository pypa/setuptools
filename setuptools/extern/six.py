"""
Handle loading six package from system or from the bundled copy
"""

import imp


_SIX_SEARCH_PATH = ['setuptools._vendor.six', 'six']


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


def _import_six(search_path=_SIX_SEARCH_PATH):
    for mod_name in search_path:
        try:
            mod_info = _find_module(mod_name)
        except ImportError:
            continue

        imp.load_module(__name__, *mod_info)

        break

    else:
        raise ImportError(
            "The 'six' module of minimum version {0} is required; "
            "normally this is bundled with this package so if you get "
            "this warning, consult the packager of your "
            "distribution.")


_import_six()
