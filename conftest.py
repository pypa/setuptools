import platform
import sys

import pytest

pytest_plugins = 'setuptools.tests.fixtures'


def pytest_addoption(parser):
    parser.addoption(
        "--package_name",
        action="append",
        default=[],
        help="list of package_name to pass to test functions",
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests (only)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "uses_network: tests may try to download files")
    _IntegrationTestSpeedups.disable_plugins_already_run(config)


collect_ignore = [
    'tests/manual_test.py',
    'setuptools/tests/mod_with_constant.py',
    'setuptools/_distutils',
    '_distutils_hack',
    'pkg_resources/tests/data',
    'setuptools/_vendor',
    'setuptools/config/_validate_pyproject',
    'setuptools/modified.py',
    'setuptools/tests/bdist_wheel_testdata',
]


if sys.version_info < (3, 9) or sys.platform == 'cygwin':
    collect_ignore.append('tools/finalize.py')


@pytest.fixture(autouse=True)
def _skip_integration(request):
    _IntegrationTestSpeedups.conditional_skip(request)


class _IntegrationTestSpeedups:
    """Speed-up integration tests by only running what does not run in other tests."""

    RUNS_ON_NORMAL_TESTS = ("checkdocks", "cov", "mypy", "perf", "ruff")

    @classmethod
    def disable_plugins_already_run(cls, config):
        if config.getoption("--integration"):
            for plugin in cls.RUNS_ON_NORMAL_TESTS:  # no need to run again
                config.pluginmanager.set_blocked(plugin)

    @staticmethod
    def conditional_skip(request):
        running_integration_tests = request.config.getoption("--integration")
        is_integration_test = request.node.get_closest_marker("integration")
        if running_integration_tests and not is_integration_test:
            pytest.skip("running integration tests only")
        if not running_integration_tests and is_integration_test:
            pytest.skip("skipping integration tests")


@pytest.fixture
def windows_only():
    if platform.system() != 'Windows':
        pytest.skip("Windows only")
