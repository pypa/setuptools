import sys


pytest_plugins = 'setuptools.tests.fixtures'


def pytest_addoption(parser):
    parser.addoption(
        "--package_name", action="append", default=[],
        help="list of package_name to pass to test functions",
    )


collect_ignore = [
    'tests/manual_test.py',
    'setuptools/tests/mod_with_constant.py',
    'setuptools/_distutils',
    '_distutils_hack',
]


def pytest_configure(config):
    disable_coverage_on_pypy(config)


def disable_coverage_on_pypy(config):
    """
    Coverage makes tests on PyPy unbearably slow, so disable it.
    """
    if '__pypy__' not in sys.builtin_module_names:
        return

    # Recommended at pytest-dev/pytest-cov#418
    cov = config.pluginmanager.get_plugin('_cov')
    cov.options.no_cov = True
    if cov.cov_controller:
        cov.cov_controller.pause()


if sys.version_info < (3,):
    collect_ignore.append('setuptools/lib2to3_ex.py')
    collect_ignore.append('setuptools/_imp.py')


if sys.version_info < (3, 6):
    collect_ignore.append('pavement.py')
