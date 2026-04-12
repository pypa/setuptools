"""Tests to verify pkg_resources is importable and emits a deprecation warning."""

import warnings

import pytest


class TestPkgResourcesImport:
    def test_import_succeeds(self):
        """pkg_resources should be importable."""
        import pkg_resources  # noqa: F401

    def test_deprecation_warning(self):
        """Importing pkg_resources should emit a DeprecationWarning."""
        # Force re-import by removing from sys.modules
        import sys

        sys.modules.pop("pkg_resources", None)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import importlib

            import pkg_resources

            importlib.reload(pkg_resources)
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert any(
                "pkg_resources is deprecated" in str(x.message)
                for x in deprecation_warnings
            ), f"Expected deprecation warning, got: {deprecation_warnings}"
