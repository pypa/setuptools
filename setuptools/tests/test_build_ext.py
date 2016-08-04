import sys
import distutils.command.build_ext as orig

from distutils.sysconfig import get_config_var
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution
from setuptools.extension import Extension

class TestBuildExt:

    def test_get_ext_filename(self):
        """
        Setuptools needs to give back the same
        result as distutils, even if the fullname
        is not in ext_map.
        """
        dist = Distribution()
        cmd = build_ext(dist)
        cmd.ext_map['foo/bar'] = ''
        res = cmd.get_ext_filename('foo')
        wanted = orig.build_ext.get_ext_filename(cmd, 'foo')
        assert res == wanted

    def test_abi3_filename(self):
        """
        Filename needs to be loadable by several versions
        of Python 3 if 'is_abi3' is truthy on Extension()
        """
        dist = Distribution(dict(ext_modules=[Extension('spam.eggs', [], is_abi3=True)]))
        cmd = build_ext(dist)
        res = cmd.get_ext_filename('spam.eggs')

        if sys.version_info[0] == 2:
            assert res.endswith(get_config_var('SO'))
        elif sys.platform == 'win32':
            assert res.endswith('eggs.pyd')
        else:
            assert 'abi3' in res