import os
import pytest


@pytest.fixture
def env(virtualenv):
    virtualenv.run(['pip', 'uninstall', '-y', 'setuptools'])
    virtualenv.run(['pip', 'install', os.getcwd()])
    return virtualenv


def find_distutils(env, imports='distutils'):
    py_cmd = 'import {imports}; print(distutils.__file__)'.format(**locals())
    cmd = ['python', '-c', py_cmd]
    return env.run(cmd, capture=True, text=True)


def test_distutils_stdlib(env):
    """
    Ensure stdlib distutils is used when appropriate.
    """
    assert '.env' not in find_distutils(env).split(os.sep)


def test_distutils_local_with_setuptools(env):
    """
    Ensure local distutils is used when appropriate.
    """
    env.env.update(SETUPTOOLS_USE_DISTUTILS='local')
    loc = find_distutils(env, imports='setuptools, distutils')
    assert '.env' in loc.split(os.sep)


@pytest.mark.xfail(reason="#2259")
def test_distutils_local(env):
    env.env.update(SETUPTOOLS_USE_DISTUTILS='local')
    assert '.env' in find_distutils(env).split(os.sep)
