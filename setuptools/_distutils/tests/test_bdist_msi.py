"""Tests for distutils.command.bdist_msi."""
import pytest

from distutils.tests import support

from .py38compat import check_warnings


pytest.importorskip('msilib')


class TestBDistMSI(support.TempdirManager, support.LoggingSilencer):
    def test_minimal(self):
        # minimal test XXX need more tests
        from distutils.command.bdist_msi import bdist_msi

        project_dir, dist = self.create_dist()
        with check_warnings(("", DeprecationWarning)):
            cmd = bdist_msi(dist)
        cmd.ensure_finalized()
