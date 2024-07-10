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
    upgrade = "--upgrade" in sys.argv  # Very simple, no need for argparse yet.
    update_target('pkg_resources', upgrade=upgrade)
    update_target(
        'setuptools',
        upgrade=upgrade,
        constraints=Path('pkg_resources/_vendor/vendored.txt'),  # ensure compatibility
    )


def repair_imports(vendor):
    """
    Rewrite imports to redirect to vendored copies.
    This applies to all Python files inside the ``_vendor`` directory.
    """
    target = vendor.parent.name  # setuptools or pkg_resources
    names = rf"(?P<name>{'|'.join(yield_top_level(target))})"

    for file in vendor.walkfiles(match="*.py"):
        text = file.read_text()
        text = re.sub(  # import {name} => from setupools.extern import {name}
            rf"^(?P<indent>\s*)import\s+{names}(?P<remaining>.*)$",
            rf'\g<indent>from {target}.extern import \g<name>\g<remaining>',
            # ^--- Assumes {name} is not nested.
            #      Otherwise we need to pass `repl=<function>` to split the import
            #      in multiple lines (one import for the parent and one for the child).
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(  # from {name} => from setuptools.extern.{name}
            rf"^(?P<indent>\s*)from\s+{names}(?P<remaining>.* import .*)$",
            rf'\g<indent>from {target}.extern.\g<name>\g<remaining>',
            text,
            flags=re.MULTILINE,
        )
        file.write_text(text)


def repair_namespace(pkg_files):
    # required for zip-packaged setuptools #3084
    if pkg_files.is_dir() and not (pkg_files / "__init__.py").exists():
        (pkg_files / '__init__.py').write_text('')


def rewrite_jaraco_text(pkg_files):
    """
    Rewrite imports in jaraco.text to redirect to vendored copies.
    """
    for file in pkg_files.glob('*.py'):
        text = file.read_text()
        # suppress loading of lorem_ipsum; ref #3072
        text = re.sub(r'^lorem_ipsum.*\n$', '', text, flags=re.M)
        file.write_text(text)


def rewrite_more_itertools(pkg_files: Path):
    """
    Defer import of concurrent.futures. Workaround for #3090.
    """
    more_file = pkg_files.joinpath('more.py')
    if not more_file.exists():
        return
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
    if not pkg_files.exists():
        return

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


def clean(vendor):
    """
    Remove all files out of the vendor directory except the meta
    data (as pip uninstall doesn't support -t).
    """
    ignored = ['vendored.in', 'vendored.txt', 'ruff.toml']
    remove_all(path for path in vendor.glob('*') if path.name not in ignored)


def resolve(vendor, upgrade=False, constraints=None):
    """Document why each indirect dependency is required."""
    constraint_args = ["--constraint", str(constraints)] if constraints else []
    upgrade_args = ["--upgrade"] if upgrade else []
    args = [
        sys.executable,
        '-m',
        'piptools',
        'compile',
        '--strip-extras',
        *upgrade_args,
        *constraint_args,
        '-o',
        str(vendor / 'vendored.txt'),
        str(vendor / 'vendored.in'),
    ]
    subprocess.check_call(args)


def install(vendor, constraints=None):
    constraint_args = ["--constraint", str(constraints)] if constraints else []
    install_args = [
        sys.executable,
        '-m',
        'pip',
        'install',
        *constraint_args,
        '-c',
        str(vendor / 'vendored.txt'),
        '-r',
        str(vendor / 'vendored.in'),
        '-t',
        str(vendor),
    ]
    subprocess.check_call(install_args)
    (vendor / '__init__.py').write_text('')


def update_target(target, upgrade=None, constraints=None):
    vendor = Path(f'{target}/_vendor')
    clean(vendor)
    resolve(vendor, upgrade, constraints)
    install(vendor, constraints)

    # Patches related to issues
    repair_namespace(vendor / 'jaraco')
    repair_namespace(vendor / 'backports')
    rewrite_jaraco_text(vendor / 'jaraco/text')
    rewrite_more_itertools(vendor / "more_itertools")
    rewrite_wheel(vendor / "wheel")

    repair_imports(vendor)  # Required for a vendoring workflow


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
