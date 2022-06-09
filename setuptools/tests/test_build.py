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
    class Subcommand(Command):
        def run(self):
            raise NotImplementedError("just to check if the command runs")

    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['build'],
        packages=[''],
        package_data={'': ['path/*']},
        cmdclass={'subcommand': Subcommand},
    ))

    distutils_build.sub_commands.append(('subcommand', None))

    warning_msg = "please use .setuptools.command.build."
    with pytest.raises(SetuptoolsDeprecationWarning, match=warning_msg):
        # For backward compatibility, the subcommand should run anyway:
        with pytest.raises(NotImplementedError, match="the command runs"):
            build(dist).run()
