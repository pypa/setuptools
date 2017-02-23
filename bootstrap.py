"""
If setuptools is not already installed in the environment, it's not possible
to invoke setuptools' own commands. This routine will bootstrap this local
environment by creating a minimal egg-info directory and then invoking the
egg-info command to flesh out the egg-info directory.
"""

from __future__ import unicode_literals

import os
import io
import re
import contextlib
import tempfile
import shutil
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
    filename = 'setuptools.egg-info/entry_points.txt'
    with io.open(filename, 'w', encoding='utf-8') as ep:
        ep.write(minimal_egg_info)


def run_egg_info():
    cmd = [sys.executable, 'setup.py', 'egg_info']
    print("Regenerating egg_info")
    subprocess.check_call(cmd)
    print("...and again.")
    subprocess.check_call(cmd)


def gen_deps():
    with io.open('setup.py', encoding='utf-8') as strm:
        text = strm.read()
    pattern = r'install_requires=\[(.*?)\]'
    match = re.search(pattern, text, flags=re.M|re.DOTALL)
    reqs = eval(match.group(1).replace('\n', ''))
    with io.open('requirements.txt', 'w', encoding='utf-8') as reqs_file:
        reqs_file.write('\n'.join(reqs))


@contextlib.contextmanager
def install_deps():
    "Just in time make the deps available"
    import pip
    tmpdir = tempfile.mkdtemp()
    args = [
        'install',
        '-t', tmpdir,
        '-r', 'requirements.txt',
    ]
    pip.main(args)
    os.environ['PYTHONPATH'] = tmpdir
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def py26_make_archive(filename, type, source_root):
    "quick and dirty backport of shutil.make_archive"
    import zipfile
    assert type == 'zip'
    filename += '.' + type
    zip_file = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(source_root):
        for file in files:
            target = os.path.join(root, file)
            rel_target = os.path.relpath(target, os.path.join(source_root))
            zip_file.write(target, rel_target)

vars(shutil).setdefault('make_archive', py26_make_archive)


def bundle_deps():
    """
    Generate 'build-deps.zip'
    """
    gen_deps()
    with install_deps() as dir:
        shutil.make_archive('build-deps', 'zip', dir)
    os.remove('requirements.txt')


def main():
    bundle_deps()
    ensure_egg_info()
    run_egg_info()


__name__ == '__main__' and main()
