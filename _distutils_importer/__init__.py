import sys

_HERE = os.path.dirname(__file__)
NEW_DISTUTILS_LOCATION = os.path.join(_HERE, 'distutils-shim-package')

def add_shim():
    if NEW_DISTUTILS_LOCATION not in sys.path:
        sys.path.insert(0, NEW_DISTUTILS_LOCATION)

def remove_shim():
    try:
        sys.path.remove(NEW_DISTUTILS_LOCATION)
    except ValueError:
        pass


add_shim()
