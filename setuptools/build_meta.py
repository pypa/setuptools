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
  - `build_editable`: build a wheel containing a .pth file and dist-info
                      metadata, and return the basename (PEP 660)
  - `get_requires_for_build_wheel`: get the `setup_requires` to build
  ` `prepare_metadata_for_build_editable`: get the `install_requires`

Again, this is not a formal definition! Just a "taste" of the module.
"""

import io
import os
import sys
import tokenize
import shutil
import contextlib
import tempfile
import warnings
import zipfile
import base64
import textwrap
import hashlib
import csv

import setuptools
import setuptools.command.egg_info
import distutils

import pkg_resources
from pkg_resources import parse_requirements, safe_name, safe_version

__all__ = ['get_requires_for_build_sdist',
           'get_requires_for_build_wheel',
           'get_requires_for_build_editable'
           'prepare_metadata_for_build_wheel',
           'prepare_metadata_for_build_editable',
           'build_wheel',
           'build_sdist',
           'build_editable',
           '__legacy__',
           'SetupRequirementsError']


class SetupRequirementsError(BaseException):
    def __init__(self, specifiers):
        self.specifiers = specifiers


class Distribution(setuptools.dist.Distribution):
    def fetch_build_eggs(self, specifiers):
        specifier_list = list(map(str, parse_requirements(specifiers)))

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


class _egg_info_EditableShim(setuptools.command.egg_info.egg_info):
    _captured_instance = None

    def finalize_options(self):
        super().finalize_options()
        self.__class__._captured_instance = self

    @classmethod
    @contextlib.contextmanager
    def patch(cls):
        orig = setuptools.command.egg_info.egg_info
        setuptools.command.egg_info.egg_info = cls
        try:
            yield
        finally:
            setuptools.command.egg_info.egg_info = orig


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


def _urlsafe_b64encode(data):
    """urlsafe_b64encode without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _add_wheel_record(archive, dist_info):
    """Add the wheel RECORD manifest."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=',', quotechar='"', lineterminator='\n')
    for f in archive.namelist():
        data = archive.read(f)
        size = len(data)
        digest = hashlib.sha256(data).digest()
        digest = "sha256=" + (_urlsafe_b64encode(digest).decode("ascii"))
        writer.writerow((f, digest, size))
    record_path = os.path.join(dist_info, "RECORD")
    archive.writestr(record_path, buffer.read())


class _BuildMetaBackend(object):

    def _fix_config(self, config_settings):
        config_settings = config_settings or {}
        config_settings.setdefault('--global-option', [])
        return config_settings

    def _get_build_requires(self, config_settings, requirements):
        config_settings = self._fix_config(config_settings)

        sys.argv = sys.argv[:1] + ['egg_info'] + \
            config_settings["--global-option"]
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
        config_settings = self._fix_config(config_settings)
        return self._get_build_requires(
            config_settings, requirements=['wheel'])

    def get_requires_for_build_sdist(self, config_settings=None):
        config_settings = self._fix_config(config_settings)
        return self._get_build_requires(config_settings, requirements=[])

    def prepare_metadata_for_build_wheel(self, metadata_directory,
                                         config_settings=None):
        sys.argv = sys.argv[:1] + [
            'dist_info', '--egg-base', metadata_directory]
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
        config_settings = self._fix_config(config_settings)
        result_directory = os.path.abspath(result_directory)

        # Build in a temporary directory, then copy to the target.
        os.makedirs(result_directory, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=result_directory) as tmp_dist_dir:
            sys.argv = (sys.argv[:1] + setup_command +
                        ['--dist-dir', tmp_dist_dir] +
                        config_settings["--global-option"])
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

    def build_editable(self, wheel_directory, config_settings=None,
                       metadata_directory=None):
        config_settings = self._fix_config(config_settings)

        sys.argv = [*sys.argv[:1], 'dist_info']
        with no_install_setup_requires(), _egg_info_EditableShim.patch():
            self.run_setup()
        # HACK: to get the distribution's location we'll have to capture the
        # egg_info instance created by dist_info. It'd be even more difficult
        # to statically recalcuate the location (i.e. the proper way) AFAICT.
        egg_info = _egg_info_EditableShim._captured_instance
        dist_info = egg_info.egg_name + '.dist-info'
        dist_info_path = os.path.join(os.getcwd(), egg_info.egg_info)
        dist_info_path = dist_info_path[:-len('.egg-info')] + '.dist-info'
        location = os.path.join(os.getcwd(), egg_info.egg_base)

        sys.argv = [
            *sys.argv[:1], 'build_ext', '--inplace',
            *config_settings['--global-option']
        ]
        with no_install_setup_requires():
            self.run_setup()

        metadata = pkg_resources.PathMetadata(location, dist_info_path)
        dist = pkg_resources.DistInfoDistribution.from_location(
            location, dist_info, metadata=metadata
        )
        # Seems like the distribution name and version attributes aren't always
        # 100% normalized ...
        dist_name = safe_name(dist.project_name).replace("-", "_")
        version = safe_version(dist.version).replace("-", "_")
        wheel_name = f'{dist_name}-{version}-ed.py3-none-any.whl'
        wheel_path = os.path.join(wheel_directory, wheel_name)
        with zipfile.ZipFile(wheel_path, 'w') as archive:
            archive.writestr(f'{dist.project_name}.pth', location)
            for file in os.scandir(dist_info_path):
                with open(file.path, encoding='utf-8') as metadata:
                    zip_filename = os.path.relpath(file.path, location)
                    archive.writestr(zip_filename, metadata.read())

            archive.writestr(
                os.path.join(dist_info, 'WHEEL'),
                textwrap.dedent(f"""\
                    Wheel-Version: 1.0
                    Generator: setuptools ({setuptools.__version__})
                    Root-Is-Purelib: false
                    Tag: ed.py3-none-any
                """)
            )
            _add_wheel_record(archive, dist_info)

        return os.path.basename(wheel_path)


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
# Fortunately we can just reuse the wheel hook for editables in this case.
get_requires_for_build_editable = _BACKEND.get_requires_for_build_wheel
prepare_metadata_for_build_wheel = _BACKEND.prepare_metadata_for_build_wheel
# Ditto reuse of wheel's equivalent.
prepare_metadata_for_build_editable = _BACKEND.prepare_metadata_for_build_wheel
build_wheel = _BACKEND.build_wheel
build_sdist = _BACKEND.build_sdist
build_editable = _BACKEND.build_editable


# The legacy backend
__legacy__ = _BuildMetaLegacyBackend()
