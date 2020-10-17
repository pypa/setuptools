import os
import sys
import functools
import subprocess
import platform

import pytest
import jaraco.envs
import path


IS_PYPY = '__pypy__' in sys.builtin_module_names


class VirtualEnv(jaraco.envs.VirtualEnv):
    name = '.env'

    def run(self, cmd, *args, **kwargs):
        cmd = [self.exe(cmd[0])] + cmd[1:]
        return subprocess.check_output(cmd, *args, cwd=self.root, **kwargs)


@pytest.fixture
def venv(tmpdir):
    env = VirtualEnv()
    env.root = path.Path(tmpdir)
    env.req = os.getcwd()
    return env.create()


def popen_text(call):
    """
    Augment the Popen call with the parameters to ensure unicode text.
    """
    return functools.partial(call, universal_newlines=True) \
        if sys.version_info < (3, 7) else functools.partial(call, text=True)


def find_distutils(venv, imports='distutils', env=None, **kwargs):
    py_cmd = 'import {imports}; print(distutils.__file__)'.format(**locals())
    cmd = ['python', '-c', py_cmd]
    if platform.system() == 'Windows':
        env['SYSTEMROOT'] = os.environ['SYSTEMROOT']
    return popen_text(venv.run)(cmd, env=env, **kwargs)


def test_distutils_stdlib(venv):
    """
    Ensure stdlib distutils is used when appropriate.
    """
    env = dict(SETUPTOOLS_USE_DISTUTILS='stdlib')
    assert venv.name not in find_distutils(venv, env=env).split(os.sep)


def test_distutils_local_with_setuptools(venv):
    """
    Ensure local distutils is used when appropriate.
    """
    env = dict(SETUPTOOLS_USE_DISTUTILS='local')
    loc = find_distutils(venv, imports='setuptools, distutils', env=env)
    assert venv.name in loc.split(os.sep)


@pytest.mark.xfail('IS_PYPY', reason='pypy imports distutils on startup')
def test_distutils_local(venv):
    """
    Even without importing, the setuptools-local copy of distutils is
    preferred.
    """
    env = dict(SETUPTOOLS_USE_DISTUTILS='local')
    assert venv.name in find_distutils(venv, env=env).split(os.sep)
