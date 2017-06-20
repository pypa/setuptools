import os
import sys
import subprocess
import tokenize
import shutil

from setuptools import dist
from setuptools.dist import SetupRequirementsError


def _run_setup(setup_script='setup.py'): #
    __file__=setup_script
    f=getattr(tokenize, 'open', open)(__file__)
    code=f.read().replace('\\r\\n', '\\n')
    f.close()
    exec(compile(code, __file__, 'exec'))


def get_build_requires(config_settings):
    requirements = ['setuptools', 'wheel']
    dist.skip_install_eggs = True

    sys.argv = sys.argv[:1] + ['egg_info']
    try:
        _run_setup()
    except SetupRequirementsError as e:
        requirements += e.specifiers

    dist.skip_install_eggs = False

    return requirements


def build_wheel(wheel_directory, config_settings, metadata_directory=None):
    sys.argv = sys.argv[:1] + ['bdist_wheel']
    _run_setup()
    if wheel_directory != 'dist':
        shutil.rmtree(wheel_directory)
        shutil.copytree('dist', wheel_directory)
