import mock
from distutils import log
import os

import pytest

from setuptools.command.test import test
from setuptools.dist import Distribution
from setuptools.tests import ack_2to3

from .textwrap import DALS


SETUP_PY = DALS("""
    from setuptools import setup

    setup(name='foo',
        packages=['name', 'name.space', 'name.space.tests'],
        namespace_packages=['name'],
        test_suite='name.space.tests.test_suite',
    )
    """)

NS_INIT = DALS("""
    # -*- coding: Latin-1 -*-
    # Söme Arbiträry Ünicode to test Distribute Issüé 310
    try:
        __import__('pkg_resources').declare_namespace(__name__)
    except ImportError:
        from pkgutil import extend_path
        __path__ = extend_path(__path__, __name__)
    """)

TEST_PY = DALS("""
    import unittest

    class TestTest(unittest.TestCase):
        def test_test(self):
            print "Foo" # Should fail under Python 3 unless 2to3 is used

    test_suite = unittest.makeSuite(TestTest)
    """)


@pytest.fixture
def sample_test(tmpdir_cwd):
    os.makedirs('name/space/tests')

    # setup.py
    with open('setup.py', 'wt') as f:
        f.write(SETUP_PY)

    # name/__init__.py
    with open('name/__init__.py', 'wb') as f:
        f.write(NS_INIT.encode('Latin-1'))

    # name/space/__init__.py
    with open('name/space/__init__.py', 'wt') as f:
        f.write('#empty\n')

    # name/space/tests/__init__.py
    with open('name/space/tests/__init__.py', 'wt') as f:
        f.write(TEST_PY)


@pytest.fixture
def quiet_log():
    # Running some of the other tests will automatically
    # change the log level to info, messing our output.
    log.set_verbosity(0)


@pytest.mark.usefixtures('sample_test', 'quiet_log')
@ack_2to3
def test_test(capfd):
    params = dict(
        name='foo',
        packages=['name', 'name.space', 'name.space.tests'],
        namespace_packages=['name'],
        test_suite='name.space.tests.test_suite',
        use_2to3=True,
    )
    dist = Distribution(params)
    dist.script_name = 'setup.py'
    cmd = test(dist)
    cmd.ensure_finalized()
    cmd.run()
    out, err = capfd.readouterr()
    assert out == 'Foo\n'


@pytest.mark.usefixtures('tmpdir_cwd', 'quiet_log')
def test_tests_are_run_once(capfd):
    params = dict(
        name='foo',
        packages=['dummy'],
    )
    with open('setup.py', 'wt') as f:
        f.write('from setuptools import setup; setup(\n')
        for k, v in sorted(params.items()):
            f.write('    %s=%r,\n' % (k, v))
        f.write(')\n')
    os.makedirs('dummy')
    with open('dummy/__init__.py', 'wt'):
        pass
    with open('dummy/test_dummy.py', 'wt') as f:
        f.write(DALS(
            """
            import unittest
            class TestTest(unittest.TestCase):
                def test_test(self):
                    print('Foo')
             """))
    dist = Distribution(params)
    dist.script_name = 'setup.py'
    cmd = test(dist)
    cmd.ensure_finalized()
    cmd.run()
    out, err = capfd.readouterr()
    assert out == 'Foo\n'


@pytest.mark.usefixtures('sample_test')
@ack_2to3
def test_warns_deprecation(capfd):
    params = dict(
        name='foo',
        packages=['name', 'name.space', 'name.space.tests'],
        namespace_packages=['name'],
        test_suite='name.space.tests.test_suite',
        use_2to3=True
    )
    dist = Distribution(params)
    dist.script_name = 'setup.py'
    cmd = test(dist)
    cmd.ensure_finalized()
    cmd.announce = mock.Mock()
    cmd.run()
    capfd.readouterr()
    msg = (
        "WARNING: Testing via this command is deprecated and will be "
        "removed in a future version. Users looking for a generic test "
        "entry point independent of test runner are encouraged to use "
        "tox."
    )
    cmd.announce.assert_any_call(msg, log.WARN)


@pytest.mark.usefixtures('sample_test')
@ack_2to3
def test_deprecation_stderr(capfd):
    params = dict(
        name='foo',
        packages=['name', 'name.space', 'name.space.tests'],
        namespace_packages=['name'],
        test_suite='name.space.tests.test_suite',
        use_2to3=True
    )
    dist = Distribution(params)
    dist.script_name = 'setup.py'
    cmd = test(dist)
    cmd.ensure_finalized()
    cmd.run()
    out, err = capfd.readouterr()
    msg = (
        "WARNING: Testing via this command is deprecated and will be "
        "removed in a future version. Users looking for a generic test "
        "entry point independent of test runner are encouraged to use "
        "tox.\n"
    )
    assert msg in err
