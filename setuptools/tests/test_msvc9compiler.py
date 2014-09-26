"""msvc9compiler monkey patch test

This test ensures that importing setuptools is sufficient to replace
the standard find_vcvarsall function with our patched version that
finds the Visual C++ for Python package.
"""

import os
import shutil
import sys
import tempfile
import unittest
import distutils.errors
import contextlib

# importing only setuptools should apply the patch
__import__('setuptools')

class MockReg:
    """Mock for distutils.msvc9compiler.Reg. We patch it
    with an instance of this class that mocks out the
    functions that access the registry.
    """

    def __init__(self, hkey_local_machine={}, hkey_current_user={}):
        self.hklm = hkey_local_machine
        self.hkcu = hkey_current_user

    def __enter__(self):
        self.original_read_keys = distutils.msvc9compiler.Reg.read_keys
        self.original_read_values = distutils.msvc9compiler.Reg.read_values

        _winreg = getattr(distutils.msvc9compiler, '_winreg', None)
        winreg = getattr(distutils.msvc9compiler, 'winreg', _winreg)

        hives = {
            winreg.HKEY_CURRENT_USER: self.hkcu,
            winreg.HKEY_LOCAL_MACHINE: self.hklm,
        }

        def read_keys(cls, base, key):
            """Return list of registry keys."""
            hive = hives.get(base, {})
            return [k.rpartition('\\')[2]
                    for k in hive if k.startswith(key.lower())]

        def read_values(cls, base, key):
            """Return dict of registry keys and values."""
            hive = hives.get(base, {})
            return dict((k.rpartition('\\')[2], hive[k])
                        for k in hive if k.startswith(key.lower()))

        distutils.msvc9compiler.Reg.read_keys = classmethod(read_keys)
        distutils.msvc9compiler.Reg.read_values = classmethod(read_values)

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        distutils.msvc9compiler.Reg.read_keys = self.original_read_keys
        distutils.msvc9compiler.Reg.read_values = self.original_read_values

@contextlib.contextmanager
def patch_env(**replacements):
    """
    In a context, patch the environment with replacements. Pass None values
    to clear the values.
    """
    saved = dict(
        (key, os.environ['key'])
        for key in replacements
        if key in os.environ
    )

    # remove values that are null
    remove = (key for (key, value) in replacements.items() if value is None)
    for key in list(remove):
        os.environ.pop(key, None)
        replacements.pop(key)

    os.environ.update(replacements)

    try:
        yield saved
    finally:
        for key in replacements:
            os.environ.pop(key, None)
        os.environ.update(saved)

class TestMSVC9Compiler(unittest.TestCase):

    def test_find_vcvarsall_patch(self):
        if not hasattr(distutils, 'msvc9compiler'):
            # skip
            return

        self.assertEqual(
            "setuptools.msvc9_support",
            distutils.msvc9compiler.find_vcvarsall.__module__,
            "find_vcvarsall was not patched"
        )

        find_vcvarsall = distutils.msvc9compiler.find_vcvarsall
        query_vcvarsall = distutils.msvc9compiler.query_vcvarsall

        # No registry entries or environment variable means we should
        # not find anything
        with patch_env(VS90COMNTOOLS=None):
            with MockReg():
                self.assertIsNone(find_vcvarsall(9.0))

                try:
                    query_vcvarsall(9.0)
                    self.fail('Expected DistutilsPlatformError from query_vcvarsall()')
                except distutils.errors.DistutilsPlatformError:
                    exc_message = str(sys.exc_info()[1])
                self.assertIn('aka.ms/vcpython27', exc_message)

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
            with MockReg(
                hkey_current_user={key_32: mock_installdir_1},
                hkey_local_machine={
                    key_32: mock_installdir_2,
                    key_64: mock_installdir_2,
                }
            ):
                self.assertEqual(mock_vcvarsall_bat_1, find_vcvarsall(9.0))

            # Ensure we get the local machine value if it's there
            with MockReg(hkey_local_machine={key_32: mock_installdir_2}):
                self.assertEqual(mock_vcvarsall_bat_2, find_vcvarsall(9.0))

            # Ensure we prefer the 64-bit local machine key
            # (*not* the Wow6432Node key)
            with MockReg(
                hkey_local_machine={
                    # This *should* only exist on 32-bit machines
                    key_32: mock_installdir_1,
                    # This *should* only exist on 64-bit machines
                    key_64: mock_installdir_2,
                }
            ):
                self.assertEqual(mock_vcvarsall_bat_1, find_vcvarsall(9.0))
        finally:
            shutil.rmtree(mock_installdir_1)
            shutil.rmtree(mock_installdir_2)
