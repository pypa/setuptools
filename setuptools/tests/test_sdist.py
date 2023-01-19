"""sdist tests"""

import os
import sys
import tempfile
import unicodedata
import contextlib
import io
from unittest import mock

import pytest

from setuptools import Command
from setuptools._importlib import metadata
from setuptools import SetuptoolsDeprecationWarning
from setuptools.command.sdist import sdist
from setuptools.command.egg_info import manifest_maker
from setuptools.dist import Distribution
from setuptools.tests import fail_on_ascii
from .text import Filenames


SETUP_ATTRS = {
    'name': 'sdist_test',
    'version': '0.0',
    'packages': ['sdist_test'],
    'package_data': {'sdist_test': ['*.txt']},
    'data_files': [("data", [os.path.join("d", "e.dat")])],
}

SETUP_PY = (
    """\
from setuptools import setup

setup(**%r)
"""
    % SETUP_ATTRS
)


@contextlib.contextmanager
def quiet():
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


# Convert to POSIX path
def posix(path):
    if not isinstance(path, str):
        return path.replace(os.sep.encode('ascii'), b'/')
    else:
        return path.replace(os.sep, '/')


# HFS Plus uses decomposed UTF-8
def decompose(path):
    if isinstance(path, str):
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


skip_under_xdist = pytest.mark.skipif(
    "os.environ.get('PYTEST_XDIST_WORKER')",
    reason="pytest-dev/pytest-xdist#843",
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

    def assert_package_data_in_manifest(self, cmd):
        manifest = cmd.filelist.files
        assert os.path.join('sdist_test', 'a.txt') in manifest
        assert os.path.join('sdist_test', 'b.txt') in manifest
        assert os.path.join('sdist_test', 'c.rst') not in manifest
        assert os.path.join('d', 'e.dat') in manifest

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

        self.assert_package_data_in_manifest(cmd)

    def test_package_data_and_include_package_data_in_sdist(self):
        """
        Ensure package_data and include_package_data work
        together.
        """
        setup_attrs = {**SETUP_ATTRS, 'include_package_data': True}
        assert setup_attrs['package_data']

        dist = Distribution(setup_attrs)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        with quiet():
            cmd.run()

        self.assert_package_data_in_manifest(cmd)

    def test_custom_build_py(self):
        """
        Ensure projects defining custom build_py don't break
        when creating sdists (issue #2849)
        """
        from distutils.command.build_py import build_py as OrigBuildPy

        using_custom_command_guard = mock.Mock()

        class CustomBuildPy(OrigBuildPy):
            """
            Some projects have custom commands inheriting from `distutils`
            """

            def get_data_files(self):
                using_custom_command_guard()
                return super().get_data_files()

        setup_attrs = {**SETUP_ATTRS, 'include_package_data': True}
        assert setup_attrs['package_data']

        dist = Distribution(setup_attrs)
        dist.script_name = 'setup.py'
        cmd = sdist(dist)
        cmd.ensure_finalized()

        # Make sure we use the custom command
        cmd.cmdclass = {'build_py': CustomBuildPy}
        cmd.distribution.cmdclass = {'build_py': CustomBuildPy}
        assert cmd.distribution.get_command_class('build_py') == CustomBuildPy

        msg = "setuptools instead of distutils"
        with quiet(), pytest.warns(SetuptoolsDeprecationWarning, match=msg):
            cmd.run()

        using_custom_command_guard.assert_called()
        self.assert_package_data_in_manifest(cmd)

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

    @skip_under_xdist
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
        filename = filename.decode('utf-8')
        assert filename in cmd.filelist.files

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

        fs_enc = sys.getfilesystemencoding()

        if sys.platform == 'win32':
            if fs_enc == 'cp1252':
                # Python mangles the UTF-8 filename
                filename = filename.decode('cp1252')
                assert filename in cmd.filelist.files
            else:
                filename = filename.decode('mbcs')
                assert filename in cmd.filelist.files
        else:
            filename = filename.decode('utf-8')
            assert filename in cmd.filelist.files

    @classmethod
    def make_strings(cls, item):
        if isinstance(item, dict):
            return {key: cls.make_strings(value) for key, value in item.items()}
        if isinstance(item, list):
            return list(map(cls.make_strings, item))
        return str(item)

    @fail_on_latin1_encoded_filenames
    @skip_under_xdist
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

    _EXAMPLE_DIRECTIVES = {
        "setup.cfg - long_description and version": """
            [metadata]
            name = testing
            version = file: VERSION.txt
            license_files = DOWHATYOUWANT
            long_description = file: README.rst, USAGE.rst
            """,
        "pyproject.toml - static readme/license files and dynamic version": """
            [project]
            name = "testing"
            readme = "USAGE.rst"
            license = {file = "DOWHATYOUWANT"}
            dynamic = ["version"]
            [tool.setuptools.dynamic]
            version = {file = ["VERSION.txt"]}
            """
    }

    @pytest.mark.parametrize("config", _EXAMPLE_DIRECTIVES.keys())
    def test_add_files_referenced_by_config_directives(self, tmp_path, config):
        config_file, _, _ = config.partition(" - ")
        config_text = self._EXAMPLE_DIRECTIVES[config]
        (tmp_path / 'VERSION.txt').write_text("0.42", encoding="utf-8")
        (tmp_path / 'README.rst').write_text("hello world!", encoding="utf-8")
        (tmp_path / 'USAGE.rst').write_text("hello world!", encoding="utf-8")
        (tmp_path / 'DOWHATYOUWANT').write_text("hello world!", encoding="utf-8")
        (tmp_path / config_file).write_text(config_text, encoding="utf-8")

        dist = Distribution({"packages": []})
        dist.script_name = 'setup.py'
        dist.parse_config_files()

        cmd = sdist(dist)
        cmd.ensure_finalized()
        with quiet():
            cmd.run()

        assert 'VERSION.txt' in cmd.filelist.files
        assert 'USAGE.rst' in cmd.filelist.files
        assert 'DOWHATYOUWANT' in cmd.filelist.files

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

    def test_build_subcommand_source_files(self, tmpdir):
        touch(tmpdir / '.myfile~')

        # Sanity check: without custom commands file list should not be affected
        dist = Distribution({**SETUP_ATTRS, "script_name": "setup.py"})
        cmd = sdist(dist)
        cmd.ensure_finalized()
        with quiet():
            cmd.run()
        manifest = cmd.filelist.files
        assert '.myfile~' not in manifest

        # Test: custom command should be able to augment file list
        dist = Distribution({**SETUP_ATTRS, "script_name": "setup.py"})
        build = dist.get_command_obj("build")
        build.sub_commands = [*build.sub_commands, ("build_custom", None)]

        class build_custom(Command):
            def initialize_options(self):
                ...

            def finalize_options(self):
                ...

            def run(self):
                ...

            def get_source_files(self):
                return ['.myfile~']

        dist.cmdclass.update(build_custom=build_custom)

        cmd = sdist(dist)
        cmd.use_defaults = True
        cmd.ensure_finalized()
        with quiet():
            cmd.run()
        manifest = cmd.filelist.files
        assert '.myfile~' in manifest


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
    (ep,) = metadata.EntryPoints._from_text(
        """
        [setuptools.file_finders]
        svn_cvs = setuptools.command.sdist:_default_revctrl
        """
    )
    res = ep.load()
    assert hasattr(res, '__iter__')
