"""msvc9compiler monkey patch test

This test ensures that importing setuptools is sufficient to replace
the standard find_vcvarsall function with our patched version that
finds the Visual C++ for Python package.
"""

import os
import shutil
import tempfile
import distutils.errors

import pytest
import mock

from . import contexts

# importing only setuptools should apply the patch
__import__('setuptools')

pytest.importorskip("distutils.msvc9compiler")


def mock_reg(hkcu=None, hklm=None):
    """
    Return a mock for distutils.msvc9compiler.Reg, patched
    to mock out the functions that access the registry.
    """

    _winreg = getattr(distutils.msvc9compiler, '_winreg', None)
    winreg = getattr(distutils.msvc9compiler, 'winreg', _winreg)

    hives = {
        winreg.HKEY_CURRENT_USER: hkcu or {},
        winreg.HKEY_LOCAL_MACHINE: hklm or {},
    }

    @classmethod
    def read_keys(cls, base, key):
        """Return list of registry keys."""
        hive = hives.get(base, {})
        return [
            k.rpartition('\\')[2]
            for k in hive if k.startswith(key.lower())
        ]

    @classmethod
    def read_values(cls, base, key):
        """Return dict of registry keys and values."""
        hive = hives.get(base, {})
        return dict(
            (k.rpartition('\\')[2], hive[k])
            for k in hive if k.startswith(key.lower())
        )

    return mock.patch.multiple(distutils.msvc9compiler.Reg,
        read_keys=read_keys, read_values=read_values)


class TestMSVC9Compiler:

    def test_find_vcvarsall_patch(self):
        mod_name = distutils.msvc9compiler.find_vcvarsall.__module__
        assert mod_name == "setuptools.msvc9_support", "find_vcvarsall unpatched"

        find_vcvarsall = distutils.msvc9compiler.find_vcvarsall
        query_vcvarsall = distutils.msvc9compiler.query_vcvarsall

        # No registry entries or environment variable means we should
        # not find anything
        with contexts.environment(VS90COMNTOOLS=None):
            with mock_reg():
                assert find_vcvarsall(9.0) is None

                expected = distutils.errors.DistutilsPlatformError
                with pytest.raises(expected) as exc:
                    query_vcvarsall(9.0)
                assert 'aka.ms/vcpython27' in str(exc)

        key_32 = r'software\microsoft\devdiv\vcforpython\9.0\installdir'
        key_64 = r'software\wow6432node\microsoft\devdiv\vcforpython\9.0\installdir'

        # Make two mock files so we can tell whether HCKU entries are
        # preferred to HKLM entries.
        mock_installdir_1 = tempfile.mkdtemp()
        mock_vcvarsall_bat_1 = os.path.join(mock_installdir_1, 'vcvarsall.bat')
        open(mock_vcvarsall_bat_1, 'w').close()
        mock_installdir_2 = tempfile.mkdtemp()
        mock_vcvarsall_bat_2 = os.path.join(mock_installdir_2, 'vcvarsall.bat')
        open(mock_vcvarsall_bat_2, 'w').close()
        try:
            # Ensure we get the current user's setting first
            reg = mock_reg(
                hkcu={
                    key_32: mock_installdir_1,
                },
                hklm={
                    key_32: mock_installdir_2,
                    key_64: mock_installdir_2,
                },
            )
            with reg:
                assert mock_vcvarsall_bat_1 == find_vcvarsall(9.0)

            # Ensure we get the local machine value if it's there
            with mock_reg(hklm={key_32: mock_installdir_2}):
                assert mock_vcvarsall_bat_2 == find_vcvarsall(9.0)

            # Ensure we prefer the 64-bit local machine key
            # (*not* the Wow6432Node key)
            reg = mock_reg(
                hklm={
                    # This *should* only exist on 32-bit machines
                    key_32: mock_installdir_1,
                    # This *should* only exist on 64-bit machines
                    key_64: mock_installdir_2,
                }
            )
            with reg:
                assert mock_vcvarsall_bat_1 == find_vcvarsall(9.0)
        finally:
            shutil.rmtree(mock_installdir_1)
            shutil.rmtree(mock_installdir_2)
