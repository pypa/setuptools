import sys

here = os.path.dirname(__file__)
NEW_DISTUTILS_LOCATION = os.path.join(here, 'distutils-shim-package')

sys.path.insert(0, NEW_DISTUTILS_LOCATION)
