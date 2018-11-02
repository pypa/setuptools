import sys
import pytest
from path import Path


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


@pytest.fixture(autouse=True)
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
