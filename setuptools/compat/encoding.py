import sys
from typing import Optional


locale_encoding = "locale" if sys.version_info >= (3, 10) else None
"""
Use this variable to explicitly set encoding to avoid `EncodingWarning` in tests logs: ``encoding=locale_encoding``.

Python <= 3.10, `None` and ``locale.getpreferredencoding(False)`` are equivalent.
Python >= 3.11, using ``getpreferredencoding`` in  leads to ``EncodingWarning: UTF-8 Mode affects \
locale.getpreferredencoding(). Consider locale.getencoding() instead.``.
So let's avoid using `locale.getpreferredencoding` at all for simplicity.

Note that, until Python 3.11 `TextIOWrapper` still used UTF-8 even with ``encoding='locale'``
Ref.: https://peps.python.org/pep-0686/#fixing-encoding-locale-option

---

When working with ``.pth`` files, let's ignore UTF-8 mode (``PYTHONUTF8`` or ``python -X utf8``)
Ref.: https://peps.python.org/pep-0686/#locale-getencoding

``.pth`` files break with UTF-8 encoding.
https://github.com/python/cpython/issues/77102#issuecomment-1568457039
"""


def locale_encoding_for_mode(mode: str) -> Optional[str]:
    """
    Files open in binary mode should not be passed an encoding.
    """
    return None if "b" in mode else locale_encoding
