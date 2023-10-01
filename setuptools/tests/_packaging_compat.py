from packaging import __version__ as packaging_version

if tuple(packaging_version.split(".")) >= ("23", "2"):
    from packaging.metadata import Metadata  # type: ignore[attr-defined]
else:
    # Just pretend it exists while waiting for release...
    from unittest.mock import MagicMock

    Metadata = MagicMock()
