"""A PEP 517 interface to setuptools

Previously, when a user or a command line tool (let's call it a "frontend")
needed to make a request of setuptools to take a certain action, for
example, generating a list of installation requirements, the frontend would
would call "setup.py egg_info" or "setup.py bdist_wheel" on the command line.

PEP 517 defines a different method of interfacing with setuptools. Rather
than calling "setup.py" directly, the frontend should:

  1. Set the current directory to the directory with a setup.py file
  2. Import this module into a safe python interpreter (one in which
     setuptools can potentially set global variables or crash hard).
  3. Call one of the functions defined in PEP 517.

What each function does is defined in PEP 517. However, here is a "casual"
definition of the functions (this definition should not be relied on for
bug reports or API stability):

  - `build_wheel`: build a wheel in the folder and return the basename
  - `get_requires_for_build_wheel`: get the `setup_requires` to build
  - `prepare_metadata_for_build_wheel`: get the `install_requires`
  - `build_sdist`: build an sdist in the folder and return the basename
  - `get_requires_for_build_sdist`: get the `setup_requires` to build

Again, this is not a formal definition! Just a "taste" of the module.
"""

import os
import sys
import tokenize
import shutil
import contextlib
import tempfile
import warnings
from itertools import chain
from uuid import uuid4

import setuptools
import distutils
from ._reqs import parse_strings

__all__ = ['get_requires_for_build_sdist',
           'get_requires_for_build_wheel',
           'prepare_metadata_for_build_wheel',
           'build_wheel',
           'build_sdist',
           '__legacy__']


@contextlib.contextmanager
def no_install_setup_requires():
    """Temporarily disable installing setup_requires

    Under PEP 517, the backend reports build dependencies to the frontend,
    and the frontend is responsible for ensuring they're installed.
    So setuptools (acting as a backend) should not try to install them.
    """
    orig = setuptools._install_setup_requires
    setuptools._install_setup_requires = lambda attrs: None
    try:
        yield
    finally:
        setuptools._install_setup_requires = orig


def _get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def _file_with_extension(directory, extension):
    matching = (
        f for f in os.listdir(directory)
        if f.endswith(extension)
    )
    try:
        file, = matching
    except ValueError:
        raise ValueError(
            'No distribution was found. Ensure that `setup.py` '
            'is not empty and that it calls `setup()`.')
    return file


@contextlib.contextmanager
def suppress_known_deprecation():
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'setup.py install is deprecated')
        yield


@contextlib.contextmanager
def _patch_distutils_core():
    """Make sure distutils.core uses the latest enhancements"""
    orig_exec = exec
    if hasattr(distutils.core, "run_commands"):
        yield  # do nothing, already using the improved version of distutils
        return

    def _exec(code, global_vars):
        try:
            fid, tmp = tempfile.mkstemp(suffix=f"{uuid4()}-setup.py", text=False)
            os.close(fid)  # Ignore the low level API
            with open(tmp, "wb") as f:
                f.write(code)
            with tokenize.open(tmp) as f:
                code = f.read().replace(r'\r\n', r'\n')
        finally:
            os.remove(tmp)
        orig_exec(code, {**global_vars, "__name__": "__main__"})

    def _run_commands(dist):
        try:
            dist.run_commands()
        except Exception as ex:
            raise SystemExit("error:" + str(ex))

    distutils.core.exec = _exec
    distutils.core.run_commands = _run_commands
    try:
        yield
    finally:
        distutils.core.exec = orig_exec
        del distutils.core.run_commands


class _BuildMetaBackend(object):

    def _fix_config(self, config_settings):
        config_settings = config_settings or {}
        config_settings.setdefault('--global-option', [])
        return config_settings

    def _get_dist(self, setup_script="setup.py"):
        """Retrieve a distribution object already configured."""

        if os.path.exists(setup_script) and os.stat(setup_script).st_size > 0:
            with no_install_setup_requires(), _patch_distutils_core():
                dist = distutils.core.run_setup(setup_script, stop_after="init")
        else:
            dist = setuptools.dist.Distribution()

        dist.parse_config_files()
        dist.finalize_options()
        return dist

    def _get_build_requires(self, config_settings, requirements):
        dist = self._get_dist()
        parsed = chain(parse_strings(requirements),
                       parse_strings(dist.setup_requires))
        deduplicated = {r.key: str(r) for r in parsed}
        return list(deduplicated.values())

    def run_command(self, *args):
        # Note that we can reuse our build directory between calls
        # Correctness comes first, then optimization later
        dist = self._get_dist()
        dist.script_name = sys.argv[0]
        dist.script_args = args
        dist.parse_command_line()

        with _patch_distutils_core():
            return distutils.core.run_commands(dist)

    def get_requires_for_build_wheel(self, config_settings=None):
        config_settings = self._fix_config(config_settings)
        return self._get_build_requires(
            config_settings, requirements=['wheel'])

    def get_requires_for_build_sdist(self, config_settings=None):
        config_settings = self._fix_config(config_settings)
        return self._get_build_requires(config_settings, requirements=[])

    def prepare_metadata_for_build_wheel(self, metadata_directory,
                                         config_settings=None):
        self.run_command('dist_info', '--egg-base', metadata_directory)

        dist_info_directory = metadata_directory
        while True:
            dist_infos = [f for f in os.listdir(dist_info_directory)
                          if f.endswith('.dist-info')]

            if (
                len(dist_infos) == 0 and
                len(_get_immediate_subdirectories(dist_info_directory)) == 1
            ):

                dist_info_directory = os.path.join(
                    dist_info_directory, os.listdir(dist_info_directory)[0])
                continue

            assert len(dist_infos) == 1
            break

        # PEP 517 requires that the .dist-info directory be placed in the
        # metadata_directory. To comply, we MUST copy the directory to the root
        if dist_info_directory != metadata_directory:
            shutil.move(
                os.path.join(dist_info_directory, dist_infos[0]),
                metadata_directory)
            shutil.rmtree(dist_info_directory, ignore_errors=True)

        return dist_infos[0]

    def _build_with_temp_dir(self, setup_command, result_extension,
                             result_directory, config_settings):
        config_settings = self._fix_config(config_settings)
        result_directory = os.path.abspath(result_directory)

        # Build in a temporary directory, then copy to the target.
        os.makedirs(result_directory, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=result_directory) as tmp_dist_dir:
            self.run_command(
                *setup_command, "--dist-dir", tmp_dist_dir,
                *config_settings["--global-option"]
            )

            result_basename = _file_with_extension(
                tmp_dist_dir, result_extension)
            result_path = os.path.join(result_directory, result_basename)
            if os.path.exists(result_path):
                # os.rename will fail overwriting on non-Unix.
                os.remove(result_path)
            os.rename(os.path.join(tmp_dist_dir, result_basename), result_path)

        return result_basename

    def build_wheel(self, wheel_directory, config_settings=None,
                    metadata_directory=None):
        with suppress_known_deprecation():
            return self._build_with_temp_dir(['bdist_wheel'], '.whl',
                                             wheel_directory, config_settings)

    def build_sdist(self, sdist_directory, config_settings=None):
        return self._build_with_temp_dir(['sdist', '--formats', 'gztar'],
                                         '.tar.gz', sdist_directory,
                                         config_settings)


class _BuildMetaLegacyBackend(_BuildMetaBackend):
    """Compatibility backend for setuptools

    This is a version of setuptools.build_meta that endeavors
    to maintain backwards
    compatibility with pre-PEP 517 modes of invocation. It
    exists as a temporary
    bridge between the old packaging mechanism and the new
    packaging mechanism,
    and will eventually be removed.
    """

    def run_command(self, *args):
        # In order to maintain compatibility with scripts assuming that
        # the setup.py script is in a directory on the PYTHONPATH, inject
        # '' into sys.path. (pypa/setuptools#1642)
        sys_path = list(sys.path)           # Save the original path

        setup_script = "setup.py"
        if not os.path.exists(setup_script) or os.stat(setup_script).st_size == 0:
            msg = f"__legacy__ backend conflicts with empty/missing {setup_script!r}"
            warnings.warn(msg, setuptools.SetuptoolsDeprecationWarning)
            return super().run_command(*args)

        script_dir = os.path.dirname(os.path.abspath(setup_script))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Some setup.py scripts (e.g. in pygame and numpy) use sys.argv[0] to
        # get the directory of the source code. They expect it to refer to the
        # setup.py script. ==> This is already handled in distutils.core
        try:
            with no_install_setup_requires(), _patch_distutils_core():
                distutils.core.run_setup(setup_script, args)
        finally:
            # While PEP 517 frontends should be calling each hook in a fresh
            # subprocess according to the standard (and thus it should not be
            # strictly necessary to restore the old sys.path), we'll restore
            # the original path so that the path manipulation does not persist
            # within the hook after run_setup is called.
            sys.path[:] = sys_path


# The primary backend
_BACKEND = _BuildMetaBackend()

get_requires_for_build_wheel = _BACKEND.get_requires_for_build_wheel
get_requires_for_build_sdist = _BACKEND.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = _BACKEND.prepare_metadata_for_build_wheel
build_wheel = _BACKEND.build_wheel
build_sdist = _BACKEND.build_sdist


# The legacy backend
__legacy__ = _BuildMetaLegacyBackend()
