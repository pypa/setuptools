#!/usr/bin/env python
import sys

if sys.version_info[0] >= 3:
    raise NotImplementedError('Py3 not supported in this test yet')

import os
import shutil
import tempfile
from distutils.command.install import INSTALL_SCHEMES
from string import Template
from urllib2 import urlopen

try:
    import subprocess
    def _system_call(*args):
        assert subprocess.call(args) == 0
except ImportError:
    # Python 2.3
    def _system_call(*args):
        # quoting arguments if windows
        if sys.platform == 'win32':
            def quote(arg):
                if ' ' in arg:
                    return '"%s"' % arg
                return arg
            args = [quote(arg) for arg in args]
        assert os.system(' '.join(args)) == 0

def tempdir(func):
    def _tempdir(*args, **kwargs):
        test_dir = tempfile.mkdtemp()
        old_dir = os.getcwd()
        os.chdir(test_dir)
        try:
            return func(*args, **kwargs)
        finally:
            os.chdir(old_dir)
            shutil.rmtree(test_dir)
    return _tempdir

SIMPLE_BUILDOUT = """\
[buildout]

parts = eggs

[eggs]
recipe = zc.recipe.egg

eggs =
    extensions
"""

BOOTSTRAP = 'http://python-distribute.org/bootstrap.py'
PYVER = sys.version.split()[0][:3]
DEV_URL = 'http://bitbucket.org/tarek/distribute/get/0.6-maintenance.zip#egg=distribute-dev'

_VARS = {'base': '.',
         'py_version_short': PYVER}

if sys.platform == 'win32':
    PURELIB = INSTALL_SCHEMES['nt']['purelib']
else:
    PURELIB = INSTALL_SCHEMES['unix_prefix']['purelib']


@tempdir
def test_virtualenv():
    """virtualenv with distribute"""
    purelib = os.path.abspath(Template(PURELIB).substitute(**_VARS))
    _system_call('virtualenv', '--no-site-packages', '.', '--distribute')
    _system_call('bin/easy_install', 'distribute==dev')
    # linux specific
    site_pkg = os.listdir(purelib)
    site_pkg.sort()
    assert 'distribute' in site_pkg[0]
    easy_install = os.path.join(purelib, 'easy-install.pth')
    with open(easy_install) as f:
        res = f.read()
    assert 'distribute' in res
    assert 'setuptools' not in res

@tempdir
def test_full():
    """virtualenv + pip + buildout"""
    _system_call('virtualenv', '--no-site-packages', '.')
    _system_call('bin/easy_install', '-q', 'distribute==dev')
    _system_call('bin/easy_install', '-qU', 'distribute==dev')
    _system_call('bin/easy_install', '-q', 'pip')
    _system_call('bin/pip', 'install', '-q', 'zc.buildout')

    with open('buildout.cfg', 'w') as f:
        f.write(SIMPLE_BUILDOUT)

    with open('bootstrap.py', 'w') as f:
        f.write(urlopen(BOOTSTRAP).read())

    _system_call('bin/python', 'bootstrap.py', '--distribute')
    _system_call('bin/buildout', '-q')
    eggs = os.listdir('eggs')
    eggs.sort()
    assert len(eggs) == 3
    assert eggs[0].startswith('distribute')
    assert eggs[1:] == ['extensions-0.3-py2.6.egg',
                        'zc.recipe.egg-1.2.2-py2.6.egg']

if __name__ == '__main__':
    test_virtualenv()
    test_full()

