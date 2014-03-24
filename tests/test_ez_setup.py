import sys
import os
import tempfile
import unittest
import shutil
import copy

CURDIR = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.split(CURDIR)[0]
sys.path.insert(0, TOPDIR)

from ez_setup import (use_setuptools, _python_cmd, _install)
import ez_setup

class TestSetup(unittest.TestCase):

    def urlopen(self, url):
        return open(self.tarball, 'rb')

    def setUp(self):
        self.old_sys_path = copy.copy(sys.path)
        self.cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(TOPDIR)
        _python_cmd("setup.py", "-q", "egg_info", "-RDb", "", "sdist",
            "--formats", "zip", "--dist-dir", self.tmpdir)
        zipball = os.listdir(self.tmpdir)[0]
        self.zipball = os.path.join(self.tmpdir, zipball)
        from setuptools.compat import urllib2
        urllib2.urlopen = self.urlopen

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        os.chdir(self.cwd)
        sys.path = copy.copy(self.old_sys_path)

    def test_install(self):
        def _faked(*args):
            return True
        ez_setup._python_cmd = _faked
        _install(self.zipball)

    def test_use_setuptools(self):
        self.assertEqual(use_setuptools(), None)

if __name__ == '__main__':
    unittest.main()
