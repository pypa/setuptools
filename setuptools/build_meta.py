"""A PEP 517 interface to setuptools

Previously, when a user or a command line tool (let's call it a "frontend")
needed to make a request of setuptools to take a certain action, for
example, generating a list of installation requirements, the frontend would
would call "setup.py egg_info" or "setup.py bdist_wheel" on the command line.

PEP 517 defines a different method of interfacing with setuptools. Rather
than calling "setup.py" directly, the frontend should:

  1. Set the current directory to the directory with a setup.py file
  2. Import this module into a safe python interpreter (one in which
     setuptools can potentially set global variables or crash hard).
  3. Call one of the functions defined in PEP 517.

What each function does is defined in PEP 517. However, here is a "casual"
definition of the functions (this definition should not be relied on for
bug reports or API stability):

  - `build_wheel`: build a wheel in the folder and return the basename
  - `get_requires_for_build_wheel`: get the `setup_requires` to build
  - `prepare_metadata_for_build_wheel`: get the `install_requires`
  - `build_sdist`: build an sdist in the folder and return the basename
  - `get_requires_for_build_sdist`: get the `setup_requires` to build

Again, this is not a formal definition! Just a "taste" of the module.
"""

import os
import sys
import tokenize
import shutil
import contextlib

import setuptools
import setuptools.command.dist_info
import distutils

from os.path import basename, dirname

class SetupRequirementsError(BaseException):
    def __init__(self, specifiers):
        self.specifiers = specifiers


class Distribution(setuptools.dist.Distribution):
    def fetch_build_eggs(self, specifiers):
        raise SetupRequirementsError(specifiers)

    @classmethod
    @contextlib.contextmanager
    def patch(cls):
        """
        Replace
        distutils.dist.Distribution with this class
        for the duration of this context.
        """
        orig = distutils.core.Distribution
        distutils.core.Distribution = cls
        try:
            yield
        finally:
            distutils.core.Distribution = orig


class dist_info(setuptools.command.dist_info.dist_info):
    def run(self):
        dist_info._orig.run(self)
        dist_info.dist_info = self.dist_info

    @classmethod
    @contextlib.contextmanager
    def patch(cls):
        """
        Replace
        distutils.dist.Distribution with this class
        for the duration of this context.
        """
        dist_info._orig = setuptools.command.dist_info.dist_info
        setuptools.command.dist_info.dist_info = cls
        try:
            yield
        finally:
            setuptools.command.dist_info.dist_info = dist_info._orig


def _run_setup(args, config_settings=None, setup_script='setup.py'):
    # Note that we can reuse our build directory between calls
    # Correctness comes first, then optimization later
    config_settings = _fix_config(config_settings)
    sys.argv = [setup_script] + args + \
        config_settings['--global-option']
    __file__ = setup_script
    __name__ = '__main__'
    f = getattr(tokenize, 'open', open)(__file__)
    code = f.read().replace('\\r\\n', '\\n')
    f.close()
    exec(compile(code, __file__, 'exec'), locals())


def _fix_config(config_settings):
    config_settings = config_settings or {}
    config_settings.setdefault('--global-option', [])
    return config_settings


def _get_build_requires(config_settings):
    requirements = ['setuptools', 'wheel']
    try:
        with Distribution.patch():
            _run_setup(['egg_info'], config_settings)
    except SetupRequirementsError as e:
        requirements += e.specifiers

    return requirements


def get_requires_for_build_wheel(config_settings=None):
    return _get_build_requires(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    return _get_build_requires(config_settings)


def prepare_metadata_for_build_wheel(metadata_directory,
                                     config_settings=None):
    with dist_info.patch():    
        _run_setup(['dist_info', '--egg-base',
                    metadata_directory], config_settings)

    # PEP 517 requires that the .dist-info directory be placed in the
    # metadata_directory. To comply, we MUST copy the directory to the root
    if dirname(dist_info.dist_info) != metadata_directory:
        shutil.move(dist_info.dist_info, metadata_directory)

    return basename(dist_info.dist_info)


def build_wheel(wheel_directory, config_settings=None,
                metadata_directory=None):
    wheel_directory = os.path.abspath(wheel_directory)
    _run_setup(['bdist_wheel'], config_settings)
    if wheel_directory != 'dist':
        shutil.rmtree(wheel_directory)
        shutil.copytree('dist', wheel_directory)

    wheels = [f for f in os.listdir(wheel_directory)
              if f.endswith('.whl')]

    assert len(wheels) == 1
    return wheels[0]


def build_sdist(sdist_directory, config_settings=None):
    sdist_directory = os.path.abspath(sdist_directory)
    _run_setup(['sdist'], config_settings)
    if sdist_directory != 'dist':
        shutil.rmtree(sdist_directory)
        shutil.copytree('dist', sdist_directory)

    sdists = [f for f in os.listdir(sdist_directory)
              if f.endswith('.tar.gz')]

    assert len(sdists) == 1
    return sdists[0]
