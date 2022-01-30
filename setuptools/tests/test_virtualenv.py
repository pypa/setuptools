import os
import sys
import itertools
import subprocess

import pathlib

import pytest

from . import contexts
from .textwrap import DALS
from .test_easy_install import make_nspkg_sdist


@pytest.fixture(autouse=True)
def pytest_virtualenv_works(venv):
    """
    pytest_virtualenv may not work. if it doesn't, skip these
    tests. See #1284.
    """
    venv_prefix = venv.run(["python" , "-c", "import sys; print(sys.prefix)"]).strip()
    if venv_prefix == sys.prefix:
        pytest.skip("virtualenv is broken (see pypa/setuptools#1284)")


def test_clean_env_install(venv_without_setuptools, setuptools_wheel):
    """
    Check setuptools can be installed in a clean environment.
    """
    cmd = ["python", "-m", "pip", "install", str(setuptools_wheel)]
    venv_without_setuptools.run(cmd)


def _get_pip_versions():
    # This fixture will attempt to detect if tests are being run without
    # network connectivity and if so skip some tests

    network = True
    if not os.environ.get('NETWORK_REQUIRED', False):  # pragma: nocover
        try:
            from urllib.request import urlopen
            from urllib.error import URLError
        except ImportError:
            from urllib2 import urlopen, URLError  # Python 2.7 compat

        try:
            urlopen('https://pypi.org', timeout=1)
        except URLError:
            # No network, disable most of these tests
            network = False

    def mark(param, *marks):
        if not isinstance(param, type(pytest.param(''))):
            param = pytest.param(param)
        return param._replace(marks=param.marks + marks)

    def skip_network(param):
        return param if network else mark(param, pytest.mark.skip(reason="no network"))

    network_versions = [
        mark('pip<20', pytest.mark.xfail(reason='pypa/pip#6599')),
        'pip<20.1',
        'pip<21',
        'pip<22',
        mark(
            'https://github.com/pypa/pip/archive/main.zip',
            pytest.mark.xfail(reason='#2975'),
        ),
    ]

    versions = itertools.chain(
        [None],
        map(skip_network, network_versions)
    )

    return list(versions)


@pytest.mark.skipif(
    'platform.python_implementation() == "PyPy"',
    reason="https://github.com/pypa/setuptools/pull/2865#issuecomment-965834995",
)
@pytest.mark.parametrize('pip_version', _get_pip_versions())
def test_pip_upgrade_from_source(pip_version, venv_without_setuptools,
                                 setuptools_wheel, setuptools_sdist):
    """
    Check pip can upgrade setuptools from source.
    """
    # Install pip/wheel, in a venv without setuptools (as it
    # should not be needed for bootstraping from source)
    venv = venv_without_setuptools
    venv.run(["pip", "install", "-U", "wheel"])
    if pip_version is not None:
        venv.run(["python", "-m", "pip", "install", "-U", pip_version, "--retries=1"])
    with pytest.raises(subprocess.CalledProcessError):
        # Meta-test to make sure setuptools is not installed
        venv.run(["python", "-c", "import setuptools"])

    # Then install from wheel.
    venv.run(["pip", "install", str(setuptools_wheel)])
    # And finally try to upgrade from source.
    venv.run(["pip", "install", "--no-cache-dir", "--upgrade", str(setuptools_sdist)])


def _check_test_command_install_requirements(venv, tmpdir):
    """
    Check the test command will install all required dependencies.
    """
    def sdist(distname, version):
        dist_path = tmpdir.join('%s-%s.tar.gz' % (distname, version))
        make_nspkg_sdist(str(dist_path), distname, version)
        return dist_path
    dependency_links = [
        pathlib.Path(str(dist_path)).as_uri()
        for dist_path in (
            sdist('foobar', '2.4'),
            sdist('bits', '4.2'),
            sdist('bobs', '6.0'),
            sdist('pieces', '0.6'),
        )
    ]
    with tmpdir.join('setup.py').open('w') as fp:
        fp.write(DALS(
            '''
            from setuptools import setup

            setup(
                dependency_links={dependency_links!r},
                install_requires=[
                    'barbazquux1; sys_platform in ""',
                    'foobar==2.4',
                ],
                setup_requires='bits==4.2',
                tests_require="""
                    bobs==6.0
                """,
                extras_require={{
                    'test': ['barbazquux2'],
                    ':"" in sys_platform': 'pieces==0.6',
                    ':python_version > "1"': """
                        pieces
                        foobar
                    """,
                }}
            )
            '''.format(dependency_links=dependency_links)))
    with tmpdir.join('test.py').open('w') as fp:
        fp.write(DALS(
            '''
            import foobar
            import bits
            import bobs
            import pieces

            open('success', 'w').close()
            '''))

    cmd = ["python", 'setup.py', 'test', '-s', 'test']
    venv.run(cmd, cwd=str(tmpdir))
    assert tmpdir.join('success').check()


def test_test_command_install_requirements(venv, tmpdir, tmpdir_cwd):
    # Ensure pip/wheel packages are installed.
    venv.run(["python", "-c", "__import__('pkg_resources').require(['pip', 'wheel'])"])
    # disable index URL so bits and bobs aren't requested from PyPI
    with contexts.environment(PYTHONPATH=None, PIP_NO_INDEX="1"):
        _check_test_command_install_requirements(venv, tmpdir)


def test_no_missing_dependencies(bare_venv, request):
    """
    Quick and dirty test to ensure all external dependencies are vendored.
    """
    setuptools_dir = request.config.rootdir
    for command in ('upload',):  # sorted(distutils.command.__all__):
        bare_venv.run(['python', 'setup.py', command, '-h'], cwd=setuptools_dir)
