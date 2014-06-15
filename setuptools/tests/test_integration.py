"""Run some integration tests.

Try to install a few packages.
"""

import glob
import os
import shutil
import site
import sys
import tempfile

import pytest

from setuptools.command.easy_install import easy_install
from setuptools.command import easy_install as easy_install_pkg
from setuptools.dist import Distribution


@pytest.fixture
def install_context(request):
    """Fixture to set up temporary installation directory.
    """
    # Save old values so we can restore them.
    new_cwd = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    old_enable_site = site.ENABLE_USER_SITE
    old_file = easy_install_pkg.__file__
    old_base = site.USER_BASE
    old_site = site.USER_SITE
    old_ppath = os.environ.get('PYTHONPATH')

    def fin():
        os.chdir(old_cwd)
        shutil.rmtree(new_cwd)
        shutil.rmtree(site.USER_BASE)
        shutil.rmtree(site.USER_SITE)
        site.USER_BASE = old_base
        site.USER_SITE = old_site
        site.ENABLE_USER_SITE = old_enable_site
        easy_install_pkg.__file__ = old_file
        os.environ['PYTHONPATH'] = old_ppath or ''
    request.addfinalizer(fin)

    # Change the environment and site settings to control where the
    # files are installed and ensure we do not overwrite anything.
    site.USER_BASE = tempfile.mkdtemp()
    site.USER_SITE = tempfile.mkdtemp()
    easy_install_pkg.__file__ = site.USER_SITE
    os.chdir(new_cwd)
    install_dir = tempfile.mkdtemp()
    sys.path.append(install_dir)
    os.environ['PYTHONPATH'] = os.path.pathsep.join(sys.path)

    # Set up the command for performing the installation.
    dist = Distribution()
    cmd = easy_install(dist)
    cmd.install_dir = install_dir
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

def test_virtualenvwrapper(install_context):
    _install_one('virtualenvwrapper', install_context,
                 'virtualenvwrapper', 'hook_loader.py')

def test_pbr(install_context):
    _install_one('pbr', install_context,
                 'pbr', 'core.py')

def test_python_novaclient(install_context):
    _install_one('python-novaclient', install_context,
                 'novaclient', 'base.py')
