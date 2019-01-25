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
]


if sys.version_info < (3,):
    collect_ignore.append('setuptools/lib2to3_ex.py')


if sys.version_info < (3, 6):
    collect_ignore.append('pavement.py')
