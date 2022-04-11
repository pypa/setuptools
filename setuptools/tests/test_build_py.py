import os
import stat
import shutil

import pytest
import jaraco.path
from path import Path

from setuptools.dist import Distribution

from .textwrap import DALS


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
    ))
    os.makedirs('pkg')
    open('pkg/__init__.py', 'w').close()
    open('pkg/run-me', 'w').close()
    os.chmod('pkg/run-me', 0o700)

    dist.parse_command_line()
    dist.run_commands()

    assert os.stat('build/lib/pkg/run-me').st_mode & stat.S_IEXEC, \
        "Script is not executable"


def test_excluded_subpacakges(tmp_path):
    files = {
        "setup.cfg": DALS("""
            [metadata]
            name = mypkg
            version = 42

            [options]
            include_package_data = True
            packages = find:

            [options.packages.find]
            exclude = *.tests*
            """),
        "mypkg": {
            "__init__.py": "",
            "resource_file.txt": "",
            "tests": {
                "__init__.py": "",
                "test_mypkg.py": "",
                "test_file.txt": "",
            }
        },
        "MANIFEST.in": DALS("""
            global-include *.py *.txt
            global-exclude *.py[cod]
            prune dist
            prune build
            prune *.egg-info
            """)
    }

    with Path(tmp_path):
        jaraco.path.build(files)
        dist = Distribution({"script_name": "%PEP 517%"})
        dist.parse_config_files()
        dist.run_command("build_py")
        build_dir = Path(dist.get_command_obj("build_py").build_lib)

        assert (build_dir / "mypkg/__init__.py").exists()
        assert (build_dir / "mypkg/resource_file.txt").exists()
        assert not (build_dir / "mypkg/tests/__init__.py").exists()
        assert not (build_dir / "mypkg/tests/test_mypkg.py").exists()
        assert not (build_dir / "mypkg/tests/test_file.txt").exists()
        assert not (build_dir / "mypkg/tests").exists()
