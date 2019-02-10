# -*- encoding: utf-8 -*-

"""Tests for setuptools.get_version()."""
import os
import codecs
import tempfile

import pytest

from setuptools import __version__, get_version


def test_get_version():
    version = get_version('setup.cfg', field='current_version')
    assert version == __version__


class TestFiles:
    def setup_method(self, method):
        self.tmpdir = tempfile.mkdtemp()

        self.file_python = os.path.join(self.tmpdir, 'version.py') 
        with open(self.file_python, 'w') as fp:
            fp.write('__version__ = "0.23beta"\n')

        self.file_russian = os.path.join(self.tmpdir, 'russian.py') 
        with open(self.file_russian, 'wb') as fp:
            fp.write('# файл в русской кодировке\n\n'.encode('cp1251'))
            fp.write('__version__ = "17.0"\n')

    def teardown_method(self, method):
        shutil.rmtree(self.dist_dir)

    def test_get_version_files(self):
        version = get_version(self.ver_python)
        assert version == '0.23beta'

        version2 = get_version(self.ver_russian)
        assert version2 == '17.0'

