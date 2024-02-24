import locale
import sys


encoding_for_open = (
    "locale" if sys.version_info >= (3, 10) else locale.getpreferredencoding(False)
)
"""
This variable exists to centralize calls to `getpreferredencoding`
to reduce the amount of `EncodingWarning` in tests logs.
"""

encoding_for_pth = locale.getencoding() if sys.version_info >= (3, 11) else None
"""
When working with ``.pth`` files, let's ignore UTF-8 mode (``PYTHONUTF8`` or ``python -X utf8``)
Ref.: https://peps.python.org/pep-0686/#locale-getencoding

``.pth`` files break with UTF-8 encoding.
https://github.com/python/cpython/issues/77102#issuecomment-1568457039

Until Python 3.11 `TextIOWrapper` still used UTF-8 even with ``encoding='locale'``
Ref.: https://peps.python.org/pep-0686/#fixing-encoding-locale-option
"""
