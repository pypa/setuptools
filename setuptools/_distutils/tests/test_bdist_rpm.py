"""Tests for distutils.command.bdist_rpm."""

import unittest
import sys
import os

import pytest

from distutils.core import Distribution
from distutils.command.bdist_rpm import bdist_rpm
from distutils.tests import support
from distutils.spawn import find_executable

from .py38compat import requires_zlib


SETUP_PY = """\
from distutils.core import setup
import foo

setup(name='foo', version='0.1', py_modules=['foo'],
      url='xxx', author='xxx', author_email='xxx')

"""


@pytest.fixture(autouse=True)
def sys_executable_encodable():
    try:
        sys.executable.encode('UTF-8')
    except UnicodeEncodeError:
        pytest.skip("sys.executable is not encodable to UTF-8")


@pytest.mark.usefixtures('save_env')
@pytest.mark.usefixtures('save_argv')
@pytest.mark.usefixtures('save_cwd')
class TestBuildRpm(
    support.TempdirManager,
    support.LoggingSilencer,
):

    # XXX I am unable yet to make this test work without
    # spurious sdtout/stderr output under Mac OS X
    @unittest.skipUnless(
        sys.platform.startswith('linux'), 'spurious sdtout/stderr output under Mac OS X'
    )
    @requires_zlib()
    @unittest.skipIf(find_executable('rpm') is None, 'the rpm command is not found')
    @unittest.skipIf(
        find_executable('rpmbuild') is None, 'the rpmbuild command is not found'
    )
    def test_quiet(self):
        # let's create a package
        tmp_dir = self.mkdtemp()
        os.environ['HOME'] = tmp_dir  # to confine dir '.rpmdb' creation
        pkg_dir = os.path.join(tmp_dir, 'foo')
        os.mkdir(pkg_dir)
        self.write_file((pkg_dir, 'setup.py'), SETUP_PY)
        self.write_file((pkg_dir, 'foo.py'), '#')
        self.write_file((pkg_dir, 'MANIFEST.in'), 'include foo.py')
        self.write_file((pkg_dir, 'README'), '')

        dist = Distribution(
            {
                'name': 'foo',
                'version': '0.1',
                'py_modules': ['foo'],
                'url': 'xxx',
                'author': 'xxx',
                'author_email': 'xxx',
            }
        )
        dist.script_name = 'setup.py'
        os.chdir(pkg_dir)

        sys.argv = ['setup.py']
        cmd = bdist_rpm(dist)
        cmd.fix_python = True

        # running in quiet mode
        cmd.quiet = 1
        cmd.ensure_finalized()
        cmd.run()

        dist_created = os.listdir(os.path.join(pkg_dir, 'dist'))
        assert 'foo-0.1-1.noarch.rpm' in dist_created

        # bug #2945: upload ignores bdist_rpm files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.src.rpm') in dist.dist_files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.noarch.rpm') in dist.dist_files

    # XXX I am unable yet to make this test work without
    # spurious sdtout/stderr output under Mac OS X
    @unittest.skipUnless(
        sys.platform.startswith('linux'), 'spurious sdtout/stderr output under Mac OS X'
    )
    @requires_zlib()
    # http://bugs.python.org/issue1533164
    @unittest.skipIf(find_executable('rpm') is None, 'the rpm command is not found')
    @unittest.skipIf(
        find_executable('rpmbuild') is None, 'the rpmbuild command is not found'
    )
    def test_no_optimize_flag(self):
        # let's create a package that breaks bdist_rpm
        tmp_dir = self.mkdtemp()
        os.environ['HOME'] = tmp_dir  # to confine dir '.rpmdb' creation
        pkg_dir = os.path.join(tmp_dir, 'foo')
        os.mkdir(pkg_dir)
        self.write_file((pkg_dir, 'setup.py'), SETUP_PY)
        self.write_file((pkg_dir, 'foo.py'), '#')
        self.write_file((pkg_dir, 'MANIFEST.in'), 'include foo.py')
        self.write_file((pkg_dir, 'README'), '')

        dist = Distribution(
            {
                'name': 'foo',
                'version': '0.1',
                'py_modules': ['foo'],
                'url': 'xxx',
                'author': 'xxx',
                'author_email': 'xxx',
            }
        )
        dist.script_name = 'setup.py'
        os.chdir(pkg_dir)

        sys.argv = ['setup.py']
        cmd = bdist_rpm(dist)
        cmd.fix_python = True

        cmd.quiet = 1
        cmd.ensure_finalized()
        cmd.run()

        dist_created = os.listdir(os.path.join(pkg_dir, 'dist'))
        assert 'foo-0.1-1.noarch.rpm' in dist_created

        # bug #2945: upload ignores bdist_rpm files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.src.rpm') in dist.dist_files
        assert ('bdist_rpm', 'any', 'dist/foo-0.1-1.noarch.rpm') in dist.dist_files

        os.remove(os.path.join(pkg_dir, 'dist', 'foo-0.1-1.noarch.rpm'))
