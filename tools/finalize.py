"""
Finalize the repo for a release. Invokes towncrier.
"""

__requires__ = ['towncrier', 'jaraco.develop>=7.23']

import pathlib
import re
import subprocess
import sys

from jaraco.develop import towncrier

bump_version_command = [
    sys.executable,
    '-m',
    'bumpversion',
    towncrier.release_kind(),
]


def get_version():
    return towncrier.semver(towncrier.get_version())


def save_version(version):
    pathlib.Path(".version").unlink()  # Remove development version
    pathlib.Path(".stable").write_text(version, encoding="utf-8")
    subprocess.check_output(['git', 'add', ".stable"])


def update_changelog():
    towncrier.run('build', '--yes')
    _repair_changelog()


def _repair_changelog():
    """
    Workaround for #2666
    """
    changelog_fn = pathlib.Path('NEWS.rst')
    changelog = changelog_fn.read_text(encoding='utf-8')
    fixed = re.sub(r'^(v[0-9.]+)v[0-9.]+$', r'\1', changelog, flags=re.M)
    changelog_fn.write_text(fixed, encoding='utf-8')
    subprocess.check_output(['git', 'add', changelog_fn])


def ensure_config():
    """
    Double-check that Git has an e-mail configured.
    """
    subprocess.check_output(['git', 'config', 'user.email'])


if __name__ == '__main__':
    version = get_version()
    print("Cutting release at", version)
    ensure_config()
    save_version(version)
    towncrier.check_changes()
    update_changelog()
    subprocess.check_call(['git', 'commit', '-a', '-m', f'Finalize #{version}'])
    subprocess.check_call(['git', 'tag', '-a', '-m', '', version])
