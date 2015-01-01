"""develop tests
"""
import os
import re
import shutil
import site
import sys
import tempfile
import unittest

from setuptools.dist import Distribution

from . import contexts


SETUP_PY = """\
from setuptools import setup

setup(name='foo', py_modules=['hi'])
"""

class TestDevelopTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.dir)
        with open('setup.py', 'w') as f:
            f.write(SETUP_PY)
        with open('hi.py', 'w') as f:
            f.write('1\n')
        if sys.version >= "2.6":
            self.old_base = site.USER_BASE
            site.USER_BASE = tempfile.mkdtemp()
            self.old_site = site.USER_SITE
            site.USER_SITE = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.dir)
        if sys.version >= "2.6":
            shutil.rmtree(site.USER_BASE)
            shutil.rmtree(site.USER_SITE)
            site.USER_BASE = self.old_base
            site.USER_SITE = self.old_site

    def test_bdist_egg(self):
        dist = Distribution(dict(
            script_name='setup.py',
            script_args=['bdist_egg'],
            name='foo',
            py_modules=['hi']
            ))
        os.makedirs(os.path.join('build', 'src'))
        with contexts.quiet():
            dist.parse_command_line()
            dist.run_commands()

        # let's see if we got our egg link at the right place
        [content] = os.listdir('dist')
        self.assertTrue(re.match('foo-0.0.0-py[23].\d.egg$', content))

def test_suite():
    return unittest.makeSuite(TestDevelopTest)

