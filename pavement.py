import re
import sys
import subprocess
from fnmatch import fnmatch

from paver.easy import task, path as Path


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
        text = re.sub(r' (pyparsing)', rf' {new_root}.\1', text)
        text = text.replace(
            'from six.moves.urllib import parse',
            'from urllib import parse',
        )
        file.write_text(text)


def clean(vendor):
    """
    Remove all files out of the vendor directory except the meta
    data (as pip uninstall doesn't support -t).
    """
    remove_all(
        path
        for path in vendor.glob('*')
        if path.basename() != 'vendored.txt'
    )


def install(vendor):
    clean(vendor)
    install_args = [
        sys.executable,
        '-m', 'pip',
        'install',
        '-r', str(vendor / 'vendored.txt'),
        '-t', str(vendor),
    ]
    subprocess.check_call(install_args)
    move_licenses(vendor)
    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))
    remove_all(vendor.glob('six.py'))
    (vendor / '__init__.py').write_text('')


def move_licenses(vendor):
    license_patterns = ("*LICEN[CS]E*", "COPYING*", "NOTICE*", "AUTHORS*")
    licenses = (
        entry
        for path in vendor.glob("*.dist-info")
        for entry in path.glob("*")
        if any(fnmatch(str(entry), p) for p in license_patterns)
    )
    for file in licenses:
        file.move(_find_license_dest(file, vendor))


def _find_license_dest(license_file, vendor):
    basename = license_file.basename()
    pkg = license_file.dirname().basename().replace(".dist-info", "")
    parts = pkg.split("-")
    acc = []
    for part in parts:
        # Find actual name from normalized name + version
        acc.append(part)
        for option in ("_".join(acc), "-".join(acc), ".".join(acc)):
            candidate = vendor / option
            if candidate.isdir():
                return candidate / basename
            if Path(f"{candidate}.py").isfile():
                return Path(f"{candidate}.{basename}")

    raise FileNotFoundError(f"No destination found for {license_file}")


def update_pkg_resources():
    vendor = Path('pkg_resources/_vendor')
    install(vendor)
    rewrite_packaging(vendor / 'packaging', 'pkg_resources.extern')


def update_setuptools():
    vendor = Path('setuptools/_vendor')
    install(vendor)
    rewrite_packaging(vendor / 'packaging', 'setuptools.extern')
