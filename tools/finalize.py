"""
Finalize the repo for a release. Invokes towncrier and bumpversion.
"""

__requires__ = ['bump2version', 'towncrier']


import subprocess
import pathlib
import re
import sys


def release_kind():
    """
    Determine which release to make based on the files in the
    changelog.
    """
    # use min here as 'major' < 'minor' < 'patch'
    return min(
        'major' if 'breaking' in file.name else
        'minor' if 'change' in file.name else
        'patch'
        for file in pathlib.Path('changelog.d').iterdir()
    )


bump_version_command = [
    sys.executable,
    '-m', 'bumpversion',
    release_kind(),
]


def get_version():
    cmd = bump_version_command + ['--dry-run', '--verbose']
    out = subprocess.check_output(cmd, text=True)
    return re.search('^new_version=(.*)', out, re.MULTILINE).group(1)


def update_changelog():
    cmd = [
        sys.executable, '-m',
        'towncrier',
        '--version', get_version(),
        '--yes',
    ]
    subprocess.check_call(cmd)


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
    update_changelog()
    bump_version()
