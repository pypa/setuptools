import re

from paver.easy import task, path as Path
import pip


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.isdir() else path.remove()


@task
def update_vendored():
    update_pkg_resources()
    update_setuptools()


def rewrite_packaging(pkg_files, new_root):
    """
    Rewrite imports in packaging to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.text()
        text = re.sub(r' (pyparsing|six)', rf' {new_root}.\1', text)
        file.write_text(text)


def install(vendor):
    clean(vendor)
    install_args = [
        'install',
        '-r', str(vendor / 'vendored.txt'),
        '-t', str(vendor),
    ]
    pip.main(install_args)
    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))

def update_pkg_resources():
    vendor = Path('pkg_resources/_vendor')
    # pip uninstall doesn't support -t, so do it manually
    remove_all(vendor.glob('packaging*'))
    remove_all(vendor.glob('six*'))
    remove_all(vendor.glob('pyparsing*'))
    remove_all(vendor.glob('appdirs*'))
    install_args = [
        'install',
        '-r', str(vendor / 'vendored.txt'),
        '-t', str(vendor),
    ]
    pip.main(install_args)
    rewrite_packaging(vendor / 'packaging', 'pkg_resources.extern.')
    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))


def update_setuptools():
    vendor = Path('setuptools/_vendor')
    # pip uninstall doesn't support -t, so do it manually
    remove_all(vendor.glob('packaging*'))
    remove_all(vendor.glob('six*'))
    remove_all(vendor.glob('pyparsing*'))
    install_args = [
        'install',
        '-r', str(vendor / 'vendored.txt'),
        '-t', str(vendor),
    ]
    pip.main(install_args)
    rewrite_packaging(vendor / 'packaging', 'setuptools.extern')
    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))
