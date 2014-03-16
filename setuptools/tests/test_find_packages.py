"""Tests for setuptools.find_packages()."""
import os
import shutil
import tempfile
import unittest

from setuptools import find_packages


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

    def test_regular_package(self):
        self._touch('__init__.py', self.pkg_dir)
        packages = find_packages(self.dist_dir)
        self.assertEqual(packages, ['pkg', 'pkg.subpkg'])

    def test_include_excludes_other(self):
        """
        If include is specified, other packages should be excluded.
        """
        self._touch('__init__.py', self.pkg_dir)
        alt_dir = self._mkdir('other_pkg', self.dist_dir)
        self._touch('__init__.py', alt_dir)
        packages = find_packages(self.dist_dir, include=['other_pkg'])
        self.assertEqual(packages, ['other_pkg'])

    def test_dir_with_dot_is_skipped(self):
        shutil.rmtree(os.path.join(self.dist_dir, 'pkg/subpkg/assets'))
        data_dir = self._mkdir('some.data', self.pkg_dir)
        self._touch('__init__.py', data_dir)
        self._touch('file.dat', data_dir)
        packages = find_packages(self.dist_dir)
        self.assertTrue('pkg.some.data' not in packages)
