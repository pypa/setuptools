"""Tests for the 'setuptools' package"""

import sys
import os
import distutils.core
import distutils.cmd
from distutils.errors import DistutilsOptionError
from distutils.errors import DistutilsSetupError
from distutils.core import Extension
from zipfile import ZipFile

import pytest

from setuptools.extern.packaging import version

import setuptools
import setuptools.dist
import setuptools.depends as dep
from setuptools.depends import Require

from . import __name__ as __pkg__


@pytest.fixture(autouse=True)
def isolated_dir(tmpdir_cwd):
    yield


def makeSetup(**args):
    """Return distribution from 'setup(**args)', without executing commands"""

    distutils.core._setup_stop_after = "commandline"

    # Don't let system command line leak into tests!
    args.setdefault('script_args', ['install'])

    try:
        return setuptools.setup(**args)
    finally:
        distutils.core._setup_stop_after = None


needs_bytecode = pytest.mark.skipif(
    not hasattr(dep, 'get_module_constant'),
    reason="bytecode support not available",
)


class TestDepends:
    def testExtractConst(self):
        if not hasattr(dep, 'extract_constant'):
            # skip on non-bytecode platforms
            return

        def f1():
            global x, y, z
            x = "test"
            y = z

        fc = f1.__code__

        # unrecognized name
        assert dep.extract_constant(fc, 'q', -1) is None

        # constant assigned
        dep.extract_constant(fc, 'x', -1) == "test"

        # expression assigned
        dep.extract_constant(fc, 'y', -1) == -1

        # recognized name, not assigned
        dep.extract_constant(fc, 'z', -1) is None

    def testFindModule(self):
        with pytest.raises(ImportError):
            dep.find_module('no-such.-thing')
        with pytest.raises(ImportError):
            dep.find_module('setuptools.non-existent')
        f, p, i = dep.find_module(__pkg__)
        f.close()

    @needs_bytecode
    def testModuleExtract(self):
        from json import __version__
        assert dep.get_module_constant('json', '__version__') == __version__
        assert dep.get_module_constant('sys', 'version') == sys.version
        assert dep.get_module_constant(__name__, '__doc__') == __doc__

    @needs_bytecode
    def testRequire(self):
        req = Require('Json', '1.0.3', 'json')

        assert req.name == 'Json'
        assert req.module == 'json'
        assert req.requested_version == version.Version('1.0.3')
        assert req.attribute == '__version__'
        assert req.full_name() == 'Json-1.0.3'

        from json import __version__
        assert str(req.get_version()) == __version__
        assert req.version_ok('1.0.9')
        assert not req.version_ok('0.9.1')
        assert not req.version_ok('unknown')

        assert req.is_present()
        assert req.is_current()

        req = Require('Do-what-I-mean', '1.0', 'd-w-i-m')
        assert not req.is_present()
        assert not req.is_current()

    @needs_bytecode
    def test_require_present(self, tmp_path):
        # In #1896, this test was failing for months with the only
        # complaint coming from test runners (not end users).
        # TODO: Evaluate if this code is needed at all.
        mod = (tmp_path / "module_under_test.py")
        mod.write_text("hello_world = True")

        req = Require('Tests', None, "module_under_test", homepage="http://example.com")
        assert req.format is None
        assert req.attribute is None
        assert req.requested_version is None
        assert req.full_name() == 'Tests'
        assert req.homepage == 'http://example.com'

        paths = [str(tmp_path)]
        assert req.is_present(paths)
        assert req.is_current(paths)


class TestDistro:
    def setup_method(self, method):
        self.e1 = Extension('bar.ext', ['bar.c'])
        self.e2 = Extension('c.y', ['y.c'])

        self.dist = makeSetup(
            packages=['a', 'a.b', 'a.b.c', 'b', 'c'],
            py_modules=['b.d', 'x'],
            ext_modules=(self.e1, self.e2),
            package_dir={},
        )

    def testDistroType(self):
        assert isinstance(self.dist, setuptools.dist.Distribution)

    def testExcludePackage(self):
        self.dist.exclude_package('a')
        assert self.dist.packages == ['b', 'c']

        self.dist.exclude_package('b')
        assert self.dist.packages == ['c']
        assert self.dist.py_modules == ['x']
        assert self.dist.ext_modules == [self.e1, self.e2]

        self.dist.exclude_package('c')
        assert self.dist.packages == []
        assert self.dist.py_modules == ['x']
        assert self.dist.ext_modules == [self.e1]

        # test removals from unspecified options
        makeSetup().exclude_package('x')

    def testIncludeExclude(self):
        # remove an extension
        self.dist.exclude(ext_modules=[self.e1])
        assert self.dist.ext_modules == [self.e2]

        # add it back in
        self.dist.include(ext_modules=[self.e1])
        assert self.dist.ext_modules == [self.e2, self.e1]

        # should not add duplicate
        self.dist.include(ext_modules=[self.e1])
        assert self.dist.ext_modules == [self.e2, self.e1]

    def testExcludePackages(self):
        self.dist.exclude(packages=['c', 'b', 'a'])
        assert self.dist.packages == []
        assert self.dist.py_modules == ['x']
        assert self.dist.ext_modules == [self.e1]

    def testEmpty(self):
        dist = makeSetup()
        dist.include(packages=['a'], py_modules=['b'], ext_modules=[self.e2])
        dist = makeSetup()
        dist.exclude(packages=['a'], py_modules=['b'], ext_modules=[self.e2])

    def testContents(self):
        assert self.dist.has_contents_for('a')
        self.dist.exclude_package('a')
        assert not self.dist.has_contents_for('a')

        assert self.dist.has_contents_for('b')
        self.dist.exclude_package('b')
        assert not self.dist.has_contents_for('b')

        assert self.dist.has_contents_for('c')
        self.dist.exclude_package('c')
        assert not self.dist.has_contents_for('c')

    def testInvalidIncludeExclude(self):
        with pytest.raises(DistutilsSetupError):
            self.dist.include(nonexistent_option='x')
        with pytest.raises(DistutilsSetupError):
            self.dist.exclude(nonexistent_option='x')
        with pytest.raises(DistutilsSetupError):
            self.dist.include(packages={'x': 'y'})
        with pytest.raises(DistutilsSetupError):
            self.dist.exclude(packages={'x': 'y'})
        with pytest.raises(DistutilsSetupError):
            self.dist.include(ext_modules={'x': 'y'})
        with pytest.raises(DistutilsSetupError):
            self.dist.exclude(ext_modules={'x': 'y'})

        with pytest.raises(DistutilsSetupError):
            self.dist.include(package_dir=['q'])
        with pytest.raises(DistutilsSetupError):
            self.dist.exclude(package_dir=['q'])


class TestCommandTests:
    def testTestIsCommand(self):
        test_cmd = makeSetup().get_command_obj('test')
        assert (isinstance(test_cmd, distutils.cmd.Command))

    def testLongOptSuiteWNoDefault(self):
        ts1 = makeSetup(script_args=['test', '--test-suite=foo.tests.suite'])
        ts1 = ts1.get_command_obj('test')
        ts1.ensure_finalized()
        assert ts1.test_suite == 'foo.tests.suite'

    def testDefaultSuite(self):
        ts2 = makeSetup(test_suite='bar.tests.suite').get_command_obj('test')
        ts2.ensure_finalized()
        assert ts2.test_suite == 'bar.tests.suite'

    def testDefaultWModuleOnCmdLine(self):
        ts3 = makeSetup(
            test_suite='bar.tests',
            script_args=['test', '-m', 'foo.tests']
        ).get_command_obj('test')
        ts3.ensure_finalized()
        assert ts3.test_module == 'foo.tests'
        assert ts3.test_suite == 'foo.tests.test_suite'

    def testConflictingOptions(self):
        ts4 = makeSetup(
            script_args=['test', '-m', 'bar.tests', '-s', 'foo.tests.suite']
        ).get_command_obj('test')
        with pytest.raises(DistutilsOptionError):
            ts4.ensure_finalized()

    def testNoSuite(self):
        ts5 = makeSetup().get_command_obj('test')
        ts5.ensure_finalized()
        assert ts5.test_suite is None


@pytest.fixture
def example_source(tmpdir):
    tmpdir.mkdir('foo')
    (tmpdir / 'foo/bar.py').write('')
    (tmpdir / 'readme.txt').write('')
    return tmpdir


def test_findall(example_source):
    found = list(setuptools.findall(str(example_source)))
    expected = ['readme.txt', 'foo/bar.py']
    expected = [example_source.join(fn) for fn in expected]
    assert found == expected


def test_findall_curdir(example_source):
    with example_source.as_cwd():
        found = list(setuptools.findall())
    expected = ['readme.txt', os.path.join('foo', 'bar.py')]
    assert found == expected


@pytest.fixture
def can_symlink(tmpdir):
    """
    Skip if cannot create a symbolic link
    """
    link_fn = 'link'
    target_fn = 'target'
    try:
        os.symlink(target_fn, link_fn)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("Cannot create symbolic links")
    os.remove(link_fn)


def test_findall_missing_symlink(tmpdir, can_symlink):
    with tmpdir.as_cwd():
        os.symlink('foo', 'bar')
        found = list(setuptools.findall())
        assert found == []


def test_its_own_wheel_does_not_contain_tests(setuptools_wheel):
    with ZipFile(setuptools_wheel) as zipfile:
        contents = [f.replace(os.sep, '/') for f in zipfile.namelist()]

    for member in contents:
        assert '/tests/' not in member
