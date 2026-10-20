from __future__ import annotations

import sys
from collections.abc import Iterator


def implied_symbols(name: str) -> Iterator[str]:
    """
    Yield the symbols a shared extension for the module ``name`` must
    export implicitly (that is, in addition to 'ext.export_symbols').

    On Python 3.14 and below (that is, before a new export hook name was
    added), the module import hook "PyInit_" + name must be exported.
    Only relevant on Windows, where the .pyd file (DLL) must export that
    function.

    Since Python 3.15, nothing is implied; an export directive was added
    to the "PyMODINIT_FUNC" implementation, which is all that is needed.
    """
    if sys.version_info >= (3, 15):
        return

    try:
        # Unicode module name support as defined in PEP-489
        # https://peps.python.org/pep-0489/#export-hook-name
        name.encode('ascii')
    except UnicodeEncodeError:
        suffix = 'U_' + name.encode('punycode').replace(b'-', b'_').decode('ascii')
    else:
        suffix = "_" + name

    yield "PyInit" + suffix
