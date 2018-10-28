import sys
import pytest
from path import Path
import os


pytest_plugins = 'setuptools.tests.fixtures'


def pytest_addoption(parser):
    parser.addoption(
        "--package_name", action="append", default=[],
        help="list of package_name to pass to test functions",
    )
    parser.addoption(
        "--keep-tmpdir", action="store_true",
        default=False, help="keep temporary test directories"
    )


collect_ignore = [
    'tests/manual_test.py',
    'setuptools/tests/mod_with_constant.py',
]


if sys.version_info < (3,):
    collect_ignore.append('setuptools/lib2to3_ex.py')


if sys.version_info < (3, 6):
    collect_ignore.append('pavement.py')


@pytest.yield_fixture
def global_tmpdir(request, tmpdir):
    """
    Return a temporary directory path object which is unique to each test
    function invocation, created as a sub directory of the base temporary
    directory. The returned object is a ``tests.lib.path.Path`` object.

    This uses the built-in tmpdir fixture from pytest itself but modified
    to return our typical path object instead of py.path.local as well as
    deleting the temporary directories at the end of each test case.
    """
    assert tmpdir.isdir()
    yield Path(str(tmpdir))
    # Clear out the temporary directory after the test has finished using it.
    # This should prevent us from needing a multiple gigabyte temporary
    # directory while running the tests.
    if not request.config.getoption("--keep-tmpdir"):
        tmpdir.remove(ignore_errors=True)


@pytest.fixture(autouse=True)
def isolate(global_tmpdir):
    """
    Isolate our tests so that things like global configuration files and the
    like do not affect our test results.

    We use an autouse function scoped fixture because we want to ensure that
    every test has it's own isolated home directory.
    """

    # TODO: Figure out how to isolate from *system* level configuration files
    #       as well as user level configuration files.

    # Create a directory to use as our home location.
    home_dir = os.path.join(str(global_tmpdir), "home")
    os.makedirs(home_dir)

    # Create a directory to use as a fake root
    fake_root = os.path.join(str(global_tmpdir), "fake-root")
    os.makedirs(fake_root)

    if sys.platform == 'win32':
        # Note: this will only take effect in subprocesses...
        home_drive, home_path = os.path.splitdrive(home_dir)
        os.environ.update({
            'USERPROFILE': home_dir,
            'HOMEDRIVE': home_drive,
            'HOMEPATH': home_path,
        })
        for env_var, sub_path in (
            ('APPDATA', 'AppData/Roaming'),
            ('LOCALAPPDATA', 'AppData/Local'),
        ):
            path = os.path.join(home_dir, *sub_path.split('/'))
            os.environ[env_var] = path
            os.makedirs(path)
    else:
        # Set our home directory to our temporary directory, this should force
        # all of our relative configuration files to be read from here instead
        # of the user's actual $HOME directory.
        os.environ["HOME"] = home_dir
        # Isolate ourselves from XDG directories
        os.environ["XDG_DATA_HOME"] = os.path.join(home_dir, ".local", "share")
        os.environ["XDG_CONFIG_HOME"] = os.path.join(home_dir, ".config")
        os.environ["XDG_CACHE_HOME"] = os.path.join(home_dir, ".cache")
        os.environ["XDG_RUNTIME_DIR"] = os.path.join(home_dir, ".runtime")
        os.environ["XDG_DATA_DIRS"] = ":".join([
            os.path.join(fake_root, "usr", "local", "share"),
            os.path.join(fake_root, "usr", "share"),
        ])
        os.environ["XDG_CONFIG_DIRS"] = os.path.join(fake_root, "etc", "xdg")

    # We want to disable the version check from running in the tests
    os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "true"

    # Make sure tests don't share a requirements tracker.
    os.environ.pop('PIP_REQ_TRACKER', None)
