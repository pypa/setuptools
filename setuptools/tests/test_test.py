# -*- coding: UTF-8 -*-

"""develop tests
"""
import os
import site
import sys

import pytest

from setuptools.compat import StringIO, PY2
from setuptools.command.test import test
from setuptools.dist import Distribution

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
    # Söme Arbiträry Ünicode to test Issüé 310
    try:
        __import__('pkg_resources').declare_namespace(__name__)
    except ImportError:
        from pkgutil import extend_path
        __path__ = extend_path(__path__, __name__)
    """)

# Make sure this is Latin-1 binary, before writing:
if PY2:
    NS_INIT = NS_INIT.decode('UTF-8')
NS_INIT = NS_INIT.encode('Latin-1')

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
        f.write(NS_INIT)

    # name/space/__init__.py
    with open('name/space/__init__.py', 'wt') as f:
        f.write('#empty\n')

    # name/space/tests/__init__.py
    with open('name/space/tests/__init__.py', 'wt') as f:
        f.write(TEST_PY)


@pytest.mark.skipif('hasattr(sys, "real_prefix")')
@pytest.mark.usefixtures('user_override')
@pytest.mark.usefixtures('sample_test')
class TestTestTest:

    def test_test(self):
        dist = Distribution(dict(
            name='foo',
            packages=['name', 'name.space', 'name.space.tests'],
            namespace_packages=['name'],
            test_suite='name.space.tests.test_suite',
            use_2to3=True,
            ))
        dist.script_name = 'setup.py'
        cmd = test(dist)
        cmd.user = 1
        cmd.ensure_finalized()
        cmd.install_dir = site.USER_SITE
        cmd.user = 1
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            try: # try/except/finally doesn't work in Python 2.4, so we need nested try-statements.
                cmd.run()
            except SystemExit: # The test runner calls sys.exit, stop that making an error.
                pass
        finally:
            sys.stdout = old_stdout

