import os
import stat
import shutil

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
    Ensure mode is not preserved in copy for package modules
    and package data, as that causes problems
    with deleting read-only files on Windows.

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
