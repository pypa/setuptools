import os
import subprocess
import sys


def remove_setuptools():
    """
    Remove setuptools from the current environment.
    """
    print("Removing setuptools")
    cmd = [sys.executable, '-m', 'pip', 'uninstall', '-y', 'setuptools']
    # set cwd to something other than '.' to avoid detecting
    # '.' as the installed package.
    subprocess.check_call(cmd, cwd='.tox')


def pip(args):
    # Honor requires-python when installing test suite dependencies
    if any('-r' in arg for arg in args):
        os.environ['PIP_IGNORE_REQUIRES_PYTHON'] = '0'

    # When installing '.', remove setuptools
    '.' in args and remove_setuptools()

    cmd = [sys.executable, '-m', 'pip'] + args
    subprocess.check_call(cmd)


if __name__ == '__main__':
    pip(sys.argv[1:])
