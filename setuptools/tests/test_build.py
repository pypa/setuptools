from setuptools.dist import Distribution
from setuptools.command.build import build
from distutils.command.build import build as distutils_build


def test_distribution_gives_setuptools_build_obj(tmpdir_cwd):
    """
    Check that the setuptools Distribution uses the
    setuptools specific build object.
    """
    dist = Distribution(dict(
        script_name='setup.py',
        script_args=['build'],
        packages=[''],
        package_data={'': ['path/*']},
    ))

    build_obj = dist.get_command_obj("build")
    assert isinstance(build_obj, build)

    build_obj.sub_commands.append(("custom_build_subcommand", None))

    distutils_subcommands = [cmd[0] for cmd in distutils_build.sub_commands]
    assert "custom_build_subcommand" not in distutils_subcommands
