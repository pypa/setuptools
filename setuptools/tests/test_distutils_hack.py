"""Test that the distutils hack works properly."""
import os
import subprocess
import sys


def test_distutils_hack():
    env = os.environ.copy()
    env['SETUPTOOLS_USE_DISTUTILS'] = 'local'
    subprocess.run([sys.executable, '-c',
                    '\n'.join((
                        'import distutils',
                        'import setuptools._distutils',
                        'if distutils is not setuptools._distutils:',
                        '    raise Exception("Distutils hack failed.")',
                    ))],
                   check=True)


def test_distutils_hack_disabled():
    env = os.environ.copy()
    env['SETUPTOOLS_USE_DISTUTILS'] = ''
    subprocess.run([sys.executable, '-c',
                    '\n'.join((
                        'import distutils',
                        'import setuptools._distutils',
                        'if distutils is setuptools._distutils:',
                        '    raise Exception("Distutils hack not disabled.")',
                    ))],
                   check=True)
