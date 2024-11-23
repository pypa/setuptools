import functools
import re
import subprocess

import jaraco.packaging.metadata
from path import Path


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.is_dir() else path.remove()


def update_vendored():
    update_setuptools()


def clean(target):
    """
    Remove all files out of the target directory except the meta
    data (as pip uninstall doesn't support -t).
    """
    ignored = ['ruff.toml']
    remove_all(path for path in target.glob('*') if path.basename() not in ignored)


@functools.lru_cache
def metadata():
    return jaraco.packaging.metadata.load('.')


def upgrade_core(dep):
    """
    Remove 'extra == "core"' from any dependency.
    """
    return re.sub('''(;| and) extra == ['"]core['"]''', '', dep)


def load_deps():
    """
    Read the dependencies from `.[core]`.
    """
    return list(map(upgrade_core, metadata().get_all('Requires-Dist')))


def min_python():
    return metadata()['Requires-Python'].removeprefix('>=').strip()


def install_deps(deps, target):
    """
    Install the deps to vendor.
    """
    install_args = [
        'uv',
        'pip',
        'install',
        '--target',
        str(target),
        '--python-version',
        min_python(),
        '--only-binary',
        ':all:',
    ] + list(deps)
    subprocess.check_call(install_args)


def update_setuptools():
    target = Path('setuptools/_vendor')
    deps = load_deps()
    clean(target)
    install_deps(deps, target)


__name__ == '__main__' and update_vendored()
