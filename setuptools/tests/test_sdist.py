"""sdist tests"""


import os
import shutil
import sys
import tempfile
import unittest
from StringIO import StringIO


from setuptools.command.sdist import sdist
from setuptools.dist import Distribution


SETUP_ATTRS = {
    'name': 'sdist_test',
    'version': '0.0',
    'packages': ['sdist_test'],
    'package_data': {'sdist_test': ['*.txt']}
}


SETUP_PY = """\
from setuptools import setup

setup(**%r)
""" % SETUP_ATTRS


class TestSdistTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        f = open(os.path.join(self.temp_dir, 'setup.py'), 'w')
        f.write(SETUP_PY)
        f.close()
        # Set up the rest of the test package
        test_pkg = os.path.join(self.temp_dir, 'sdist_test')
        os.mkdir(test_pkg)
        # *.rst was not included in package_data, so c.rst should not be
        # automatically added to the manifest when not under version control
        for fname in ['__init__.py', 'a.txt', 'b.txt', 'c.rst']:
            # Just touch the files; their contents are irrelevant
            open(os.path.join(test_pkg, fname), 'w').close()

        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)

    def test_package_data_in_sdist(self):
        """Regression test for pull request #4: ensures that files listed in
        package_data are included in the manifest even if they're not added to
        version control.
        """

        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        # squelch output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        try:
            cmd.run()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        manifest = cmd.filelist.files

        self.assert_(os.path.join('sdist_test', 'a.txt') in manifest)
        self.assert_(os.path.join('sdist_test', 'b.txt') in manifest)
        self.assert_(os.path.join('sdist_test', 'c.rst') not in manifest)
