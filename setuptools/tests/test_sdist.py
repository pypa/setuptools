# -*- coding: utf-8 -*-
"""sdist tests"""

from __future__ import print_function, unicode_literals

import os
import sys
import tempfile
import unicodedata
import contextlib
import io

from setuptools.extern import six
from setuptools.extern.six.moves import map

import pytest

import pkg_resources
from setuptools.command.sdist import sdist
from setuptools.command.egg_info import manifest_maker
from setuptools.dist import Distribution
from setuptools.tests import fail_on_ascii
from .text import Filenames
from . import py3_only


SETUP_ATTRS = {
    'name': 'sdist_test',
    'version': '0.0',
    'packages': ['sdist_test'],
    'package_data': {'sdist_test': ['*.txt']},
    'data_files': [("data", [os.path.join("d", "e.dat")])],
}

SETUP_PY = """\
from setuptools import setup

setup(**%r)
""" % SETUP_ATTRS


@contextlib.contextmanager
def quiet():
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = six.StringIO(), six.StringIO()
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


# Convert to POSIX path
def posix(path):
    if six.PY3 and not isinstance(path, str):
        return path.replace(os.sep.encode('ascii'), b'/')
    else:
        return path.replace(os.sep, '/')


# HFS Plus uses decomposed UTF-8
def decompose(path):
    if isinstance(path, six.text_type):
        return unicodedata.normalize('NFD', path)
    try:
        path = path.decode('utf-8')
        path = unicodedata.normalize('NFD', path)
        path = path.encode('utf-8')
    except UnicodeError:
        pass  # Not UTF-8
    return path


def read_all_bytes(filename):
    with io.open(filename, 'rb') as fp:
        return fp.read()


def latin1_fail():
    try:
        desc, filename = tempfile.mkstemp(suffix=Filenames.latin_1)
        os.close(desc)
        os.remove(filename)
    except Exception:
        return True


fail_on_latin1_encoded_filenames = pytest.mark.xfail(
    latin1_fail(),
    reason="System does not support latin-1 filenames",
)


def touch(path):
    path.write_text('', encoding='utf-8')


class TestSdistTest:
    @pytest.fixture(autouse=True)
    def source_dir(self, tmpdir):
        (tmpdir / 'setup.py').write_text(SETUP_PY, encoding='utf-8')

        # Set up the rest of the test package
        test_pkg = tmpdir / 'sdist_test'
        test_pkg.mkdir()
        data_folder = tmpdir / 'd'
        data_folder.mkdir()
        # *.rst was not included in package_data, so c.rst should not be
        # automatically added to the manifest when not under version control
        for fname in ['__init__.py', 'a.txt', 'b.txt', 'c.rst']:
            touch(test_pkg / fname)
        touch(data_folder / 'e.dat')

        with tmpdir.as_cwd():
            yield

    def test_package_data_in_sdist(self):
        """Regression test for pull request #4: ensures that files listed in
        package_data are included in the manifest even if they're not added to
        version control.
        """

        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        with quiet():
            cmd.run()

        manifest = cmd.filelist.files
        assert os.path.join('sdist_test', 'a.txt') in manifest
        assert os.path.join('sdist_test', 'b.txt') in manifest
        assert os.path.join('sdist_test', 'c.rst') not in manifest
        assert os.path.join('d', 'e.dat') in manifest

    def test_setup_py_exists(self):
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'foo.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        with quiet():
            cmd.run()

        manifest = cmd.filelist.files
        assert 'setup.py' in manifest

    def test_setup_py_missing(self):
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'foo.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        if os.path.exists("setup.py"):
            os.remove("setup.py")
        with quiet():
            cmd.run()

        manifest = cmd.filelist.files
        assert 'setup.py' not in manifest

    def test_setup_py_excluded(self):
        with open("MANIFEST.in", "w") as manifest_file:
            manifest_file.write("exclude setup.py")

        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'foo.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        with quiet():
            cmd.run()

        manifest = cmd.filelist.files
        assert 'setup.py' not in manifest

    def test_defaults_case_sensitivity(self, tmpdir):
        """
        Make sure default files (README.*, etc.) are added in a case-sensitive
        way to avoid problems with packages built on Windows.
        """

        touch(tmpdir / 'readme.rst')
        touch(tmpdir / 'SETUP.cfg')

        dist = Distribution(SETUP_ATTRS)
        # the extension deliberately capitalized for this test
        # to make sure the actual filename (not capitalized) gets added
        # to the manifest
        dist.script_name = 'setup.PY'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        with quiet():
            cmd.run()

        # lowercase all names so we can test in a
        # case-insensitive way to make sure the files
        # are not included.
        manifest = map(lambda x: x.lower(), cmd.filelist.files)
        assert 'readme.rst' not in manifest, manifest
        assert 'setup.py' not in manifest, manifest
        assert 'setup.cfg' not in manifest, manifest

    @fail_on_ascii
    def test_manifest_is_written_with_utf8_encoding(self):
        # Test for #303.
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        mm = manifest_maker(dist)
        mm.manifest = os.path.join('sdist_test.egg-info', 'SOURCES.txt')
        os.mkdir('sdist_test.egg-info')

        # UTF-8 filename
        filename = os.path.join('sdist_test', 'smörbröd.py')

        # Must create the file or it will get stripped.
        open(filename, 'w').close()

        # Add UTF-8 filename and write manifest
        with quiet():
            mm.run()
            mm.filelist.append(filename)
            mm.write_manifest()

        contents = read_all_bytes(mm.manifest)

        # The manifest should be UTF-8 encoded
        u_contents = contents.decode('UTF-8')

        # The manifest should contain the UTF-8 filename
        assert posix(filename) in u_contents

    @py3_only
    @fail_on_ascii
    def test_write_manifest_allows_utf8_filenames(self):
        # Test for #303.
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        mm = manifest_maker(dist)
        mm.manifest = os.path.join('sdist_test.egg-info', 'SOURCES.txt')
        os.mkdir('sdist_test.egg-info')

        filename = os.path.join(b'sdist_test', Filenames.utf_8)

        # Must touch the file or risk removal
        open(filename, "w").close()

        # Add filename and write manifest
        with quiet():
            mm.run()
            u_filename = filename.decode('utf-8')
            mm.filelist.files.append(u_filename)
            # Re-write manifest
            mm.write_manifest()

        contents = read_all_bytes(mm.manifest)

        # The manifest should be UTF-8 encoded
        contents.decode('UTF-8')

        # The manifest should contain the UTF-8 filename
        assert posix(filename) in contents

        # The filelist should have been updated as well
        assert u_filename in mm.filelist.files

    @py3_only
    def test_write_manifest_skips_non_utf8_filenames(self):
        """
        Files that cannot be encoded to UTF-8 (specifically, those that
        weren't originally successfully decoded and have surrogate
        escapes) should be omitted from the manifest.
        See https://bitbucket.org/tarek/distribute/issue/303 for history.
        """
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        mm = manifest_maker(dist)
        mm.manifest = os.path.join('sdist_test.egg-info', 'SOURCES.txt')
        os.mkdir('sdist_test.egg-info')

        # Latin-1 filename
        filename = os.path.join(b'sdist_test', Filenames.latin_1)

        # Add filename with surrogates and write manifest
        with quiet():
            mm.run()
            u_filename = filename.decode('utf-8', 'surrogateescape')
            mm.filelist.append(u_filename)
            # Re-write manifest
            mm.write_manifest()

        contents = read_all_bytes(mm.manifest)

        # The manifest should be UTF-8 encoded
        contents.decode('UTF-8')

        # The Latin-1 filename should have been skipped
        assert posix(filename) not in contents

        # The filelist should have been updated as well
        assert u_filename not in mm.filelist.files

    @fail_on_ascii
    def test_manifest_is_read_with_utf8_encoding(self):
        # Test for #303.
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        # Create manifest
        with quiet():
            cmd.run()

        # Add UTF-8 filename to manifest
        filename = os.path.join(b'sdist_test', Filenames.utf_8)
        cmd.manifest = os.path.join('sdist_test.egg-info', 'SOURCES.txt')
        manifest = open(cmd.manifest, 'ab')
        manifest.write(b'\n' + filename)
        manifest.close()

        # The file must exist to be included in the filelist
        open(filename, 'w').close()

        # Re-read manifest
        cmd.filelist.files = []
        with quiet():
            cmd.read_manifest()

        # The filelist should contain the UTF-8 filename
        if six.PY3:
            filename = filename.decode('utf-8')
        assert filename in cmd.filelist.files

    @py3_only
    @fail_on_latin1_encoded_filenames
    def test_read_manifest_skips_non_utf8_filenames(self):
        # Test for #303.
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        # Create manifest
        with quiet():
            cmd.run()

        # Add Latin-1 filename to manifest
        filename = os.path.join(b'sdist_test', Filenames.latin_1)
        cmd.manifest = os.path.join('sdist_test.egg-info', 'SOURCES.txt')
        manifest = open(cmd.manifest, 'ab')
        manifest.write(b'\n' + filename)
        manifest.close()

        # The file must exist to be included in the filelist
        open(filename, 'w').close()

        # Re-read manifest
        cmd.filelist.files = []
        with quiet():
            cmd.read_manifest()

        # The Latin-1 filename should have been skipped
        filename = filename.decode('latin-1')
        assert filename not in cmd.filelist.files

    @fail_on_ascii
    @fail_on_latin1_encoded_filenames
    def test_sdist_with_utf8_encoded_filename(self):
        # Test for #303.
        dist = Distribution(self.make_strings(SETUP_ATTRS))
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        filename = os.path.join(b'sdist_test', Filenames.utf_8)
        open(filename, 'w').close()

        with quiet():
            cmd.run()

        if sys.platform == 'darwin':
            filename = decompose(filename)

        if six.PY3:
            fs_enc = sys.getfilesystemencoding()

            if sys.platform == 'win32':
                if fs_enc == 'cp1252':
                    # Python 3 mangles the UTF-8 filename
                    filename = filename.decode('cp1252')
                    assert filename in cmd.filelist.files
                else:
                    filename = filename.decode('mbcs')
                    assert filename in cmd.filelist.files
            else:
                filename = filename.decode('utf-8')
                assert filename in cmd.filelist.files
        else:
            assert filename in cmd.filelist.files

    @classmethod
    def make_strings(cls, item):
        if isinstance(item, dict):
            return {
                key: cls.make_strings(value) for key, value in item.items()}
        if isinstance(item, list):
            return list(map(cls.make_strings, item))
        return str(item)

    @fail_on_latin1_encoded_filenames
    def test_sdist_with_latin1_encoded_filename(self):
        # Test for #303.
        dist = Distribution(self.make_strings(SETUP_ATTRS))
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        # Latin-1 filename
        filename = os.path.join(b'sdist_test', Filenames.latin_1)
        open(filename, 'w').close()
        assert os.path.isfile(filename)

        with quiet():
            cmd.run()

        if six.PY3:
            # not all windows systems have a default FS encoding of cp1252
            if sys.platform == 'win32':
                # Latin-1 is similar to Windows-1252 however
                # on mbcs filesys it is not in latin-1 encoding
                fs_enc = sys.getfilesystemencoding()
                if fs_enc != 'mbcs':
                    fs_enc = 'latin-1'
                filename = filename.decode(fs_enc)

                assert filename in cmd.filelist.files
            else:
                # The Latin-1 filename should have been skipped
                filename = filename.decode('latin-1')
                filename not in cmd.filelist.files
        else:
            # Under Python 2 there seems to be no decoded string in the
            # filelist.  However, due to decode and encoding of the
            # file name to get utf-8 Manifest the latin1 maybe excluded
            try:
                # fs_enc should match how one is expect the decoding to
                # be proformed for the manifest output.
                fs_enc = sys.getfilesystemencoding()
                filename.decode(fs_enc)
                assert filename in cmd.filelist.files
            except UnicodeDecodeError:
                filename not in cmd.filelist.files

    def test_pyproject_toml_in_sdist(self, tmpdir):
        """
        Check if pyproject.toml is included in source distribution if present
        """
        touch(tmpdir / 'pyproject.toml')
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()
        with quiet():
            cmd.run()
        manifest = cmd.filelist.files
        assert 'pyproject.toml' in manifest

    def test_pyproject_toml_excluded(self, tmpdir):
        """
        Check that pyproject.toml can excluded even if present
        """
        touch(tmpdir / 'pyproject.toml')
        with open('MANIFEST.in', 'w') as mts:
            print('exclude pyproject.toml', file=mts)
        dist = Distribution(SETUP_ATTRS)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()
        with quiet():
            cmd.run()
        manifest = cmd.filelist.files
        assert 'pyproject.toml' not in manifest


def test_default_revctrl():
    """
    When _default_revctrl was removed from the `setuptools.command.sdist`
    module in 10.0, it broke some systems which keep an old install of
    setuptools (Distribute) around. Those old versions require that the
    setuptools package continue to implement that interface, so this
    function provides that interface, stubbed. See #320 for details.

    This interface must be maintained until Ubuntu 12.04 is no longer
    supported (by Setuptools).
    """
    ep_def = 'svn_cvs = setuptools.command.sdist:_default_revctrl'
    ep = pkg_resources.EntryPoint.parse(ep_def)
    res = ep.resolve()
    assert hasattr(res, '__iter__')
