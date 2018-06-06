pytest_plugins = 'setuptools.tests.fixtures'


def pytest_addoption(parser):
    parser.addoption(
        "--package_name", action="append", default=[],
        help="list of package_name to pass to test functions",
    )


collect_ignore = [
    'setuptools/lib2to3_ex.py',
    'tests/manual_test.py',
    'tests/test_pypi.py',
    'pavement.py',
    'setuptools/tests/mod_with_constant.py',
]
