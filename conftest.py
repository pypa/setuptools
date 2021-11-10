import sys
import warnings


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
    'setuptools/extern',
    'pkg_resources/extern',
    'pkg_resources/tests/data',
    'setuptools/_vendor',
    'pkg_resources/_vendor',
]


if sys.version_info < (3, 6):
    collect_ignore.append('docs/conf.py')  # uses f-strings
    collect_ignore.append('pavement.py')


if sys.version_info > (3, 10):
    # https://github.com/pypa/setuptools/pull/2865#issuecomment-965700112
    warnings.filterwarnings(
        'ignore',
        'The distutils.sysconfig module is deprecated, use sysconfig instead',
    )


is_pypy = '__pypy__' in sys.builtin_module_names
if is_pypy:
    # Workaround for pypa/setuptools#2868
    warnings.filterwarnings(
        'ignore',
        'Distutils was imported before setuptools',
    )
    warnings.filterwarnings(
        'ignore',
        'Setuptools is replacing distutils',
    )
