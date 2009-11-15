"""develop tests
"""
import sys
import os, shutil, tempfile, unittest
import tempfile
import site
from StringIO import StringIO

from setuptools.command.develop import develop
from setuptools.command import develop as develop_pkg
from setuptools.dist import Distribution

SETUP_PY = """\
from setuptools import setup

setup(name='foo')
"""

class TestDevelopTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        setup = os.path.join(self.dir, 'setup.py')
        f = open(setup, 'w')
        f.write(SETUP_PY)
        f.close()
        self.old_cwd = os.getcwd()
        os.chdir(self.dir)
        if sys.version >= "2.6":
            self.old_base = site.USER_BASE
            site.USER_BASE = develop_pkg.USER_BASE = tempfile.mkdtemp()
            self.old_site = site.USER_SITE
            site.USER_SITE = develop_pkg.USER_SITE = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.dir)
        if sys.version >= "2.6":
            shutil.rmtree(site.USER_BASE)
            shutil.rmtree(site.USER_SITE)
            site.USER_BASE = self.old_base
            site.USER_SITE = self.old_site

    def test_develop(self):
        if sys.version < "2.6":
            return
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = develop(dist)
        cmd.user = 1
        cmd.ensure_finalized()
        cmd.user = 1
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cmd.run()
        finally:
            sys.stdout = old_stdout

        # let's see if we got our egg link at the right place
        content = os.listdir(site.USER_SITE)
        content.sort()
        self.assertEquals(content, ['UNKNOWN.egg-link', 'easy-install.pth'])

