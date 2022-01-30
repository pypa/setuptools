import pytest
from jaraco import path

from setuptools.command.test import test
from setuptools.dist import Distribution

from .textwrap import DALS


@pytest.mark.usefixtures('tmpdir_cwd')
def test_tests_are_run_once(capfd):
    params = dict(
        packages=['dummy'],
    )
    files = {
        'setup.py':
            'from setuptools import setup; setup('
            + ','.join(f'{name}={params[name]!r}' for name in params)
            + ')',
        'dummy': {
            '__init__.py': '',
            'test_dummy.py': DALS(
                """
                import unittest
                class TestTest(unittest.TestCase):
                    def test_test(self):
                        print('Foo')
                """
                ),
            },
    }
    path.build(files)
    dist = Distribution(params)
    dist.script_name = 'setup.py'
    cmd = test(dist)
    cmd.ensure_finalized()
    cmd.run()
    out, err = capfd.readouterr()
    assert out.endswith('Foo\n')
    assert len(out.split('Foo')) == 2
