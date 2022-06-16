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

import io
import os
import shlex
import sys
import tokenize
import shutil
import contextlib
import tempfile
import warnings
from typing import Dict, List, Optional, Union

import setuptools
import distutils
from ._reqs import parse_strings
from distutils.util import strtobool


__all__ = ['get_requires_for_build_sdist',
           'get_requires_for_build_wheel',
           'prepare_metadata_for_build_wheel',
           'build_wheel',
           'build_sdist',
           'get_requires_for_build_editable',
           'build_editable',
           '__legacy__',
           'SetupRequirementsError']


class SetupRequirementsError(BaseException):
    def __init__(self, specifiers):
        self.specifiers = specifiers


class Distribution(setuptools.dist.Distribution):
    def fetch_build_eggs(self, specifiers):
        specifier_list = list(parse_strings(specifiers))

        raise SetupRequirementsError(specifier_list)

    @classmethod
    @contextlib.contextmanager
    def patch(cls):
        """
        Replace
        distutils.dist.Distribution with this class
        for the duration of this context.
        """
        orig = distutils.core.Distribution
        distutils.core.Distribution = cls
        try:
            yield
        finally:
            distutils.core.Distribution = orig


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


def _open_setup_script(setup_script):
    if not os.path.exists(setup_script):
        # Supply a default setup.py
        return io.StringIO(u"from setuptools import setup; setup()")

    return getattr(tokenize, 'open', open)(setup_script)


@contextlib.contextmanager
def suppress_known_deprecation():
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'setup.py install is deprecated')
        yield


_ConfigSettings = Optional[Dict[str, Union[str, List[str], None]]]
"""
Currently the user can run::

    pip install -e . --config-settings key=value
    python -m build -C--key=value -C key=value

- pip will pass both key and value as strings and overwriting repeated keys
  (pypa/pip#11059).
- build will accumulate values associated with repeated keys in a list.
  It will also accept keys with no associated value.
  This means that an option passed by build can be ``str | list[str] | None``.
- PEP 517 specifies that ``config_settings`` is an optional dict.
"""


class _ConfigSettingsTranslator:
    """Translate ``config_settings`` into distutils-style command arguments.
    Only a limited number of options is currently supported.
    """

    def _global_args(self, config_settings: _ConfigSettings) -> List[str]:
        """
        If the user specify ``log-level``, it should be applied to all commands.

        >>> fn = _ConfigSettingsTranslator()._global_args
        >>> fn(None)
        []
        >>> fn({"log-level": "WARNING"})
        ['-q']
        >>> fn({"log-level": "DEBUG"})
        ['-vv']
        >>> fn({"log-level": None})
        Traceback (most recent call last):
           ...
        ValueError: Invalid value for log-level: None.
        Try one of: ['WARNING', 'INFO', 'DEBUG'].
        """
        log_levels = {"WARNING": "-q", "INFO": "-v", "DEBUG": "-vv"}
        cfg = config_settings or {}
        if "log-level" in cfg:
            level = cfg["log-level"]
            if level not in log_levels:
                msg = f"Invalid value for log-level: {level!r}."
                raise ValueError(msg + f"\nTry one of: {list(log_levels.keys())}.")
            assert isinstance(level, str)
            return [log_levels[level]]
        return []

    def __dist_info_args(self, config_settings: _ConfigSettings) -> List[str]:
        """
        The ``dist_info`` command accepts ``tag-date`` and ``tag-build``.

        .. warning::
           We cannot use this yet as it requires the ``sdist`` and ``bdist_wheel``
           commands run in ``build_sdist`` and ``build_wheel`` to re-use the egg-info
           directory created in ``prepare_metadata_for_build_wheel``.

        >>> fn = _ConfigSettingsTranslator()._ConfigSettingsTranslator__dist_info_args
        >>> fn(None)
        []
        >>> fn({"tag-date": "False"})
        ['--no-date']
        >>> fn({"tag-date": None})
        ['--no-date']
        >>> fn({"tag-date": "true", "tag-build": ".a"})
        ['--tag-date', '--tag-build', '.a']
        """
        cfg = config_settings or {}
        args: List[str] = []
        if "tag-date" in cfg:
            val = strtobool(str(cfg["tag-date"] or "false"))
            args.append("--tag-date" if val else "--no-date")
        if "tag-build" in cfg:
            args.extend(["--tag-build", str(cfg["tag-build"])])
        return args

    def _editable_args(self, config_settings: _ConfigSettings) -> List[str]:
        """
        The ``editable_wheel`` command accepts ``editable-mode=strict``.

        >>> fn = _ConfigSettingsTranslator()._editable_args
        >>> fn(None)
        []
        >>> fn({"editable-mode": "strict"})
        ['--strict']
        >>> fn({"editable-mode": "other"})
        Traceback (most recent call last):
           ...
        ValueError: Invalid value for editable-mode: 'other'. Try: 'strict'.
        """
        cfg = config_settings or {}
        if "editable-mode" not in cfg:
            return []
        mode = cfg["editable-mode"]
        if mode != "strict":
            msg = f"Invalid value for editable-mode: {mode!r}. Try: 'strict'."
            raise ValueError(msg)
        return ["--strict"]

    def _arbitrary_args(self, config_settings: _ConfigSettings) -> List[str]:
        """
        Users may expect to pass arbitrary lists of arguments to a command
        via "--global-option" (example provided in PEP 517 of a "escape hatch").

        >>> fn = _ConfigSettingsTranslator()._arbitrary_args
        >>> fn(None)
        []
        >>> fn({})
        []
        >>> fn({'--global-option': 'foo'})
        ['foo']
        >>> fn({'--global-option': ['foo']})
        ['foo']
        >>> fn({'--global-option': 'foo'})
        ['foo']
        >>> fn({'--global-option': 'foo bar'})
        ['foo', 'bar']
        """
        cfg = config_settings or {}
        opts = cfg.get("--global-option") or []
        return shlex.split(opts) if isinstance(opts, str) else opts


class _BuildMetaBackend(_ConfigSettingsTranslator):
    def _get_build_requires(self, config_settings, requirements):
        sys.argv = [*sys.argv[:1], "egg_info", *self._arbitrary_args(config_settings)]
        try:
            with Distribution.patch():
                self.run_setup()
        except SetupRequirementsError as e:
            requirements += e.specifiers

        return requirements

    def run_setup(self, setup_script='setup.py'):
        # Note that we can reuse our build directory between calls
        # Correctness comes first, then optimization later
        __file__ = setup_script
        __name__ = '__main__'

        with _open_setup_script(__file__) as f:
            code = f.read().replace(r'\r\n', r'\n')

        exec(compile(code, __file__, 'exec'), locals())

    def get_requires_for_build_wheel(self, config_settings=None):
        return self._get_build_requires(config_settings, requirements=['wheel'])

    def get_requires_for_build_sdist(self, config_settings=None):
        return self._get_build_requires(config_settings, requirements=[])

    def prepare_metadata_for_build_wheel(self, metadata_directory,
                                         config_settings=None):
        sys.argv = [*sys.argv[:1], 'dist_info', '--output-dir', metadata_directory]
        with no_install_setup_requires():
            self.run_setup()

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
        args = self._arbitrary_args(config_settings)
        result_directory = os.path.abspath(result_directory)

        # Build in a temporary directory, then copy to the target.
        os.makedirs(result_directory, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=result_directory) as tmp_dist_dir:
            sys.argv = [
                *sys.argv[:1], *setup_command, "--dist-dir", tmp_dist_dir, *args
            ]
            with no_install_setup_requires():
                self.run_setup()

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

    # PEP660 hooks:
    # build_editable
    # get_requires_for_build_editable
    # prepare_metadata_for_build_editable
    def build_editable(
        self, wheel_directory, config_settings=None, metadata_directory=None
    ):
        # XXX can or should we hide our editable_wheel command normally?
        return self._build_with_temp_dir(
            ["editable_wheel", "--dist-info-dir", metadata_directory],
            ".whl", wheel_directory, config_settings
        )

    def get_requires_for_build_editable(self, config_settings=None):
        return self.get_requires_for_build_wheel(config_settings)

    def prepare_metadata_for_build_editable(self, metadata_directory,
                                            config_settings=None):
        return self.prepare_metadata_for_build_wheel(
            metadata_directory, config_settings
        )


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
    def run_setup(self, setup_script='setup.py'):
        # In order to maintain compatibility with scripts assuming that
        # the setup.py script is in a directory on the PYTHONPATH, inject
        # '' into sys.path. (pypa/setuptools#1642)
        sys_path = list(sys.path)           # Save the original path

        script_dir = os.path.dirname(os.path.abspath(setup_script))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Some setup.py scripts (e.g. in pygame and numpy) use sys.argv[0] to
        # get the directory of the source code. They expect it to refer to the
        # setup.py script.
        sys_argv_0 = sys.argv[0]
        sys.argv[0] = setup_script

        try:
            super(_BuildMetaLegacyBackend,
                  self).run_setup(setup_script=setup_script)
        finally:
            # While PEP 517 frontends should be calling each hook in a fresh
            # subprocess according to the standard (and thus it should not be
            # strictly necessary to restore the old sys.path), we'll restore
            # the original path so that the path manipulation does not persist
            # within the hook after run_setup is called.
            sys.path[:] = sys_path
            sys.argv[0] = sys_argv_0


# The primary backend
_BACKEND = _BuildMetaBackend()

get_requires_for_build_wheel = _BACKEND.get_requires_for_build_wheel
get_requires_for_build_sdist = _BACKEND.get_requires_for_build_sdist
get_requires_for_build_editable = _BACKEND.get_requires_for_build_editable
prepare_metadata_for_build_wheel = _BACKEND.prepare_metadata_for_build_wheel
prepare_metadata_for_build_editable = _BACKEND.prepare_metadata_for_build_editable
build_wheel = _BACKEND.build_wheel
build_sdist = _BACKEND.build_sdist
build_editable = _BACKEND.build_editable


# The legacy backend
__legacy__ = _BuildMetaLegacyBackend()
