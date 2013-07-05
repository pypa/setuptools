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

def _extract(self, member, path=None, pwd=None):
    """for zipfile py2.5 borrowed from cpython"""
    if not isinstance(member, zipfile.ZipInfo):
        member = self.getinfo(member)

    if path is None:
        path = os.getcwd()

    return _extract_member(self, member, path, pwd)

def _extract_from_zip(self, name, dest_path):
    dest_file = open(dest_path, 'wb')
    try:
        dest_file.write(self.read(name))
    finally:
        dest_file.close()

def _extract_member(self, member, targetpath, pwd):
    """for zipfile py2.5 borrowed from cpython"""
    # build the destination pathname, replacing
    # forward slashes to platform specific separators.
    # Strip trailing path separator, unless it represents the root.
    if (targetpath[-1:] in (os.path.sep, os.path.altsep)
        and len(os.path.splitdrive(targetpath)[1]) > 1):
        targetpath = targetpath[:-1]

    # don't include leading "/" from file name if present
    if member.filename[0] == '/':
        targetpath = os.path.join(targetpath, member.filename[1:])
    else:
        targetpath = os.path.join(targetpath, member.filename)

    targetpath = os.path.normpath(targetpath)

    # Create all upper directories if necessary.
    upperdirs = os.path.dirname(targetpath)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    if member.filename[-1] == '/':
        if not os.path.isdir(targetpath):
            os.mkdir(targetpath)
        return targetpath

    _extract_from_zip(self, member.filename, targetpath)

    return targetpath


def _remove_dir(target):

    #on windows this seems to a problem
    for dir_path, dirs, files in os.walk(target):
        os.chmod(dir_path, stat.S_IWRITE)
        for filename in files:
            os.chmod(os.path.join(dir_path, filename), stat.S_IWRITE)
    shutil.rmtree(target)


class TestSvnVersion(unittest.TestCase):

    def test_no_svn_found(self):
        path_variable = None
        for env in os.environ:
            if env.lower() == 'path':
                path_variable = env

        if path_variable is None:
            self.skipTest('Cannot figure out how to modify path')

        old_path = os.environ[path_variable]
        os.environ[path_variable] = ''
        try:
            version = svn_utils.get_svn_tool_version()
            self.assertEqual(version, '')
        finally:
            os.environ[path_variable] = old_path

    def test_svn_should_exist(self):
        version = svn_utils.get_svn_tool_version()
        self.assertNotEqual(version, '')


class TestSvn_1_7(unittest.TestCase):

    def setUp(self):
        version = svn_utils.get_svn_tool_version()
        ver_list = [int(x) for x in version.split('.')]
        if ver_list < [1,7,0]:
            self.version_err = 'Insufficent Subversion (%s)' % version
        else:
            self.version_err = None


        self.temp_dir = tempfile.mkdtemp()
        zip_file, source, target = [None, None, None]
        try:
            zip_file = zipfile.ZipFile(os.path.join('setuptools', 'tests',
                                                    'svn17_example.zip'))
            for files in zip_file.namelist():
                _extract(zip_file, files, self.temp_dir)
        finally:
            if zip_file:
                zip_file.close()
            del zip_file

        self.old_cwd = os.getcwd()
        os.chdir(os.path.join(self.temp_dir, 'svn17_example'))

    def tearDown(self):
        try:
            os.chdir(self.old_cwd)
            _remove_dir(self.temp_dir)
        except OSError:
            #sigh?
            pass

    def _chk_skip(self):
        if self.version_err is not None:
            if hasattr(self, 'skipTest'):
                self.skipTest(self.version_err)
            else:
                sys.stderr.write(self.version_error + "\n")
                return True
        return False

    def test_egg_info(self):
        if self._chk_skip:
            return

        rev = egg_info.egg_info.get_svn_revision()
        self.assertEqual(rev, '4')

    def test_iterator(self):
        if self._chk_skip:
            return

        expected = set([
            os.path.join('.', 'readme.txt'),
            os.path.join('.', 'other'),
            os.path.join('.', 'third_party'),
            os.path.join('.', 'third_party2'),
            os.path.join('.', 'third_party3'),
            ])
        self.assertEqual(set(x for x
                               in sdist.entries_externals_finder('.', '')),
                         expected)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

