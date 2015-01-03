"""
If setuptools is not already installed in the environment, it's not possible
to invoke setuptools' own commands. This routine will bootstrap this local
environment by creating a minimal egg-info directory and then invoking the
egg-info command to flesh out the egg-info directory.
"""

import os
import sys
import textwrap
import subprocess


minimal_egg_info = textwrap.dedent("""
    [distutils.commands]
    egg_info = setuptools.command.egg_info:egg_info

    [distutils.setup_keywords]
    include_package_data = setuptools.dist:assert_bool
    install_requires = setuptools.dist:check_requirements
    extras_require = setuptools.dist:check_extras
    entry_points = setuptools.dist:check_entry_points

    [egg_info.writers]
    dependency_links.txt = setuptools.command.egg_info:overwrite_arg
    entry_points.txt = setuptools.command.egg_info:write_entries
    requires.txt = setuptools.command.egg_info:write_requirements
    """)

def ensure_egg_info():
    if os.path.exists('setuptools.egg-info'):
        return
    print("adding minimal entry_points")
    build_egg_info()


def build_egg_info():
    """
    Build a minimal egg-info, enough to invoke egg_info
    """

    os.mkdir('setuptools.egg-info')
    with open('setuptools.egg-info/entry_points.txt', 'w') as ep:
        ep.write(minimal_egg_info)


def run_egg_info():
    cmd = [sys.executable, 'setup.py', 'egg_info']
    print("Regenerating egg_info")
    subprocess.check_call(cmd)
    print("...and again.")
    subprocess.check_call(cmd)


if __name__ == '__main__':
    ensure_egg_info()
    run_egg_info()
