# -*- coding: utf-8 -*-

"""Tests for setuptools.get_version()."""
import os
import codecs
import tempfile

import pytest

from setuptools import __version__, get_version


def test_own_version():
    version = get_version('setup.cfg', field='current_version')

    # `setup.py egg_info` which is run in bootstrap.py during package
    # installation adds `.post` prefix to setuptools.__version__
    # which becomes different from 'setup.cfg` file

    # https://setuptools.readthedocs.io/en/latest/setuptools.html#egg-info

    assert __version__.startswith(version + '.post')


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

    def test_python_file(self):
        version = get_version(self.ver_python)
        assert version == '0.23beta'

    def test_non_utf8_python_file(self):
        version2 = get_version(self.ver_russian)
        assert version2 == '17.0'

