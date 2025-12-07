import sys

# Python 3.13 should support `.pth` files encoded in UTF-8
# See discussion in https://github.com/python/cpython/issues/77102
PTH_ENCODING = "utf-8" if sys.version_info >= (3, 12, 4) else "locale"
