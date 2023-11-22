from typing import TYPE_CHECKING

from packaging import __version__ as packaging_version

if TYPE_CHECKING or tuple(packaging_version.split(".")) >= ("23", "2"):
    from packaging.metadata import Metadata
else:
    # Just pretend it exists while waiting for release...
    from unittest.mock import MagicMock

    Metadata = MagicMock()
