import os
import sys
import subprocess
import tokenize
import shutil
import tempfile

from setuptools import dist
from setuptools.dist import SetupRequirementsError


SETUPTOOLS_IMPLEMENTATION_REVISION = 0.1


class TemporaryBuildDirectory(object):
    def __init__(self):
        self._tmpdir = tempfile.mkdtemp(
            prefix='setuptools')
        self._cwd = os.getcwd()
        
    def __enter__(self):
        """Enter the temporary directory 
        
        Please remember to obtain abs paths 
        before entering
        """
        # Get list of directories to copy
        directories_to_copy = [
            d in os.listdir('.') if not d.startswith('.')]
        for directory in directories_to_copy:
            shutil.copytree(
                os.path.join(self._cwd, directory),
                self._tmpdir)
            
        # Now enter the directory
        os.chdir(self._tmpdir.name)
        
    def __exit__(self):
        os.chdir(self._cwd)
        shutil.rmtree(self._tmpdir)


def _run_setup(setup_script='setup.py'): #
    # Note that we can reuse our build directory between calls
    # Correctness comes first, then optimization later    
    with TemporaryBuildDirectory():
        __file__=setup_script
        f=getattr(tokenize, 'open', open)(__file__)
        code=f.read().replace('\\r\\n', '\\n')
        f.close()
        exec(compile(code, __file__, 'exec'))


def get_build_requires(config_settings):
    requirements = ['setuptools', 'wheel']
    dist.skip_install_eggs = True

    sys.argv = sys.argv[:1] + ['egg_info'] 
        + config_settings["--global-option"]
    try:
        _run_setup()
    except SetupRequirementsError as e:
        requirements += e.specifiers

    dist.skip_install_eggs = False

    return requirements


def get_requires_for_build_wheel(config_settings=None):
    return get_build_requires(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    return get_build_requires(config_settings)


def build_wheel(wheel_directory, config_settings=None,
                metadata_directory=None):
    sys.argv = sys.argv[:1] + ['bdist_wheel']
        + config_settings["--global-option"]
    _run_setup()
    if wheel_directory != 'dist':
        shutil.rmtree(wheel_directory)
        shutil.copytree('dist', wheel_directory)


def build_sdist(sdist_directory, config_settings=None):
    sys.argv = sys.argv[:1] + ['sdist']
        + config_settings["--global-option"]
    _run_setup()
    if sdist_directory != 'dist':
        shutil.rmtree(sdist_directory)
        shutil.copytree('dist', sdist_directory)
