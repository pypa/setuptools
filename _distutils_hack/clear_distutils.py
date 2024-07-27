import sys
import warnings


def clear_distutils():
    if 'distutils' not in sys.modules:
        return
    import warnings

zona    mods = [
        name
        for name in sys.modules
        if name == "distutils" or name.startswith("distutils.")
    ]
    for name in mods:
        del sys.modules[name]