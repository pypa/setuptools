import os
import sys
import subprocess
import tokenize
import shutil
import tempfile

from setuptools import dist
from setuptools.dist import SetupRequirementsError


SETUPTOOLS_IMPLEMENTATION_REVISION = 0.1

def _run_setup(setup_script='setup.py'): #
    # Note that we can reuse our build directory between calls
    # Correctness comes first, then optimization later    
    __file__=setup_script
    f=getattr(tokenize, 'open', open)(__file__)
    code=f.read().replace('\\r\\n', '\\n')
    f.close()
    exec(compile(code, __file__, 'exec'))


def fix_config(config_settings):
    config_settings = config_settings or {}
    config_settings.setdefault('--global-option', [])
    return config_settings

def get_build_requires(config_settings):
    config_settings = fix_config(config_settings)
    requirements = ['setuptools', 'wheel']
    dist.skip_install_eggs = True

    sys.argv = sys.argv[:1] + ['egg_info'] + \
        config_settings["--global-option"]
    try:
        _run_setup()
    except SetupRequirementsError as e:
        requirements += e.specifiers

    dist.skip_install_eggs = False

    return requirements


def get_requires_for_build_wheel(config_settings=None):
    config_settings = fix_config(config_settings)
    return get_build_requires(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    config_settings = fix_config(config_settings)
    return get_build_requires(config_settings)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    sys.argv = sys.argv[:1] + ['dist_info', '--egg-base', metadata_directory]
    _run_setup()

def build_wheel(wheel_directory, config_settings=None,
                metadata_directory=None):
    config_settings = fix_config(config_settings)
    wheel_directory = os.path.abspath(wheel_directory)
    sys.argv = sys.argv[:1] + ['bdist_wheel'] + \
        config_settings["--global-option"]
    _run_setup()
    if wheel_directory != 'dist':
        shutil.rmtree(wheel_directory)
        shutil.copytree('dist', wheel_directory)


def build_sdist(sdist_directory, config_settings=None):
    config_settings = fix_config(config_settings)
    sdist_directory = os.path.abspath(sdist_directory)
    sys.argv = sys.argv[:1] + ['sdist'] + \
        config_settings["--global-option"]
    _run_setup()
    if sdist_directory != 'dist':
        shutil.rmtree(sdist_directory)
        shutil.copytree('dist', sdist_directory)
