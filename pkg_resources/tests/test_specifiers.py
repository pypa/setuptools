import pytest

from pkg_resources.extern import packaging


class TestSpecifier:
    def testAllOperators(self):
        for operator in ('', '~=', '==', '!=', '<=', '>=', '<', '>', '==='):
            specifier = packaging.specifiers.Specifier(operator + '3.5')
            assert(specifier.operator == operator)
            assert(specifier.version == '3.5')

    def testVersionFormats(self):
        # A few versions found as examples in PEP440.
        versions = [
            '0.9', '0.9.1', '0.9.2',
            '2012.04',
            '1.0a1', '1.0a2', '1.0b1', '1.0rc1',
            '1.0.dev1', '1.0.post1', '1.0b2.post345.dev456',
            '1.4.*', '1.4.5.*',
        ]
        for version in versions:
            specifier = packaging.specifiers.Specifier('==' + version)
            assert(specifier.operator == '==')
            assert(specifier.version == version)

    def testInvalidSpecifier(self):
        with pytest.raises(packaging.specifiers.InvalidSpecifier):
            # This is a Twiddle Wakka operator, used in Ruby.
            packaging.specifiers.Specifier('~> 2.5')

    def testInvalidCompatibleClause(self):
        with pytest.raises(packaging.specifiers.InvalidSpecifier):
            # PEP440 states that "[The compatible release operator] MUST NOT be
            # used with a single segment version number such as ~=1.
            packaging.specifiers.Specifier('~= 1')
