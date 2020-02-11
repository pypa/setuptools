import os
import subprocess
import sys
import re


def remove_setuptools():
    """
    Remove setuptools from the current environment.
    """
    print("Removing setuptools")
    cmd = [sys.executable, '-m', 'pip', 'uninstall', '-y', 'setuptools']
    # set cwd to something other than '.' to avoid detecting
    # '.' as the installed package.
    subprocess.check_call(cmd, cwd='.tox')


def bootstrap():
    print("Running bootstrap")
    cmd = [sys.executable, '-m', 'bootstrap']
    subprocess.check_call(cmd)


def is_install_self(args):
    """
    Do the args represent an install of .?
    """
    def strip_extras(arg):
        match = re.match(r'(.*)?\[.*\]$', arg)
        return match.group(1) if match else arg

    return (
        'install' in args
        and any(
            arg in ['.', os.getcwd()]
            for arg in map(strip_extras, args)
        )
    )


def pip(*args):
    cmd = [sys.executable, '-m', 'pip'] + list(args)
    return subprocess.check_call(cmd)


def test_dependencies():
    from ConfigParser import ConfigParser

    def clean(dep):
        spec, _, _ = dep.partition('#')
        return spec.strip()

    parser = ConfigParser()
    parser.read('setup.cfg')
    raw = parser.get('options.extras_require', 'tests').split('\n')
    return filter(None, map(clean, raw))


def disable_python_requires():
    """
    On Python 2, install the dependencies that are selective
    on Python version while honoring REQUIRES_PYTHON, then
    disable REQUIRES_PYTHON so that pip can install this
    checkout of setuptools.
    """
    pip('install', *test_dependencies())
    os.environ['PIP_IGNORE_REQUIRES_PYTHON'] = 'true'


def run(args):
    os.environ['PIP_USE_PEP517'] = 'true'

    if is_install_self(args):
        remove_setuptools()
        bootstrap()
        sys.version_info > (3,) or disable_python_requires()

    pip(*args)


if __name__ == '__main__':
    run(sys.argv[1:])
