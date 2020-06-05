# coding: utf-8

from pkg_resources import safe_version
from setuptools import sic


class TestSafeVersion:

    def test_safe_version_ok(self):
        actual = '1.2.3'
        safe = safe_version(actual)
        assert safe == actual

    def test_invalid_version_whitespace(self):
        actual = '1 2 3'
        safe = safe_version(actual)
        assert safe == '1.2.3'

    def test_invalid_version_regex(self):
        actual = '1.2.3%4'
        safe = safe_version(actual)
        assert safe == '1.2.3-4'

    def test_sic_version(self):
        actual = sic('1.2.3.beta')
        safe = safe_version(actual)
        assert safe == actual
