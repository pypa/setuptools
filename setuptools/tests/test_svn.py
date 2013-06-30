# -*- coding: utf-8 -*-
"""svn tests"""


import os
import sys
import tempfile
import unittest
import shutil
import stat

import setuptools.command.egg_info as egg_info
#requires python >= 2.4
from subprocess import call as _call

def _remove_dir(target):
    
    #on windows this seems to a problem
    for dir_path, dirs, files in os.walk(target):
        os.chmod(dir_path, stat.S_IWRITE)
        for filename in files:
            os.chmod(os.path.join(dir_path, filename), stat.S_IWRITE)
    shutil.rmtree(target)

class TestEmptySvn(unittest.TestCase):



    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        #apparently there is a standing bug in python about having
        #to use shell=True in windows to get a path search.
        if _call(['svnadmin', 'create', 'svn'], shell=(sys.platform == 'win32')):
            raise 'Failed to create SVN repository'

        self.svnrepo = os.path.join(self.temp_dir, 'svn')

        if _call(['svn', 'checkout', 'file:///' + self.svnrepo.replace('\\','/'), 'co']):
            os.chdir(self.old_cwd)
            _remove_dir(self.temp_dir)
            raise 'Failed to checkout SVN repository'

        os.chdir(os.path.join(self.temp_dir, 'co'))

    def tearDown(self):
        os.chdir(self.old_cwd)
        _remove_dir(self.temp_dir)

    def test_can_get_revision_empty(self):
        """Check that svn revision can be retrieved from an working set on an empty repository."""
        self.assertEquals('0', egg_info._get_svn_revision())

    def test_can_get_revision_single_commit(self):
        """Check that svn revision can be retrieved from an working set on an empty repository."""
    
        open('README', 'w').close()
        exitcode = _call(['svn', 'add', 'README'], shell=(sys.platform == 'win32'))
        self.assertEqual(0, exitcode)
        
        exitcode = _call(['svn', 'commit', '-m', '"README added"'], shell=(sys.platform == 'win32'))
        self.assertEqual(0, exitcode)

        exitcode = _call(['svn', 'update'], shell=(sys.platform == 'win32'))
        self.assertEqual(0, exitcode)

        self.assertEquals('1', egg_info._get_svn_revision())


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

