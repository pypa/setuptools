import re
from textwrap import dedent

from paver.easy import task, path as Path
import pip


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.isdir() else path.remove()


def patch_pkg_resources(vendor):
    pkg_resources = vendor / 'pkg_resources'
    for file in pkg_resources.glob('__init__.py'):
        text = file.text()
        text = text.replace(dedent("""
            import appdirs
            import packaging.version
            import packaging.specifiers
            import packaging.requirements
            import packaging.markers
            """), dedent("""
            from setuptools.extern import appdirs
            from setuptools.extern import packaging
            __import__('setuptools.extern.packaging.version')
            __import__('setuptools.extern.packaging.specifiers')
            __import__('setuptools.extern.packaging.requirements')
            __import__('setuptools.extern.packaging.markers')
            """),
        )
        text = text.replace(dedent("""
            import six
            from six.moves import urllib, map, filter
            """), dedent("""
            from setuptools.extern import six
            from setuptools.extern.six import urllib, map, filter
            """),
        )
        file.write_text(text)
    remove_all(vendor.glob('setuptools/_vendor/pkg_resources/_vendor'))
    remove_all(vendor.glob('setuptools/_vendor/pkg_resources/extern'))
    remove_all(vendor.glob('setuptools/_vendor/pkg_resources/tests'))


@task
def update_vendored():
    vendor = Path('setuptools/_vendor')
    # pip uninstall doesn't support -t, so do it manually
    remove_all(vendor.glob('packaging*'))
    remove_all(vendor.glob('six*'))
    remove_all(vendor.glob('pyparsing*'))
    remove_all(vendor.glob('appdirs*'))
    remove_all(vendor.glob('pkg_resources*'))
    install_args = [
        'install',
        '-r', str(vendor / 'vendored.txt'),
        '-t', str(vendor),
    ]
    pip.main(install_args)
    packaging = vendor / 'packaging'
    for file in packaging.glob('*.py'):
        text = file.text()
        text = re.sub(r' (pyparsing|six)', r' setuptools.extern.\1', text)
        file.write_text(text)

    patch_pkg_resources(vendor)

    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))
