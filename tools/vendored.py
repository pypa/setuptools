import functools
import sys
import subprocess

import jaraco.packaging.metadata
from path import Path


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.is_dir() else path.remove()


def update_vendored():
    update_pkg_resources()
    update_setuptools()


def clean(vendor):
    """
    Remove all files out of the vendor directory except the meta
    data (as pip uninstall doesn't support -t).
    """
    ignored = ['ruff.toml']
    remove_all(path for path in vendor.glob('*') if path.basename() not in ignored)


def update_pkg_resources():
    deps = [
        'packaging >= 24',
        'platformdirs >= 2.6.2',
        'jaraco.text >= 3.7',
    ]
    # workaround for https://github.com/pypa/pip/issues/12770
    deps += [
        'importlib_resources >= 5.10.2',
        'zipp >= 3.7',
        'backports.tarfile',
    ]
    vendor = Path('pkg_resources/_vendor')
    clean(vendor)
    install_deps(deps, vendor)


@functools.cache
def metadata():
    return jaraco.packaging.metadata.load('.')


def load_deps():
    """
    Read the dependencies from `.`.
    """
    return metadata().get_all('Requires-Dist')


def min_python():
    return metadata()['Requires-Python'].removeprefix('>=').strip()


def install_deps(deps, vendor):
    """
    Install the deps to vendor.
    """
    # workaround for https://github.com/pypa/pip/issues/12770
    deps += [
        'zipp >= 3.7',
        'backports.tarfile',
    ]
    install_args = [
        sys.executable,
        '-m',
        'pip',
        'install',
        '--target',
        str(vendor),
        '--python-version',
        min_python(),
        '--only-binary',
        ':all:',
    ] + list(deps)
    subprocess.check_call(install_args)


def update_setuptools():
    vendor = Path('setuptools/_vendor')
    deps = load_deps()
    clean(vendor)
    install_deps(deps, vendor)


__name__ == '__main__' and update_vendored()
