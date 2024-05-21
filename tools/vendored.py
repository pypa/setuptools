import re
import shutil
import sys
import subprocess
from textwrap import dedent

from path import Path


def remove_all(paths):
    for path in paths:
        path.rmtree() if path.is_dir() else path.remove()


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


def rewrite_jaraco_text(pkg_files, new_root):
    """
    Rewrite imports in jaraco.text to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.read_text()
        text = re.sub(r' (jaraco\.)', rf' {new_root}.\1', text)
        text = re.sub(r' (importlib_resources)', rf' {new_root}.\1', text)
        # suppress loading of lorem_ipsum; ref #3072
        text = re.sub(r'^lorem_ipsum.*\n$', '', text, flags=re.M)
        file.write_text(text)


def repair_namespace(pkg_files):
    # required for zip-packaged setuptools #3084
    pkg_files.joinpath('__init__.py').write_text('')


def rewrite_jaraco_functools(pkg_files, new_root):
    """
    Rewrite imports in jaraco.functools to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.read_text()
        text = re.sub(r' (more_itertools)', rf' {new_root}.\1', text)
        file.write_text(text)


def rewrite_jaraco_context(pkg_files, new_root):
    """
    Rewrite imports in jaraco.context to redirect to vendored copies.
    """
    for file in pkg_files.glob('context.py'):
        text = file.read_text()
        text = re.sub(r' (backports)', rf' {new_root}.\1', text)
        file.write_text(text)


def rewrite_importlib_resources(pkg_files, new_root):
    """
    Rewrite imports in importlib_resources to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.read_text().replace('importlib_resources.abc', '.abc')
        text = text.replace('zipp', '..zipp')
        file.write_text(text)


def rewrite_importlib_metadata(pkg_files, new_root):
    """
    Rewrite imports in importlib_metadata to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.read_text()
        text = text.replace('import zipp', 'from .. import zipp')
        file.write_text(text)


def rewrite_more_itertools(pkg_files: Path):
    """
    Defer import of concurrent.futures. Workaround for #3090.
    """
    more_file = pkg_files.joinpath('more.py')
    text = more_file.read_text()
    text = re.sub(r'^.*concurrent.futures.*?\n', '', text, flags=re.MULTILINE)
    text = re.sub(
        'ThreadPoolExecutor',
        '__import__("concurrent.futures").futures.ThreadPoolExecutor',
        text,
    )
    more_file.write_text(text)


def rewrite_wheel(pkg_files: Path):
    """
    Remove parts of wheel not needed by bdist_wheel, and rewrite imports to use
    setuptools's own code or vendored dependencies.
    """
    shutil.rmtree(pkg_files / 'cli')
    shutil.rmtree(pkg_files / 'vendored')
    pkg_files.joinpath('_setuptools_logging.py').unlink()
    pkg_files.joinpath('__main__.py').unlink()
    pkg_files.joinpath('bdist_wheel.py').unlink()

    # Rewrite vendored imports to use setuptools's own vendored libraries
    for path in pkg_files.iterdir():
        if path.suffix == '.py':  # type: ignore[attr-defined]
            code = path.read_text()
            if path.name == 'wheelfile.py':
                code = re.sub(
                    r"^from wheel.util import ",
                    r"from .util import ",
                    code,
                    flags=re.MULTILINE,
                )

                # No need to keep the wheel.cli package just for this trivial exception
                code = re.sub(
                    r"^from wheel.cli import WheelError\n",
                    r"",
                    code,
                    flags=re.MULTILINE,
                )
                code += dedent(
                    """

                    class WheelError(Exception):
                        pass
                    """
                )
            else:
                code = re.sub(
                    r"^from \.vendored\.([\w.]+) import ",
                    r"from ..\1 import ",
                    code,
                    flags=re.MULTILINE,
                )
                code = re.sub(
                    r"^from \.util import log$",
                    r"from distutils import log$",
                    code,
                    flags=re.MULTILINE,
                )

            path.write_text(code)  # type: ignore[attr-defined]


def rewrite_platformdirs(pkg_files: Path):
    """
    Replace some absolute imports with relative ones.
    """
    init = pkg_files.joinpath('__init__.py')
    text = init.read_text()
    text = text.replace('from platformdirs.', 'from .')
    init.write_text(text)


def clean(vendor):
    """
    Remove all files out of the vendor directory except the meta
    data (as pip uninstall doesn't support -t).
    """
    ignored = ['vendored.txt', 'ruff.toml']
    remove_all(path for path in vendor.glob('*') if path.basename() not in ignored)


def install(vendor):
    clean(vendor)
    install_args = [
        sys.executable,
        '-m',
        'pip',
        'install',
        '-r',
        str(vendor / 'vendored.txt'),
        '-t',
        str(vendor),
    ]
    subprocess.check_call(install_args)
    (vendor / '__init__.py').write_text('')


def update_pkg_resources():
    vendor = Path('pkg_resources/_vendor')
    install(vendor)
    rewrite_packaging(vendor / 'packaging', 'pkg_resources.extern')
    repair_namespace(vendor / 'jaraco')
    repair_namespace(vendor / 'backports')
    rewrite_jaraco_text(vendor / 'jaraco/text', 'pkg_resources.extern')
    rewrite_jaraco_functools(vendor / 'jaraco/functools', 'pkg_resources.extern')
    rewrite_jaraco_context(vendor / 'jaraco', 'pkg_resources.extern')
    rewrite_importlib_resources(vendor / 'importlib_resources', 'pkg_resources.extern')
    rewrite_more_itertools(vendor / "more_itertools")
    rewrite_platformdirs(vendor / "platformdirs")


def update_setuptools():
    vendor = Path('setuptools/_vendor')
    install(vendor)
    rewrite_packaging(vendor / 'packaging', 'setuptools.extern')
    repair_namespace(vendor / 'jaraco')
    repair_namespace(vendor / 'backports')
    rewrite_jaraco_text(vendor / 'jaraco/text', 'setuptools.extern')
    rewrite_jaraco_functools(vendor / 'jaraco/functools', 'setuptools.extern')
    rewrite_jaraco_context(vendor / 'jaraco', 'setuptools.extern')
    rewrite_importlib_resources(vendor / 'importlib_resources', 'setuptools.extern')
    rewrite_importlib_metadata(vendor / 'importlib_metadata', 'setuptools.extern')
    rewrite_more_itertools(vendor / "more_itertools")
    rewrite_wheel(vendor / "wheel")


def yield_top_level(name):
    """Iterate over all modules and (top level) packages vendored
    >>> roots = set(yield_top_level("setuptools"))
    >>> examples = roots & {"jaraco", "backports", "zipp"}
    >>> list(sorted(examples))
    ['backports', 'jaraco', 'zipp']
    >>> 'bin' in examples
    False
    """
    vendor = Path(f"{name}/_vendor")
    ignore = {"__pycache__", "__init__.py", ".ruff_cache", "bin"}

    for item in sorted(vendor.iterdir()):
        if item.name in ignore:
            continue
        if item.is_dir() and item.suffix != ".dist-info":
            yield str(item.name)
        if item.is_file() and item.suffix == ".py":
            yield str(item.stem)


__name__ == '__main__' and update_vendored()
