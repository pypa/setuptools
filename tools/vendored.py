import functools
import re
import subprocess

import jaraco.packaging.metadata
from path import Path


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.is_dir() else path.remove()


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


class Core(str):
    exp = '''(;| and) extra == ['"]core['"]'''

    def bare(self):
        """
        Remove 'extra == "core"' from any dependency.
        """
        return re.sub(self.exp, '', self)

    def __bool__(self):
        """
        Determine if the dependency is "core".
        """
        return bool(re.search(self.exp, self))

    @classmethod
    def load(cls):
        """
        Read the dependencies from `.[core]`.
        """
        specs = metadata().get_all('Requires-Dist')
        return [dep.bare() for dep in map(Core, specs) if dep]


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


def update_vendored():
    target = Path('setuptools/_vendor')
    deps = Core.load()
    clean(target)
    install_deps(deps, target)


__name__ == '__main__' and update_vendored()
