"""
Monkey patching of distutils.
"""

import sys
import distutils.filelist
import platform

import setuptools


__all__ = []
"""
Everything is private. Contact the project team
if you think you need this functionality.
"""


def get_unpatched(cls):
    """Protect against re-patching the distutils if reloaded

    Also ensures that no other distutils extension monkeypatched the distutils
    first.
    """
    while cls.__module__.startswith('setuptools'):
        cls, = cls.__bases__
    if not cls.__module__.startswith('distutils'):
        raise AssertionError(
            "distutils has already been patched by %r" % cls
        )
    return cls


def patch_all():
    # we can't patch distutils.cmd, alas
    distutils.core.Command = setuptools.Command

    has_issue_12885 = (
        sys.version_info < (3, 4, 6)
        or
        (3, 5) < sys.version_info <= (3, 5, 3)
        or
        (3, 6) < sys.version_info
    )

    if has_issue_12885:
        # fix findall bug in distutils (http://bugs.python.org/issue12885)
        distutils.filelist.findall = setuptools.findall

    needs_warehouse = (
        sys.version_info < (2, 7, 13)
        or
        (3, 0) < sys.version_info < (3, 3, 7)
        or
        (3, 4) < sys.version_info < (3, 4, 6)
        or
        (3, 5) < sys.version_info <= (3, 5, 3)
        or
        (3, 6) < sys.version_info
    )

    if needs_warehouse:
        warehouse = 'https://upload.pypi.org/legacy/'
        distutils.config.PyPIRCCommand.DEFAULT_REPOSITORY = warehouse

    _patch_distribution_metadata_write_pkg_file()
    _patch_distribution_metadata_write_pkg_info()

    # Install Distribution throughout the distutils
    for module in distutils.dist, distutils.core, distutils.cmd:
        module.Distribution = setuptools.dist.Distribution

    # Install the patched Extension
    distutils.core.Extension = setuptools.extension.Extension
    distutils.extension.Extension = setuptools.extension.Extension
    if 'distutils.command.build_ext' in sys.modules:
        sys.modules['distutils.command.build_ext'].Extension = (
            setuptools.extension.Extension
        )

    patch_for_msvc_specialized_compiler()


def _patch_distribution_metadata_write_pkg_file():
    """Patch write_pkg_file to also write Requires-Python/Requires-External"""
    distutils.dist.DistributionMetadata.write_pkg_file = (
        setuptools.dist.write_pkg_file
    )


def _patch_distribution_metadata_write_pkg_info():
    """
    Workaround issue #197 - Python 3 prior to 3.2.2 uses an environment-local
    encoding to save the pkg_info. Monkey-patch its write_pkg_info method to
    correct this undesirable behavior.
    """
    environment_local = (3,) <= sys.version_info[:3] < (3, 2, 2)
    if not environment_local:
        return

    distutils.dist.DistributionMetadata.write_pkg_info = (
        setuptools.dist.write_pkg_info
    )


unpatched = dict()


def patch_for_msvc_specialized_compiler():
    """
    Patch functions in distutils to use standalone Microsoft Visual C++
    compilers.
    """
    from . import msvc

    try:
        # Distutil file for MSVC++ 9.0 and upper (Python 2.7 to 3.4)
        import distutils.msvc9compiler as msvc9compiler
    except ImportError:
        pass

    try:
        # Distutil file for MSVC++ 14.0 and upper (Python 3.5+)
        import distutils._msvccompiler as msvc14compiler
    except ImportError:
        pass

    if platform.system() != 'Windows':
        # Compilers only availables on Microsoft Windows
        return

    if unpatched:
        # Already patched
        return

    try:
        # Patch distutils.msvc9compiler
        unpatched['msvc9_find_vcvarsall'] = msvc9compiler.find_vcvarsall
        msvc9compiler.find_vcvarsall = msvc.msvc9_find_vcvarsall
        unpatched['msvc9_query_vcvarsall'] = msvc9compiler.query_vcvarsall
        msvc9compiler.query_vcvarsall = msvc.msvc9_query_vcvarsall
    except NameError:
        pass

    try:
        # Patch distutils._msvccompiler._get_vc_env
        unpatched['msvc14_get_vc_env'] = msvc14compiler._get_vc_env
        msvc14compiler._get_vc_env = msvc.msvc14_get_vc_env
    except NameError:
        pass

    try:
        # Patch distutils._msvccompiler.gen_lib_options for Numpy
        unpatched['msvc14_gen_lib_options'] = msvc14compiler.gen_lib_options
        msvc14compiler.gen_lib_options = msvc.msvc14_gen_lib_options
    except NameError:
        pass
