"""Tests for setuptools.find_packages()."""
import os
import shutil
import sys
import tempfile
import unittest

from setuptools import find_packages


PEP420 = sys.version_info[:2] >= (3, 3)


class TestFindPackages(unittest.TestCase):

    def setUp(self):
        self.dist_dir = tempfile.mkdtemp()
        self._make_pkg_structure()

    def tearDown(self):
        shutil.rmtree(self.dist_dir)

    def _make_pkg_structure(self):
        """Make basic package structure.

        dist/
            docs/
                conf.py
            pkg/
                __pycache__/
                nspkg/
                    mod.py
                subpkg/
                    assets/
                        asset
                    __init__.py
            setup.py

        """
        self.docs_dir = self._mkdir('docs', self.dist_dir)
        self._touch('conf.py', self.docs_dir)
        self.pkg_dir = self._mkdir('pkg', self.dist_dir)
        self._mkdir('__pycache__', self.pkg_dir)
        self.ns_pkg_dir = self._mkdir('nspkg', self.pkg_dir)
        self._touch('mod.py', self.ns_pkg_dir)
        self.sub_pkg_dir = self._mkdir('subpkg', self.pkg_dir)
        self.asset_dir = self._mkdir('assets', self.sub_pkg_dir)
        self._touch('asset', self.asset_dir)
        self._touch('__init__.py', self.sub_pkg_dir)
        self._touch('setup.py', self.dist_dir)

    def _mkdir(self, path, parent_dir=None):
        if parent_dir:
            path = os.path.join(parent_dir, path)
        os.mkdir(path)
        return path

    def _touch(self, path, dir_=None):
        if dir_:
            path = os.path.join(dir_, path)
        fp = open(path, 'w')
        fp.close()
        return path

    @unittest.skipIf(PEP420, 'Not a PEP 420 env')
    def test_regular_package(self):
        self._touch('__init__.py', self.pkg_dir)
        packages = find_packages(self.dist_dir)
        self.assertEqual(packages, ['pkg', 'pkg.subpkg'])

    def test_dir_with_dot_is_skipped(self):
        shutil.rmtree(os.path.join(self.dist_dir, 'pkg/subpkg/assets'))
        data_dir = self._mkdir('some.data', self.pkg_dir)
        self._touch('__init__.py', data_dir)
        self._touch('file.dat', data_dir)
        packages = find_packages(self.dist_dir)
        self.assertNotIn('pkg.some.data', packages)

    @unittest.skipIf(not PEP420, 'PEP 420 only')
    def test_pep420_ns_package(self):
        packages = find_packages(
            self.dist_dir, include=['pkg*'], exclude=['pkg.subpkg.assets'])
        self.assertEqual(packages, ['pkg', 'pkg.nspkg', 'pkg.subpkg'])

    @unittest.skipIf(not PEP420, 'PEP 420 only')
    def test_pep420_ns_package_no_includes(self):
        packages = find_packages(
            self.dist_dir, exclude=['pkg.subpkg.assets'])
        self.assertEqual(packages, ['docs', 'pkg', 'pkg.nspkg', 'pkg.subpkg'])

    @unittest.skipIf(not PEP420, 'PEP 420 only')
    def test_pep420_ns_package_no_includes_or_excludes(self):
        packages = find_packages(self.dist_dir)
        expected = [
            'docs', 'pkg', 'pkg.nspkg', 'pkg.subpkg', 'pkg.subpkg.assets']
        self.assertEqual(packages, expected)

    @unittest.skipIf(not PEP420, 'PEP 420 only')
    def test_regular_package_with_nested_pep420_ns_packages(self):
        self._touch('__init__.py', self.pkg_dir)
        packages = find_packages(
            self.dist_dir, exclude=['docs', 'pkg.subpkg.assets'])
        self.assertEqual(packages, ['pkg', 'pkg.nspkg', 'pkg.subpkg'])

    @unittest.skipIf(not PEP420, 'PEP 420 only')
    def test_pep420_ns_package_no_non_package_dirs(self):
        shutil.rmtree(self.docs_dir)
        shutil.rmtree(os.path.join(self.dist_dir, 'pkg/subpkg/assets'))
        packages = find_packages(self.dist_dir)
        self.assertEqual(packages, ['pkg', 'pkg.nspkg', 'pkg.subpkg'])
