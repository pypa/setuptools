import glob
import os

from pytest import yield_fixture
from pytest_fixture_config import yield_requires_config

import pytest_virtualenv


@yield_requires_config(pytest_virtualenv.CONFIG, ['virtualenv_executable'])
@yield_fixture(scope='function')
def bare_virtualenv():
    """ Bare virtualenv (no pip/setuptools/wheel).
    """
    with pytest_virtualenv.VirtualEnv(args=(
        '--no-wheel',
        '--no-pip',
        '--no-setuptools',
    )) as venv:
        yield venv


SOURCE_DIR = os.path.join(os.path.dirname(__file__), '../..')

def test_clean_env_install(bare_virtualenv):
    """
    Check setuptools can be installed in a clean environment.
    """
    bare_virtualenv.run(' && '.join((
        'cd {source}',
        'python setup.py install',
    )).format(source=SOURCE_DIR))

def test_pip_upgrade_from_source(virtualenv):
    """
    Check pip can upgrade setuptools from source.
    """
    dist_dir = virtualenv.workspace
    # Generate source distribution / wheel.
    virtualenv.run(' && '.join((
        'cd {source}',
        'python setup.py -q sdist -d {dist}',
        'python setup.py -q bdist_wheel -d {dist}',
    )).format(source=SOURCE_DIR, dist=dist_dir))
    sdist = glob.glob(os.path.join(dist_dir, '*.zip'))[0]
    wheel = glob.glob(os.path.join(dist_dir, '*.whl'))[0]
    # Then update from wheel.
    virtualenv.run('pip install ' + wheel)
    # And finally try to upgrade from source.
    virtualenv.run('pip install --no-cache-dir --upgrade ' + sdist)
