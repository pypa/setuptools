import os
import sys
import functools
import platform
import textwrap

import pytest


IS_PYPY = '__pypy__' in sys.builtin_module_names


def popen_text(call):
    """
    Augment the Popen call with the parameters to ensure unicode text.
    """
    return functools.partial(call, universal_newlines=True) \
        if sys.version_info < (3, 7) else functools.partial(call, text=True)


def win_sr(env):
    """
    On Windows, SYSTEMROOT must be present to avoid

    > Fatal Python error: _Py_HashRandomization_Init: failed to
    > get random numbers to initialize Python
    """
    if env is None:
        return
    if platform.system() == 'Windows':
        env['SYSTEMROOT'] = os.environ['SYSTEMROOT']
    return env


def find_distutils(venv, imports='distutils', env=None, **kwargs):
    py_cmd = 'import {imports}; print(distutils.__file__)'.format(**locals())
    cmd = ['python', '-c', py_cmd]
    return popen_text(venv.run)(cmd, env=win_sr(env), **kwargs)


def count_meta_path(venv, env=None):
    py_cmd = textwrap.dedent(
        """
        import sys
        is_distutils = lambda finder: finder.__class__.__name__ == "DistutilsMetaFinder"
        print(len(list(filter(is_distutils, sys.meta_path))))
        """)
    cmd = ['python', '-c', py_cmd]
    return int(popen_text(venv.run)(cmd, env=win_sr(env)))


def test_distutils_stdlib(venv):
    """
    Ensure stdlib distutils is used when appropriate.
    """
    env = dict(SETUPTOOLS_USE_DISTUTILS='stdlib')
    assert venv.name not in find_distutils(venv, env=env).split(os.sep)
    assert count_meta_path(venv, env=env) == 0


def test_distutils_local_with_setuptools(venv):
    """
    Ensure local distutils is used when appropriate.
    """
    env = dict(SETUPTOOLS_USE_DISTUTILS='local')
    loc = find_distutils(venv, imports='setuptools, distutils', env=env)
    assert venv.name in loc.split(os.sep)
    assert count_meta_path(venv, env=env) <= 1


@pytest.mark.xfail('IS_PYPY', reason='pypy imports distutils on startup')
def test_distutils_local(venv):
    """
    Even without importing, the setuptools-local copy of distutils is
    preferred.
    """
    env = dict(SETUPTOOLS_USE_DISTUTILS='local')
    assert venv.name in find_distutils(venv, env=env).split(os.sep)
    assert count_meta_path(venv, env=env) <= 1


def test_pip_import(venv):
    """
    Ensure pip can be imported.
    Regression test for #3002.
    """
    cmd = ['python', '-c', 'import pip']
    popen_text(venv.run)(cmd)


def test_distutils_has_origin():
    """
    Distutils module spec should have an origin. #2990.
    """
    assert __import__('distutils').__spec__.origin


ENSURE_IMPORTS_ARE_NOT_DUPLICATED = r"""
# Depending on the importlib machinery and _distutils_hack, some imports can be
# duplicated resulting in different module objects being loaded, which prevents
# patches from being applied as shown in #3042.
# This script provides a way of verifying if this duplication is happening.

import distutils.command.sdist as sdist

# import last to prevent caching
from distutils import dir_util, file_util, archive_util

assert sdist.dir_util == dir_util, (
    f"\n{sdist.dir_util}\n!=\n{dir_util}"
)

assert sdist.file_util == file_util, (
    f"\n{sdist.file_util}\n!=\n{file_util}"
)

assert sdist.archive_util == archive_util, (
    f"\n{sdist.archive_util}\n!=\n{archive_util}"
)

print("success")
"""


@pytest.mark.parametrize("distutils_version", ("local", "stdlib"))
def test_modules_are_not_duplicated_on_import(distutils_version, tmpdir_cwd, venv):
    env = dict(SETUPTOOLS_USE_DISTUTILS=distutils_version)
    cmd = ['python', '-c', ENSURE_IMPORTS_ARE_NOT_DUPLICATED]
    output = popen_text(venv.run)(cmd, env=win_sr(env)).strip()
    assert output == "success"


ENSURE_LOG_IMPORT_IS_NOT_DUPLICATED = r"""
# Similar to ENSURE_IMPORTS_ARE_NOT_DUPLICATED
import distutils.dist as dist
from distutils import log

assert dist.log == log, (
    f"\n{dist.log}\n!=\n{log}"
)

print("success")
"""


@pytest.mark.parametrize(
    "distutils_version",
    [
        pytest.param(
            "local",
            marks=pytest.mark.xfail(reason="duplicated distutils.log, #3038 #3042")
        ),
        "stdlib"
    ]
)
def test_log_module_is_not_duplicated_on_import(distutils_version, tmpdir_cwd, venv):
    env = dict(SETUPTOOLS_USE_DISTUTILS=distutils_version)
    cmd = ['python', '-c', ENSURE_LOG_IMPORT_IS_NOT_DUPLICATED]
    output = popen_text(venv.run)(cmd, env=win_sr(env)).strip()
    assert output == "success"
