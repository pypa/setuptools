import sys
import os
import tempfile
import unittest
import shutil
import copy

CURDIR = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.split(CURDIR)[0]
sys.path.insert(0, TOPDIR)

from distribute_setup import (use_setuptools, _build_egg, _python_cmd,
                              _do_download, _install, DEFAULT_URL,
                              DEFAULT_VERSION)
import distribute_setup

class TestPython33BdistEgg(unittest.TestCase):

    def test_build_egg(self):
        os.chdir(os.path.join(CURDIR, 'python3.3_bdist_egg_test'))
        self.assertTrue(_python_cmd("setup.py", "bdist_egg"))


if __name__ == '__main__':
    unittest.main()
