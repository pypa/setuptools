import os


pytest_plugins = 'setuptools.tests.fixtures'


def pytest_addoption(parser):
    parser.addoption(
        "--package_name", action="append", default=[],
        help="list of package_name to pass to test functions",
    )


def pytest_configure():
    _issue_852_workaround()


def _issue_852_workaround():
    """
    Patch 'setuptools.__file__' with an absolute path
    for forward compatibility with Python 3.
    Workaround for https://github.com/pypa/setuptools/issues/852
    """
    setuptools = __import__('setuptools')
    setuptools.__file__ = os.path.abspath(setuptools.__file__)
