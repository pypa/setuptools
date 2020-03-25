import os
import stat
import shutil

import pytest

from setuptools.dist import Distribution


def test_directories_in_package_data_glob(tmpdir_cwd):
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


def test_read_only(tmpdir_cwd):
    """
    Ensure read-only flag is not preserved in copy
    for package modules and package data, as that
    causes problems with deleting read-only files on
    Windows.

    #1451
    """
    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['build_py'],
        packages=['pkg'],
        package_data={'pkg': ['data.dat']},
        name='pkg',
    ))
    os.makedirs('pkg')
    open('pkg/__init__.py', 'w').close()
    open('pkg/data.dat', 'w').close()
    os.chmod('pkg/__init__.py', stat.S_IREAD)
    os.chmod('pkg/data.dat', stat.S_IREAD)
    dist.parse_command_line()
    dist.run_commands()
    shutil.rmtree('build')


@pytest.mark.xfail(
    'platform.system() == "Windows"',
    reason="On Windows, files do not have executable bits",
    raises=AssertionError,
    strict=True,
)
def test_executable_data(tmpdir_cwd):
    """
    Ensure executable bit is preserved in copy for
    package data, as users rely on it for scripts.

    #2041
    """
    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['build_py'],
        packages=['pkg'],
        package_data={'pkg': ['run-me']},
        name='pkg',
    ))
    os.makedirs('pkg')
    open('pkg/__init__.py', 'w').close()
    open('pkg/run-me', 'w').close()
    os.chmod('pkg/run-me', 0o700)

    dist.parse_command_line()
    dist.run_commands()

    assert os.stat('build/lib/pkg/run-me').st_mode & stat.S_IEXEC, \
        "Script is not executable"
