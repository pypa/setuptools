"""Run some integration tests.

Try to install a few packages.
"""

import glob
import os
import sys
import re
import subprocess
import functools
import tarfile
import zipfile

from setuptools.extern.six.moves import urllib
import pytest

from setuptools.command.easy_install import easy_install
from setuptools.command import easy_install as easy_install_pkg
from setuptools.dist import Distribution


def setup_module(module):
    packages = 'stevedore', 'virtualenvwrapper', 'pbr', 'novaclient'
    for pkg in packages:
        try:
            __import__(pkg)
            tmpl = "Integration tests cannot run when {pkg} is installed"
            pytest.skip(tmpl.format(**locals()))
        except ImportError:
            pass

    try:
        urllib.request.urlopen('https://pypi.python.org/pypi')
    except Exception as exc:
        pytest.skip(str(exc))


@pytest.fixture
def install_context(request, tmpdir, monkeypatch):
    """Fixture to set up temporary installation directory.
    """
    # Save old values so we can restore them.
    new_cwd = tmpdir.mkdir('cwd')
    user_base = tmpdir.mkdir('user_base')
    user_site = tmpdir.mkdir('user_site')
    install_dir = tmpdir.mkdir('install_dir')

    def fin():
        # undo the monkeypatch, particularly needed under
        # windows because of kept handle on cwd
        monkeypatch.undo()
        new_cwd.remove()
        user_base.remove()
        user_site.remove()
        install_dir.remove()

    request.addfinalizer(fin)

    # Change the environment and site settings to control where the
    # files are installed and ensure we do not overwrite anything.
    monkeypatch.chdir(new_cwd)
    monkeypatch.setattr(easy_install_pkg, '__file__', user_site.strpath)
    monkeypatch.setattr('site.USER_BASE', user_base.strpath)
    monkeypatch.setattr('site.USER_SITE', user_site.strpath)
    monkeypatch.setattr('sys.path', sys.path + [install_dir.strpath])
    monkeypatch.setenv(str('PYTHONPATH'), str(os.path.pathsep.join(sys.path)))

    # Set up the command for performing the installation.
    dist = Distribution()
    cmd = easy_install(dist)
    cmd.install_dir = install_dir.strpath
    return cmd


def _install_one(requirement, cmd, pkgname, modulename):
    cmd.args = [requirement]
    cmd.ensure_finalized()
    cmd.run()
    target = cmd.install_dir
    dest_path = glob.glob(os.path.join(target, pkgname + '*.egg'))
    assert dest_path
    assert os.path.exists(os.path.join(dest_path[0], pkgname, modulename))


def test_stevedore(install_context):
    _install_one('stevedore', install_context,
                 'stevedore', 'extension.py')


@pytest.mark.xfail
def test_virtualenvwrapper(install_context):
    _install_one('virtualenvwrapper', install_context,
                 'virtualenvwrapper', 'hook_loader.py')


def test_pbr(install_context):
    _install_one('pbr', install_context,
                 'pbr', 'core.py')


@pytest.mark.xfail
def test_python_novaclient(install_context):
    _install_one('python-novaclient', install_context,
                 'novaclient', 'base.py')


def test_pyuri(install_context):
    """
    Install the pyuri package (version 0.3.1 at the time of writing).

    This is also a regression test for issue #1016.
    """
    _install_one('pyuri', install_context, 'pyuri', 'uri.py')

    pyuri = install_context.installed_projects['pyuri']

    # The package data should be installed.
    assert os.path.exists(os.path.join(pyuri.location, 'pyuri', 'uri.regex'))


build_deps = ['appdirs', 'packaging', 'pyparsing', 'six']


@pytest.mark.parametrize("build_dep", build_deps)
@pytest.mark.skipif(
    sys.version_info < (3, 6), reason='run only on late versions')
def test_build_deps_on_distutils(request, tmpdir_factory, build_dep):
    """
    All setuptools build dependencies must build without
    setuptools.
    """
    if 'pyparsing' in build_dep:
        pytest.xfail(reason="Project imports setuptools unconditionally")
    build_target = tmpdir_factory.mktemp('source')
    build_dir = download_and_extract(request, build_dep, build_target)
    install_target = tmpdir_factory.mktemp('target')
    output = install(build_dir, install_target)
    for line in output.splitlines():
        match = re.search('Unknown distribution option: (.*)', line)
        allowed_unknowns = [
            'test_suite',
            'tests_require',
            'python_requires',
            'install_requires',
            'long_description_content_type',
        ]
        assert not match or match.group(1).strip('"\'') in allowed_unknowns


def install(pkg_dir, install_dir):
    with open(os.path.join(pkg_dir, 'setuptools.py'), 'w') as breaker:
        breaker.write('raise ImportError()')
    cmd = [sys.executable, 'setup.py', 'install', '--prefix', str(install_dir)]
    env = dict(os.environ, PYTHONPATH=str(pkg_dir))
    output = subprocess.check_output(
        cmd, cwd=pkg_dir, env=env, stderr=subprocess.STDOUT)
    return output.decode('utf-8')


def download_and_extract(request, req, target):
    cmd = [
        sys.executable, '-m', 'pip', 'download', '--no-deps',
        '--no-binary', ':all:', req,
    ]
    output = subprocess.check_output(cmd, encoding='utf-8')
    filename = re.search('Saved (.*)', output).group(1)
    request.addfinalizer(functools.partial(os.remove, filename))
    opener = zipfile.ZipFile if filename.endswith('.zip') else tarfile.open
    with opener(filename) as archive:
        archive.extractall(target)
    return os.path.join(target, os.listdir(target)[0])
