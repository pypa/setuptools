import sys
import os
import tempfile
import unittest
import shutil
import copy

CURDIR = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.split(CURDIR)[0]
sys.path.insert(0, TOPDIR)

from ez_setup import (use_setuptools, _build_egg, _python_cmd, _do_download,
    _install, DEFAULT_URL, DEFAULT_VERSION)
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
                    "--dist-dir", "%s" % self.tmpdir)
        tarball = os.listdir(self.tmpdir)[0]
        self.tarball = os.path.join(self.tmpdir, tarball)
        from setuptools.compat import urllib2
        urllib2.urlopen = self.urlopen

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        os.chdir(self.cwd)
        sys.path = copy.copy(self.old_sys_path)

    def test_build_egg(self):
        # making it an egg
        egg = _build_egg('Egg to be built', self.tarball, self.tmpdir)

        # now trying to import it
        sys.path[0] = egg
        import setuptools
        self.assertTrue(setuptools.__file__.startswith(egg))

    def test_do_download(self):
        tmpdir = tempfile.mkdtemp()
        _do_download(DEFAULT_VERSION, DEFAULT_URL, tmpdir, 1)
        import setuptools
        self.assertTrue(setuptools.bootstrap_install_from.startswith(tmpdir))

    def test_install(self):
        def _faked(*args):
            return True
        ez_setup.python_cmd = _faked
        _install(self.tarball)

    def test_use_setuptools(self):
        self.assertEqual(use_setuptools(), None)

if __name__ == '__main__':
    unittest.main()
