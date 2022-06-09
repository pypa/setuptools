from contextlib import contextmanager
from setuptools import Command, SetuptoolsDeprecationWarning
from setuptools.dist import Distribution
from setuptools.command.build import build
from distutils.command.build import build as distutils_build

import pytest


def test_distribution_gives_setuptools_build_obj(tmpdir_cwd):
    """
    Check that the setuptools Distribution uses the
    setuptools specific build object.
    """

    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['build'],
        packages=[],
        package_data={'': ['path/*']},
    ))
    assert isinstance(dist.get_command_obj("build"), build)


@contextmanager
def _restore_sub_commands():
    orig = distutils_build.sub_commands[:]
    try:
        yield
    finally:
        distutils_build.sub_commands = orig


class Subcommand(Command):
    """Dummy command to be used in tests"""

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise NotImplementedError("just to check if the command runs")


@_restore_sub_commands()
def test_subcommand_in_distutils(tmpdir_cwd):
    """
    Ensure that sub commands registered in ``distutils`` run,
    after instructing the users to migrate to ``setuptools``.
    """
    dist = Distribution(dict(
        packages=[],
        cmdclass={'subcommand': Subcommand},
    ))
    distutils_build.sub_commands.append(('subcommand', None))

    warning_msg = "please use .setuptools.command.build."
    with pytest.warns(SetuptoolsDeprecationWarning, match=warning_msg):
        # For backward compatibility, the subcommand should run anyway:
        with pytest.raises(NotImplementedError, match="the command runs"):
            dist.run_command("build")
