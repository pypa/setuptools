import glob
import os
import sys
import itertools

import pathlib

import pytest
from pytest_fixture_config import yield_requires_config

import pytest_virtualenv

from .textwrap import DALS
from .test_easy_install import make_nspkg_sdist


@pytest.fixture(autouse=True)
def pytest_virtualenv_works(virtualenv):
    """
    pytest_virtualenv may not work. if it doesn't, skip these
    tests. See #1284.
    """
    venv_prefix = virtualenv.run(
        'python -c "import sys; print(sys.prefix)"',
        capture=True,
    ).strip()
    if venv_prefix == sys.prefix:
        pytest.skip("virtualenv is broken (see pypa/setuptools#1284)")


@yield_requires_config(pytest_virtualenv.CONFIG, ['virtualenv_executable'])
@pytest.fixture(scope='function')
def bare_virtualenv():
    """ Bare virtualenv (no pip/setuptools/wheel).
    """
    with pytest_virtualenv.VirtualEnv(args=(
        '--no-wheel',
        '--no-pip',
        '--no-setuptools',
    )) as venv:
        yield venv


def test_clean_env_install(bare_virtualenv, tmp_src):
    """
    Check setuptools can be installed in a clean environment.
    """
    cmd = [bare_virtualenv.python, 'setup.py', 'install']
    bare_virtualenv.run(cmd, cd=tmp_src)


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
            pytest.mark.skipif('sys.version_info < (3, 7)'),
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
def test_pip_upgrade_from_source(pip_version, tmp_src, virtualenv):
    """
    Check pip can upgrade setuptools from source.
    """
    # Install pip/wheel, and remove setuptools (as it
    # should not be needed for bootstraping from source)
    if pip_version is None:
        upgrade_pip = ()
    else:
        upgrade_pip = ('python -m pip install -U "{pip_version}" --retries=1',)
    virtualenv.run(' && '.join((
        'pip uninstall -y setuptools',
        'pip install -U wheel',
    ) + upgrade_pip).format(pip_version=pip_version))
    dist_dir = virtualenv.workspace
    # Generate source distribution / wheel.
    virtualenv.run(' && '.join((
        'python setup.py -q sdist -d {dist}',
        'python setup.py -q bdist_wheel -d {dist}',
    )).format(dist=dist_dir), cd=tmp_src)
    sdist = glob.glob(os.path.join(dist_dir, '*.zip'))[0]
    wheel = glob.glob(os.path.join(dist_dir, '*.whl'))[0]
    # Then update from wheel.
    virtualenv.run('pip install ' + wheel)
    # And finally try to upgrade from source.
    virtualenv.run('pip install --no-cache-dir --upgrade ' + sdist)


def _check_test_command_install_requirements(virtualenv, tmpdir, cwd):
    """
    Check the test command will install all required dependencies.
    """
    # Install setuptools.
    virtualenv.run('python setup.py develop', cd=cwd)

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
    # Run test command for test package.
    # use 'virtualenv.python' as workaround for man-group/pytest-plugins#166
    cmd = [virtualenv.python, 'setup.py', 'test', '-s', 'test']
    virtualenv.run(cmd, cd=str(tmpdir))
    assert tmpdir.join('success').check()


def test_test_command_install_requirements(virtualenv, tmpdir, request):
    # Ensure pip/wheel packages are installed.
    virtualenv.run(
        "python -c \"__import__('pkg_resources').require(['pip', 'wheel'])\"")
    # uninstall setuptools so that 'setup.py develop' works
    virtualenv.run("python -m pip uninstall -y setuptools")
    # disable index URL so bits and bobs aren't requested from PyPI
    virtualenv.env['PIP_NO_INDEX'] = '1'
    _check_test_command_install_requirements(virtualenv, tmpdir, request.config.rootdir)


def test_no_missing_dependencies(bare_virtualenv, request):
    """
    Quick and dirty test to ensure all external dependencies are vendored.
    """
    for command in ('upload',):  # sorted(distutils.command.__all__):
        cmd = [bare_virtualenv.python, 'setup.py', command, '-h']
        bare_virtualenv.run(cmd, cd=request.config.rootdir)
