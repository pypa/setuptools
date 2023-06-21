"""
Finalize the repo for a release. Invokes towncrier and bumpversion.
"""

__requires__ = ['bump2version', 'towncrier', 'jaraco.develop>=7.21']


import subprocess
import pathlib
import re
import sys

from jaraco.develop import towncrier


bump_version_command = [
    sys.executable,
    '-m',
    'bumpversion',
    towncrier.release_kind(),
]


def get_version():
    cmd = bump_version_command + ['--dry-run', '--verbose']
    out = subprocess.check_output(cmd, text=True)
    return re.search('^new_version=(.*)', out, re.MULTILINE).group(1)


def update_changelog():
    towncrier.run('build', '--yes')
    _repair_changelog()


def _repair_changelog():
    """
    Workaround for #2666
    """
    changelog_fn = pathlib.Path('CHANGES.rst')
    changelog = changelog_fn.read_text(encoding='utf-8')
    fixed = re.sub(r'^(v[0-9.]+)v[0-9.]+$', r'\1', changelog, flags=re.M)
    changelog_fn.write_text(fixed, encoding='utf-8')
    subprocess.check_output(['git', 'add', changelog_fn])


def bump_version():
    cmd = bump_version_command + ['--allow-dirty']
    subprocess.check_call(cmd)


def ensure_config():
    """
    Double-check that Git has an e-mail configured.
    """
    subprocess.check_output(['git', 'config', 'user.email'])


if __name__ == '__main__':
    print("Cutting release at", get_version())
    ensure_config()
    towncrier.check_changes()
    update_changelog()
    bump_version()
