import os
import re
import sys
import shutil
import subprocess
import venv
import string
from tempfile import TemporaryDirectory

from paver.easy import info, task, path as Path


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
    remove_all(vendor.glob('*.dist-info'))
    remove_all(vendor.glob('*.egg-info'))
    remove_all(vendor.glob('six.py'))
    remove_ini2toml_extras(vendor)
    (vendor / '__init__.py').write_text('')
    (vendor / 'bin').rmtree()


def update_pkg_resources():
    vendor = Path('pkg_resources/_vendor')
    install(vendor)
    rewrite_packaging(vendor / 'packaging', 'pkg_resources.extern')


def update_setuptools():
    vendor = Path('setuptools/_vendor')
    install(vendor)
    install_validate_pyproject(vendor)
    rewrite_packaging(vendor / 'packaging', 'setuptools.extern')


def install_validate_pyproject(vendor):
    """``validate-pyproject`` can be vendorized to remove all dependencies"""
    req = next(
        (x for x in (vendor / "vendored.txt").lines() if 'validate-pyproject' in x),
        "validate-pyproject[all]"
    )

    pkg, _, _ = req.strip(string.whitespace + "#").partition("#")
    pkg = pkg.strip()

    opts = {}
    if sys.version_info[:2] >= (3, 10):
        opts["ignore_cleanup_errors"] = True

    with TemporaryDirectory(**opts) as tmp:
        venv.create(tmp, with_pip=True)
        path = os.pathsep.join(Path(tmp).glob("*"))
        venv_python = shutil.which("python", path=path)
        info(f"Temporarily installing {pkg!r}...")
        subprocess.check_call([venv_python, "-m", "pip", "install", pkg])
        cmd = [
            venv_python,
            "-m",
            "validate_pyproject.vendoring",
            "--output-dir",
            str(vendor / "_validate_pyproject"),
            "--enable-plugins",
            "setuptools",
            "distutils",
            "--very-verbose"
        ]
        subprocess.check_output(cmd)
        info(f"{pkg!r} vendorized")


def remove_ini2toml_extras(vendor):
    """Remove unnecessary files from `ini2toml`"""
    unecessary = [
        "ini2toml/__main__.py",
        "ini2toml/api.py",
        "ini2toml/cli.py",
        "ini2toml/drivers/configupdater.py",
        "ini2toml/drivers/full_toml.py",
        "ini2toml/drivers/lite_toml.py",
        "ini2toml/plugins/coverage.py",
        "ini2toml/plugins/isort.py",
        "ini2toml/plugins/mypy.py",
        "ini2toml/plugins/profile_independent_tasks.py",
        "ini2toml/plugins/pytest.py",
        "ini2toml/translator.py",
    ]
    remove_all(vendor / file for file in unecessary)
