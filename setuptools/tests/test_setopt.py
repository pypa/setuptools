# coding: utf-8

from __future__ import unicode_literals

import io

import six

from setuptools.command import setopt
from setuptools.extern.six.moves import configparser


class TestEdit:
    @staticmethod
    def parse_config(filename):
        parser = configparser.ConfigParser()
        with io.open(filename, encoding='utf-8') as reader:
            (parser.read_file if six.PY3 else parser.readfp)(reader)
        return parser

    @staticmethod
    def write_text(file, content):
        with io.open(file, 'wb') as strm:
            strm.write(content.encode('utf-8'))

    def test_utf8_encoding_retained(self, tmpdir):
        """
        When editing a file, non-ASCII characters encoded in
        UTF-8 should be retained.
        """
        config = tmpdir.join('setup.cfg')
        self.write_text(str(config), '[names]\njaraco=джарако')
        setopt.edit_config(str(config), dict(names=dict(other='yes')))
        parser = self.parse_config(str(config))
        assert parser.get('names', 'jaraco') == 'джарако'
        assert parser.get('names', 'other') == 'yes'
