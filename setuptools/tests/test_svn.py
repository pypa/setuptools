# -*- coding: utf-8 -*-
"""svn tests"""


import os
import zipfile
import sys
import tempfile
import unittest
import shutil
import stat

from setuptools import svn_utils
from setuptools.command import egg_info
from setuptools.command import sdist

#requires python >= 2.4
from subprocess import call as _call

def _remove_dir(target):

    #on windows this seems to a problem
    for dir_path, dirs, files in os.walk(target):
        os.chmod(dir_path, stat.S_IWRITE)
        for filename in files:
            os.chmod(os.path.join(dir_path, filename), stat.S_IWRITE)
    shutil.rmtree(target)

class TestSvnVersion(unittest.TestCase):

    def test_no_svn_found(self):
        old_path = os.environ['path']
        os.environ['path'] = ''
        try:
            version = svn_utils.SVNEntries.get_svn_tool_version()
            self.assertEqual(version, '')
        finally:
            os.environ['path'] = old_path

    def test_svn_should_exist(self):
        version = svn_utils.SVNEntries.get_svn_tool_version()
        self.assertNotEqual(version, '')


class TestSvn_1_7(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        zip_file, source, target = [None, None, None]
        try:
            zip_file = zipfile.ZipFile(os.path.join('setuptools', 'tests',
                                                    'svn17_example.zip'))
            for files in zip_file.namelist():
                zip_file.extract(files, self.temp_dir)
        finally:
            if zip_file:
                zip_file.close()
            del zip_file

        self.old_cwd = os.getcwd()
        os.chdir(os.path.join(self.temp_dir, 'svn17_example'))

    def tearDown(self):
        os.chdir(self.old_cwd)
        _remove_dir(self.temp_dir)

    def test_svnentrycmd_is_valid(self):
        entries = svn_utils.SVNEntries.load_dir('.')
        self.assertIsInstance(entries, svn_utils.SVNEntriesCMD)
        self.assertTrue(entries.is_valid())

    def test_svnentrycmd_is_valid(self):
        entries = svn_utils.SVNEntries.load_dir('.')
        self.assertIsInstance(entries, svn_utils.SVNEntriesCMD)
        self.assertTrue(entries.is_valid())

    def test_svnentrycmd_enteries(self):
        entries = svn_utils.SVNEntries.load_dir('.')
        self.assertIsInstance(entries, svn_utils.SVNEntriesCMD)
        self.assertEqual(entries.parse_revision(), 4)
        self.assertEqual(set(entries.get_undeleted_records()),
                         set([u'readme.txt', u'other']))
        self.assertEqual(set(entries.get_external_dirs('dir-props')),
            set([u'third_party3', u'third_party2', u'third_party']))

    def test_egg_info(self):
        rev = egg_info.egg_info.get_svn_revision()
        self.assertEqual(rev, '4')

    def test_entry_iterator(self):
        expected = set([
            os.path.join('.', 'readme.txt'),
            os.path.join('.', 'other'),
            os.path.join('.', 'other', 'test.py'),
            ])
        self.assertEqual(set(x for x in sdist.entries_finder('.', '')),
                         expected)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

