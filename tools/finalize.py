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
        'major'
        if 'breaking' in file.name
        else 'minor'
        if 'change' in file.name
        else 'patch'
        for file in pathlib.Path('changelog.d').iterdir()
    )


bump_version_command = [
    sys.executable,
    '-m',
    'bumpversion',
    release_kind(),
]


def get_version():
    cmd = bump_version_command + ['--dry-run', '--verbose']
    out = subprocess.check_output(cmd, text=True)
    return re.search('^new_version=(.*)', out, re.MULTILINE).group(1)


def update_changelog():
    cmd = [
        sys.executable,
        '-m',
        'towncrier',
        'build',
        '--version',
        get_version(),
        '--yes',
    ]
    subprocess.check_call(cmd)
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


def check_changes():
    """
    Verify that all of the files in changelog.d have the appropriate
    names.
    """
    allowed = 'deprecation', 'breaking', 'change', 'doc', 'misc'
    except_ = 'README.rst', '.gitignore'
    news_fragments = (
        file
        for file in pathlib.Path('changelog.d').iterdir()
        if file.name not in except_
    )
    unrecognized = [
        str(file)
        for file in news_fragments
        if not any(f".{key}" in file.suffixes for key in allowed)
    ]
    if unrecognized:
        raise ValueError(f"Some news fragments have invalid names: {unrecognized}")


if __name__ == '__main__':
    print("Cutting release at", get_version())
    ensure_config()
    check_changes()
    update_changelog()
    bump_version()
