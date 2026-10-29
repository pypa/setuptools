from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 15):
    from builtins import sentinel
elif TYPE_CHECKING:
    from typing_extensions import sentinel
else:

    def sentinel(_x, **_y) -> sentinel:
        """Return a unique object. Must be called with an identifier."""
        return object()
