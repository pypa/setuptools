"""Tests for distutils.command.bdist_wininst."""
import sys
import platform
import unittest

from .py38compat import check_warnings

from distutils.command.bdist_wininst import bdist_wininst
from distutils.tests import support


@unittest.skipIf(
    sys.platform == 'win32' and platform.machine() == 'ARM64',
    'bdist_wininst is not supported in this install',
)
@unittest.skipIf(
    getattr(bdist_wininst, '_unsupported', False),
    'bdist_wininst is not supported in this install',
)
class TestBuildWinInst(support.TempdirManager, support.LoggingSilencer):
    def test_get_exe_bytes(self):

        # issue5731: command was broken on non-windows platforms
        # this test makes sure it works now for every platform
        # let's create a command
        pkg_pth, dist = self.create_dist()
        with check_warnings(("", DeprecationWarning)):
            cmd = bdist_wininst(dist)
        cmd.ensure_finalized()

        # let's run the code that finds the right wininst*.exe file
        # and make sure it finds it and returns its content
        # no matter what platform we have
        exe_file = cmd.get_exe_bytes()
        assert len(exe_file) > 10
