import sys
import os
import tempfile
import unittest
import shutil
import copy

CURDIR = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.split(CURDIR)[0]
sys.path.insert(0, TOPDIR)

from distribute_setup import (use_setuptools, _build_egg, python_cmd,
                              _do_download, _install)
import distribute_setup

class TestSetup(unittest.TestCase):

    def urlopen(self, url):
        return open(self.tarball)

    def setUp(self):
        self.old_sys_path = copy.copy(sys.path)
        self.cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(TOPDIR)
        python_cmd("setup.py -q egg_info -RDb '' sdist --dist-dir %s" % \
                self.tmpdir)
        tarball = os.listdir(self.tmpdir)[0]
        self.tarball = os.path.join(self.tmpdir, tarball)
        import urllib2
        urllib2.urlopen = self.urlopen

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        os.chdir(self.cwd)
        sys.path = copy.copy(self.old_sys_path)

    def test_build_egg(self):
        # making it an egg
        egg = _build_egg(self.tarball, self.tmpdir)

        # now trying to import it
        sys.path[0] = egg
        import setuptools
        self.assert_(setuptools.__file__.startswith(egg))

    def test_do_download(self):

        tmpdir = tempfile.mkdtemp()
        _do_download(to_dir=tmpdir)
        import setuptools
        self.assert_(setuptools.bootstrap_install_from.startswith(tmpdir))

    def test_install(self):
        def _faked(*args):
            return True
        distribute_setup.python_cmd = _faked
        _install(self.tarball)

if __name__ == '__main__':
    unittest.main()
