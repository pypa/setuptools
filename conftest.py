import os
import sys
from importlib.util import spec_from_file_location

import pytest


class _ImportFinder:
    """Allow in-tree pytest plugins when setuptools is installed from distribution"""

    _root_dir = os.path.dirname(__file__)
    _handled = ('setuptools.tests', 'pkg_resources.tests')

    @classmethod
    def find_spec(cls, fullname, _path, _target=None):
        if all(not fullname.startswith(n) for n in cls._handled):
            return None

        loc = os.path.join(cls._root_dir, *fullname.split("."))
        loc = os.path.join(loc, "__init__.py") if os.path.isdir(loc) else f"{loc}.py"
        return spec_from_file_location(fullname, loc)


sys.meta_path.append(_ImportFinder)
pytest_plugins = ['setuptools.tests.fixtures']


def pytest_addoption(parser):
    parser.addoption(
        "--package_name", action="append", default=[],
        help="list of package_name to pass to test functions",
    )
    parser.addoption(
        "--integration", action="store_true", default=False,
        help="run integration tests (only)"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration tests")


collect_ignore = [
    'tests/manual_test.py',
    'setuptools/tests/mod_with_constant.py',
    'setuptools/_distutils',
    '_distutils_hack',
    'setuptools/extern',
    'pkg_resources/extern',
    'pkg_resources/tests/data',
    'setuptools/_vendor',
    'pkg_resources/_vendor',
]


if sys.version_info < (3, 6):
    collect_ignore.append('docs/conf.py')  # uses f-strings
    collect_ignore.append('pavement.py')


@pytest.fixture(autouse=True)
def _skip_integration(request):
    running_integration_tests = request.config.getoption("--integration")
    is_integration_test = request.node.get_closest_marker("integration")
    if running_integration_tests and not is_integration_test:
        pytest.skip("running integration tests only")
    if not running_integration_tests and is_integration_test:
        pytest.skip("skipping integration tests")
