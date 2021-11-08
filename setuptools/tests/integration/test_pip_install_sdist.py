"""Integration tests for setuptools that focus on building packages via pip.

The idea behind these tests is not to exhaustively check all the possible
combinations of packages, operating systems, supporting libraries, etc, but
rather check a limited number of popular packages and how they interact with
the exposed public API. This way if any change in API is introduced, we hope to
identify backward compatibility problems before publishing a release.

The number of tested packages is purposefully kept small, to minimise duration
and the associated maintenance cost (changes in the way these packages define
their build process may require changes in the tests).
"""
import importlib
import json
import os
import subprocess
import sys
import tarfile
from enum import Enum
from glob import glob
from hashlib import md5
from itertools import chain
from urllib.request import urlopen
from zipfile import ZipFile

import pytest
import tomli as toml
from packaging.requirements import Requirement


pytestmark = pytest.mark.integration


LATEST, = list(Enum("v", "LATEST"))
"""Default version to be checked"""
# There are positive and negative aspects of checking the latest version of the
# packages.
# The main positive aspect is that the latest version might have already
# removed the use of APIs deprecated in previous releases of setuptools.


# Packages to be tested:
# (Please notice the test environment cannot support EVERY library required for
# compiling binary extensions. In Ubuntu/Debian nomenclature, we only assume
# that `build-essential`, `gfortran` and `libopenblas-dev` are installed,
# due to their relevance to the numerical/scientific programming ecosystem)
EXAMPLES = [
    ("numpy", LATEST),  # custom distutils-based commands
    ("pandas", LATEST),  # cython + custom build_ext
    ("sphinx", LATEST),  # custom setup.py
    ("pip", LATEST),  # just in case...
    ("pytest", LATEST),  # uses setuptools_scm
    ("mypy", LATEST),  # custom build_py + ext_modules

    # --- Popular packages: https://hugovk.github.io/top-pypi-packages/ ---
    ("botocore", LATEST),
    ("kiwisolver", "1.3.2"),  # build_ext, version pinned due to setup_requires
    ("brotli", LATEST),  # not in the list but used by urllib3
]


# Some packages have "optional" dependencies that modify their build behaviour
# and are not listed in pyproject.toml, others still use `setup_requires`
EXTRA_BUILD_DEPS = {
    "sphinx": ("babel>=1.3",),
    "kiwisolver": ("cppy>=1.1.0",)
}


# By default, pip will try to build packages in isolation (PEP 517), which
# means it will download the previous stable version of setuptools.
# `pip` flags can avoid that (the version of setuptools under test
# should be the one to be used)
PIP = (sys.executable, "-m", "pip")
SDIST_OPTIONS = (
    "--ignore-installed",
    "--no-build-isolation",
    # We don't need "--no-binary :all:" since we specify the path to the sdist.
    # It also helps with performance, since dependencies can come from wheels.
)
# The downside of `--no-build-isolation` is that pip will not download build
# dependencies. The test script will have to also handle that.


@pytest.fixture(autouse=True)
def _prepare(tmp_path, monkeypatch, request):
    (tmp_path / "lib").mkdir(exist_ok=True)
    download_path = os.getenv("DOWNLOAD_PATH", str(tmp_path))
    os.makedirs(download_path, exist_ok=True)

    # Environment vars used for building some of the packages
    monkeypatch.setenv("USE_MYPYC", "1")

    def _debug_info():
        # Let's provide the maximum amount of information possible in the case
        # it is necessary to debug the tests directly from the CI logs.
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Temporary directory:")
        for entry in chain(tmp_path.glob("*"), tmp_path.glob("lib/*")):
            print(entry)
    request.addfinalizer(_debug_info)


ALREADY_LOADED = ("pytest", "mypy")  # loaded by pytest/pytest-enabler


@pytest.mark.parametrize('package, version', EXAMPLES)
def test_install_sdist(package, version, tmp_path, monkeypatch):
    lib = tmp_path / "lib"
    sdist = retrieve_sdist(package, version, tmp_path)
    deps = build_deps(package, sdist)
    if deps:
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Dependencies:", deps)
        pip_install(*deps, target=lib)

    pip_install(*SDIST_OPTIONS, sdist, target=lib)

    if package in ALREADY_LOADED:
        # We cannot import packages already in use from a different location
        assert (lib / package).exists()
        return

    # Make sure the package was installed correctly
    with monkeypatch.context() as m:
        m.syspath_prepend(str(lib))  # add installed packages to path
        pkg = importlib.import_module(package)
        if hasattr(pkg, '__version__'):
            print(pkg.__version__)
        for path in getattr(pkg, '__path__', []):
            assert os.path.abspath(path).startswith(os.path.abspath(tmp_path))


# ---- Helper Functions ----


def pip_install(*args, target):
    """Install packages in the ``target`` directory"""
    cmd = [*PIP, 'install', '--target', str(target), *args]
    env = {**os.environ, "PYTHONPATH": str(target)}
    # ^-- use libs installed in the target for build, but keep
    #     compiling/build-related env variables

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=env
        )
    except subprocess.CalledProcessError as ex:
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Command", repr(ex.cmd), "failed with code", ex.returncode)
        print(ex.stdout)
        print(ex.stderr)
        raise


def retrieve_sdist(package, version, tmp_path):
    """Either use cached sdist file or download it from PyPI"""
    # `pip download` cannot be used due to
    # https://github.com/pypa/pip/issues/1884
    # https://discuss.python.org/t/pep-625-file-name-of-a-source-distribution/4686
    # We have to find the correct distribution file and download it
    download_path = os.getenv("DOWNLOAD_PATH", str(tmp_path))
    dist = retrieve_pypi_sdist_metadata(package, version)

    # Remove old files to prevent cache to grow indefinitely
    for file in glob(os.path.join(download_path, f"{package}*")):
        if dist["filename"] != file:
            os.unlink(file)

    dist_file = os.path.join(download_path, dist["filename"])
    if not os.path.exists(dist_file):
        download(dist["url"], dist_file, dist["md5_digest"])
    return dist_file


def retrieve_pypi_sdist_metadata(package, version):
    # https://warehouse.pypa.io/api-reference/json.html
    id_ = package if version is LATEST else f"{package}/{version}"
    with urlopen(f"https://pypi.org/pypi/{id_}/json") as f:
        metadata = json.load(f)

    if metadata["info"]["yanked"]:
        raise ValueError(f"Release for {package} {version} was yanked")

    version = metadata["info"]["version"]
    release = metadata["releases"][version]
    dists = [d for d in release if d["packagetype"] == "sdist"]
    if len(dists) == 0:
        raise ValueError(f"No sdist found for {package} {version}")

    for dist in dists:
        if dist["filename"].endswith(".tar.gz"):
            return dist

    # Not all packages are publishing tar.gz, e.g. numpy==1.21.4
    return dist


def download(url, dest, md5_digest):
    with urlopen(url) as f:
        data = f.read()

    assert md5(data).hexdigest() == md5_digest

    with open(dest, "wb") as f:
        f.write(data)

    assert os.path.exists(dest)


IN_TEST_VENV = ("setuptools", "wheel", "packaging")
"""Don't re-install"""


def build_deps(package, sdist_file):
    """Find out what are the build dependencies for a package.

    We need to "manually" install them, since pip will not install build
    deps with `--no-build-isolation`.
    """
    archive = Archive(sdist_file)
    pyproject = _read_pyproject(archive)

    info = toml.loads(pyproject)
    deps = info.get("build-system", {}).get("requires", [])
    deps += EXTRA_BUILD_DEPS.get(package, [])
    # Remove setuptools from requirements (and deduplicate)
    requirements = {Requirement(d).name: d for d in deps}
    return [v for k, v in requirements.items() if k not in IN_TEST_VENV]


def _read_pyproject(archive):
    for member in archive:
        if os.path.basename(archive.get_name(member)) == "pyproject.toml":
            return archive.get_content(member)
    return ""


class Archive:
    """Compatibility layer for ZipFile/Info and TarFile/Info"""
    def __init__(self, filename):
        self._filename = filename
        if filename.endswith("tar.gz"):
            self._obj = tarfile.open(filename, "r:gz")
        elif filename.endswith("zip"):
            self._obj = ZipFile(filename)
        else:
            raise ValueError(f"{filename} doesn't seem to be a zip or tar.gz")

    def __iter__(self):
        if hasattr(self._obj, "infolist"):
            return iter(self._obj.infolist())
        return iter(self._obj)

    def get_name(self, zip_or_tar_info):
        if hasattr(zip_or_tar_info, "filename"):
            return zip_or_tar_info.filename
        return zip_or_tar_info.name

    def get_content(self, zip_or_tar_info):
        if hasattr(self._obj, "extractfile"):
            content = self._obj.extractfile(zip_or_tar_info)
            if content is None:
                msg = f"Invalid {zip_or_tar_info.name} in {self._filename}"
                raise ValueError(msg)
            return str(content.read(), "utf-8")
        return str(self._obj.read(zip_or_tar_info), "utf-8")
