import os

import pytest

from setuptools.dist import Distribution


@pytest.yield_fixture
def tmpdir_as_cwd(tmpdir):
    with tmpdir.as_cwd():
        yield tmpdir


def test_directories_in_package_data_glob(tmpdir_as_cwd):
    """
    Directories matching the glob in package_data should
    not be included in the package data.

    Regression test for #261.
    """
    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['build_py'],
        packages=[''],
        name='foo',
        package_data={'': ['path/*']},
    ))
    os.makedirs('path/subpath')
    dist.parse_command_line()
    dist.run_commands()
