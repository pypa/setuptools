import re
from textwrap import dedent

import sys

from paver.easy import task, path as Path
import pip


del sys.path[0]


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.isdir() else path.remove()


def rewrite_pkg_resources(pkg_resources, new_root):
    for file in pkg_resources.glob('__init__.py'):
        text = file.text()
        text = text.replace(dedent("""
            import appdirs
            import packaging.version
            import packaging.specifiers
            import packaging.requirements
            import packaging.markers
            """), dedent(f"""
            from {new_root} import appdirs
            from {new_root} import packaging
            __import__('{new_root}.packaging.version')
            __import__('{new_root}.packaging.specifiers')
            __import__('{new_root}.packaging.requirements')
            __import__('{new_root}.packaging.markers')
            """),
        )
        text = text.replace(dedent("""
            import six
            from six.moves import urllib, map, filter
            """), dedent(f"""
            from {new_root} import six
            from {new_root}.six import urllib, map, filter
            """),
        )
        file.write_text(text)
    remove_all(pkg_resources.glob('_vendor'))
    remove_all(pkg_resources.glob('extern'))
    remove_all(pkg_resources.glob('tests'))


@task
def update_vendored():
    update_setuptools()


def rewrite_packaging(pkg_files, new_root):
    """
    Rewrite imports in packaging to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.text()
        text = re.sub(r' (pyparsing|six)', rf' {new_root}.\1', text)
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
        'install',
        '-r', str(vendor / 'vendored.txt'),
        '-t', str(vendor),
    ]
    pip.main(install_args)
    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))
    (vendor / '__init__.py').write_text('')


def update_setuptools():
    vendor = Path('setuptools/_vendor')
    install(vendor)
    rewrite_packaging(vendor / 'packaging', 'setuptools.extern')
    rewrite_pkg_resources(vendor / 'pkg_resources', 'setuptools.extern')
