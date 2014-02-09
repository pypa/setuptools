"""Tests for the 'setuptools' package"""
import sys
import os
import unittest
from setuptools.tests import doctest
import distutils.core
import distutils.cmd
from distutils.errors import DistutilsOptionError, DistutilsPlatformError
from distutils.errors import DistutilsSetupError
from distutils.core import Extension
from distutils.version import LooseVersion
from setuptools.compat import func_code

from setuptools.compat import func_code
import setuptools.dist
import setuptools.depends as dep
from setuptools.depends import Require

def additional_tests():
    import doctest, unittest
    suite = unittest.TestSuite((
        doctest.DocFileSuite(
            os.path.join('tests', 'api_tests.txt'),
            optionflags=doctest.ELLIPSIS, package='pkg_resources',
            ),
        ))
    if sys.platform == 'win32':
        suite.addTest(doctest.DocFileSuite('win_script_wrapper.txt'))
    return suite

def makeSetup(**args):
    """Return distribution from 'setup(**args)', without executing commands"""

    distutils.core._setup_stop_after = "commandline"

    # Don't let system command line leak into tests!
    args.setdefault('script_args',['install'])

    try:
        return setuptools.setup(**args)
    finally:
        distutils.core._setup_stop_after = None


class DependsTests(unittest.TestCase):

    def testExtractConst(self):
        if not hasattr(dep, 'extract_constant'):
            # skip on non-bytecode platforms
            return

        def f1():
            global x, y, z
            x = "test"
            y = z

        fc = func_code(f1)
        # unrecognized name
        self.assertEqual(dep.extract_constant(fc,'q', -1), None)

        # constant assigned
        self.assertEqual(dep.extract_constant(fc,'x', -1), "test")

        # expression assigned
        self.assertEqual(dep.extract_constant(fc,'y', -1), -1)

        # recognized name, not assigned
        self.assertEqual(dep.extract_constant(fc,'z', -1), None)

    def testFindModule(self):
        self.assertRaises(ImportError, dep.find_module, 'no-such.-thing')
        self.assertRaises(ImportError, dep.find_module, 'setuptools.non-existent')
        f,p,i = dep.find_module('setuptools.tests')
        f.close()

    def testModuleExtract(self):
        if not hasattr(dep, 'get_module_constant'):
            # skip on non-bytecode platforms
            return

        from email import __version__
        self.assertEqual(
            dep.get_module_constant('email','__version__'), __version__
        )
        self.assertEqual(
            dep.get_module_constant('sys','version'), sys.version
        )
        self.assertEqual(
            dep.get_module_constant('setuptools.tests','__doc__'),__doc__
        )

    def testRequire(self):
        if not hasattr(dep, 'extract_constant'):
            # skip on non-bytecode platformsh
            return

        req = Require('Email','1.0.3','email')

        self.assertEqual(req.name, 'Email')
        self.assertEqual(req.module, 'email')
        self.assertEqual(req.requested_version, '1.0.3')
        self.assertEqual(req.attribute, '__version__')
        self.assertEqual(req.full_name(), 'Email-1.0.3')

        from email import __version__
        self.assertEqual(req.get_version(), __version__)
        self.assertTrue(req.version_ok('1.0.9'))
        self.assertTrue(not req.version_ok('0.9.1'))
        self.assertTrue(not req.version_ok('unknown'))

        self.assertTrue(req.is_present())
        self.assertTrue(req.is_current())

        req = Require('Email 3000','03000','email',format=LooseVersion)
        self.assertTrue(req.is_present())
        self.assertTrue(not req.is_current())
        self.assertTrue(not req.version_ok('unknown'))

        req = Require('Do-what-I-mean','1.0','d-w-i-m')
        self.assertTrue(not req.is_present())
        self.assertTrue(not req.is_current())

        req = Require('Tests', None, 'tests', homepage="http://example.com")
        self.assertEqual(req.format, None)
        self.assertEqual(req.attribute, None)
        self.assertEqual(req.requested_version, None)
        self.assertEqual(req.full_name(), 'Tests')
        self.assertEqual(req.homepage, 'http://example.com')

        paths = [os.path.dirname(p) for p in __path__]
        self.assertTrue(req.is_present(paths))
        self.assertTrue(req.is_current(paths))


class DistroTests(unittest.TestCase):

    def setUp(self):
        self.e1 = Extension('bar.ext',['bar.c'])
        self.e2 = Extension('c.y', ['y.c'])

        self.dist = makeSetup(
            packages=['a', 'a.b', 'a.b.c', 'b', 'c'],
            py_modules=['b.d','x'],
            ext_modules = (self.e1, self.e2),
            package_dir = {},
        )

    def testDistroType(self):
        self.assertTrue(isinstance(self.dist,setuptools.dist.Distribution))

    def testExcludePackage(self):
        self.dist.exclude_package('a')
        self.assertEqual(self.dist.packages, ['b','c'])

        self.dist.exclude_package('b')
        self.assertEqual(self.dist.packages, ['c'])
        self.assertEqual(self.dist.py_modules, ['x'])
        self.assertEqual(self.dist.ext_modules, [self.e1, self.e2])

        self.dist.exclude_package('c')
        self.assertEqual(self.dist.packages, [])
        self.assertEqual(self.dist.py_modules, ['x'])
        self.assertEqual(self.dist.ext_modules, [self.e1])

        # test removals from unspecified options
        makeSetup().exclude_package('x')

    def testIncludeExclude(self):
        # remove an extension
        self.dist.exclude(ext_modules=[self.e1])
        self.assertEqual(self.dist.ext_modules, [self.e2])

        # add it back in
        self.dist.include(ext_modules=[self.e1])
        self.assertEqual(self.dist.ext_modules, [self.e2, self.e1])

        # should not add duplicate
        self.dist.include(ext_modules=[self.e1])
        self.assertEqual(self.dist.ext_modules, [self.e2, self.e1])

    def testExcludePackages(self):
        self.dist.exclude(packages=['c','b','a'])
        self.assertEqual(self.dist.packages, [])
        self.assertEqual(self.dist.py_modules, ['x'])
        self.assertEqual(self.dist.ext_modules, [self.e1])

    def testEmpty(self):
        dist = makeSetup()
        dist.include(packages=['a'], py_modules=['b'], ext_modules=[self.e2])
        dist = makeSetup()
        dist.exclude(packages=['a'], py_modules=['b'], ext_modules=[self.e2])

    def testContents(self):
        self.assertTrue(self.dist.has_contents_for('a'))
        self.dist.exclude_package('a')
        self.assertTrue(not self.dist.has_contents_for('a'))

        self.assertTrue(self.dist.has_contents_for('b'))
        self.dist.exclude_package('b')
        self.assertTrue(not self.dist.has_contents_for('b'))

        self.assertTrue(self.dist.has_contents_for('c'))
        self.dist.exclude_package('c')
        self.assertTrue(not self.dist.has_contents_for('c'))

    def testInvalidIncludeExclude(self):
        self.assertRaises(DistutilsSetupError,
            self.dist.include, nonexistent_option='x'
        )
        self.assertRaises(DistutilsSetupError,
            self.dist.exclude, nonexistent_option='x'
        )
        self.assertRaises(DistutilsSetupError,
            self.dist.include, packages={'x':'y'}
        )
        self.assertRaises(DistutilsSetupError,
            self.dist.exclude, packages={'x':'y'}
        )
        self.assertRaises(DistutilsSetupError,
            self.dist.include, ext_modules={'x':'y'}
        )
        self.assertRaises(DistutilsSetupError,
            self.dist.exclude, ext_modules={'x':'y'}
        )

        self.assertRaises(DistutilsSetupError,
            self.dist.include, package_dir=['q']
        )
        self.assertRaises(DistutilsSetupError,
            self.dist.exclude, package_dir=['q']
        )

class TestCommandTests(unittest.TestCase):

    def testTestIsCommand(self):
        test_cmd = makeSetup().get_command_obj('test')
        self.assertTrue(isinstance(test_cmd, distutils.cmd.Command))

    def testLongOptSuiteWNoDefault(self):
        ts1 = makeSetup(script_args=['test','--test-suite=foo.tests.suite'])
        ts1 = ts1.get_command_obj('test')
        ts1.ensure_finalized()
        self.assertEqual(ts1.test_suite, 'foo.tests.suite')

    def testDefaultSuite(self):
        ts2 = makeSetup(test_suite='bar.tests.suite').get_command_obj('test')
        ts2.ensure_finalized()
        self.assertEqual(ts2.test_suite, 'bar.tests.suite')

    def testDefaultWModuleOnCmdLine(self):
        ts3 = makeSetup(
            test_suite='bar.tests',
            script_args=['test','-m','foo.tests']
        ).get_command_obj('test')
        ts3.ensure_finalized()
        self.assertEqual(ts3.test_module, 'foo.tests')
        self.assertEqual(ts3.test_suite,  'foo.tests.test_suite')

    def testConflictingOptions(self):
        ts4 = makeSetup(
            script_args=['test','-m','bar.tests', '-s','foo.tests.suite']
        ).get_command_obj('test')
        self.assertRaises(DistutilsOptionError, ts4.ensure_finalized)

    def testNoSuite(self):
        ts5 = makeSetup().get_command_obj('test')
        ts5.ensure_finalized()
        self.assertEqual(ts5.test_suite, None)
