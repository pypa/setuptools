"""Extensions to the 'distutils' for large or complex distributions"""
# mypy: disable_error_code=override
# Command.reinitialize_command has an extra **kw param that distutils doesn't have
# Can't disable on the exact line because distutils doesn't exists on Python 3.12
# and mypy isn't aware of distutils_hack, causing distutils.core.Command to be Any,
# and a [unused-ignore] to be raised on 3.12+

from __future__ import annotations

import functools
import os
import sys
from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, TypeVar, overload

sys.path.extend(((vendor_path := os.path.join(os.path.dirname(os.path.dirname(__file__)), 'setuptools', '_vendor')) not in sys.path) * [vendor_path])  # fmt: skip
# workaround for #4476
sys.modules.pop('backports', None)

import _distutils_hack.override  # noqa: F401

from . import logging, monkey
from ._path import StrPath
from .depends import Require
from .discovery import PackageFinder, PEP420PackageFinder
from .dist import Distribution
from .extension import Extension
from .version import __version__ as __version__
from .warnings import SetuptoolsDeprecationWarning

import distutils.core

__all__ = [
    'setup',
    'Distribution',
    'Command',
    'Extension',
    'Require',
    'SetuptoolsDeprecationWarning',
    'find_packages',
    'find_namespace_packages',
]

_CommandT = TypeVar("_CommandT", bound="_Command")

bootstrap_install_from = None

find_packages = PackageFinder.find
find_namespace_packages = PEP420PackageFinder.find


def _install_setup_requires(attrs):
    # Note: do not use `setuptools.Distribution` directly, as
    # our PEP 517 backend patch `distutils.core.Distribution`.
    class MinimalDistribution(distutils.core.Distribution):
        """
        A minimal version of a distribution for supporting the
        fetch_build_eggs interface.
        """

        def __init__(self, attrs: Mapping[str, object]) -> None:
            _incl = 'dependency_links', 'setup_requires'
            filtered = {k: attrs[k] for k in set(_incl) & set(attrs)}
            super().__init__(filtered)
            # Prevent accidentally triggering discovery with incomplete set of attrs
            self.set_defaults._disable()

        def _get_project_config_files(self, filenames=None):
            """Ignore ``pyproject.toml``, they are not related to setup_requires"""
            try:
                cfg, _toml = super()._split_standard_project_metadata(filenames)
            except Exception:
                return filenames, ()
            return cfg, ()

        def finalize_options(self):
            """
            Disable finalize_options to avoid building the working set.
            Ref #2158.
            """

    dist = MinimalDistribution(attrs)

    # Honor setup.cfg's options.
    dist.parse_config_files(ignore_option_errors=True)
    if dist.setup_requires:
        _fetch_build_eggs(dist)


def _fetch_build_eggs(dist: Distribution):
    try:
        dist.fetch_build_eggs(dist.setup_requires)
    except Exception as ex:
        msg = """
        It is possible a package already installed in your system
        contains an version that is invalid according to PEP 440.
        You can try `pip install --use-pep517` as a workaround for this problem,
        or rely on a new virtual environment.

        If the problem refers to a package that is not installed yet,
        please contact that package's maintainers or distributors.
        """
        if "InvalidVersion" in ex.__class__.__name__:
            if hasattr(ex, "add_note"):
                ex.add_note(msg)  # PEP 678
            else:
                dist.announce(f"\n{msg}\n")
        raise


if TYPE_CHECKING:
    from typing_extensions import Never

    from setuptools.command.build_clib import _BuildInfo

    _DistributionT = TypeVar(
        "_DistributionT",
        bound=distutils.core.Distribution,
        default=Distribution,
    )

    def setup(
        *,
        # Attributes from distutils.dist.DistributionMetadata.set_*
        # These take priority over attributes from distutils.dist.DistributionMetadata.__init__
        keywords: str | Iterable[str] = ...,
        platforms: str | Iterable[str] = ...,
        classifiers: str | Iterable[str] = ...,
        requires: Iterable[str] = ...,
        provides: Iterable[str] = ...,
        obsoletes: Iterable[str] = ...,
        # Attributes from distutils.dist.DistributionMetadata.__init__
        # These take priority over attributes from distutils.dist.Distribution.__init__
        name: str | None = None,
        version: str | None = None,
        author: str | None = None,
        author_email: str | None = None,
        maintainer: str | None = None,
        maintainer_email: str | None = None,
        url: str | None = None,
        license: str | None = None,
        description: str | None = None,
        long_description: str | None = None,
        download_url: str | None = None,
        # Attributes from distutils.dist.Distribution.__init__ (except self.metadata)
        # These take priority over attributes from distutils.dist.Distribution.display_option_names
        verbose=True,
        dry_run=False,
        help=False,
        cmdclass: dict[str, type[_Command]] = {},
        command_packages: str | list[str] | None = None,
        script_name: StrPath
        | None = ...,  # default is actually set in distutils.core.setup
        script_args: list[str]
        | None = ...,  # default is actually set in distutils.core.setup
        command_options: dict[str, dict[str, tuple[str, str]]] = {},
        packages: list[str] | None = None,
        package_dir: Mapping[str, str] | None = None,
        py_modules: list[str] | None = None,
        libraries: list[tuple[str, _BuildInfo]] | None = None,
        headers: list[str] | None = None,
        ext_modules: Sequence[distutils.core.Extension] | None = None,
        ext_package: str | None = None,
        include_dirs: list[str] | None = None,
        extra_path=None,
        scripts: list[str] | None = None,
        data_files: list[tuple[str, list[str]]] | None = None,
        password: str = '',
        command_obj: dict[str, _Command] = {},
        have_run: dict[str, bool] = {},
        # kwargs used directly in distutils.dist.Distribution.__init__
        options: Mapping[str, Mapping[str, str]] | None = None,
        licence: Never = ...,  # Deprecated
        # Attributes from distutils.dist.Distribution.display_option_names
        # (this can more easily be copied from the `if TYPE_CHECKING` block)
        help_commands: bool = False,
        fullname: str | Literal[False] = False,
        contact: str | Literal[False] = False,
        contact_email: str | Literal[False] = False,
        # kwargs used directly in setuptools.dist.Distribution.__init__
        # and attributes from setuptools.dist.Distribution.__init__
        package_data: dict[str, list[str]] = {},
        dist_files: list[tuple[str, str, str]] = [],
        include_package_data: bool | None = None,
        exclude_package_data: dict[str, list[str]] | None = None,
        src_root: str | None = None,
        dependency_links: list[str] = [],
        setup_requires: list[str] = [],
        # From Distribution._DISTUTILS_UNSUPPORTED_METADATA set in Distribution._set_metadata_defaults
        long_description_content_type: str | None = None,
        project_urls=dict(),
        provides_extras=dict(),
        license_expression=None,
        license_file=None,
        license_files=None,
        install_requires=list(),
        extras_require=dict(),
        # kwargs used directly in distutils.core.setup
        distclass: type[_DistributionT] = Distribution,  # type: ignore[assignment]
        # Custom Distributions could accept more params
        **attrs: Any,
    ) -> _DistributionT: ...

else:

    def setup(**attrs) -> Distribution:
        logging.configure()
        # Make sure we have any requirements needed to interpret 'attrs'.
        _install_setup_requires(attrs)
        return distutils.core.setup(**attrs)


setup.__doc__ = distutils.core.setup.__doc__

if TYPE_CHECKING:
    # Work around a mypy issue where type[T] can't be used as a base: https://github.com/python/mypy/issues/10962
    from distutils.core import Command as _Command
else:
    _Command = monkey.get_unpatched(distutils.core.Command)


class Command(_Command):
    """
    Setuptools internal actions are organized using a *command design pattern*.
    This means that each action (or group of closely related actions) executed during
    the build should be implemented as a ``Command`` subclass.

    These commands are abstractions and do not necessarily correspond to a command that
    can (or should) be executed via a terminal, in a CLI fashion (although historically
    they would).

    When creating a new command from scratch, custom defined classes **SHOULD** inherit
    from ``setuptools.Command`` and implement a few mandatory methods.
    Between these mandatory methods, are listed:
    :meth:`initialize_options`, :meth:`finalize_options` and :meth:`run`.

    A useful analogy for command classes is to think of them as subroutines with local
    variables called "options".  The options are "declared" in :meth:`initialize_options`
    and "defined" (given their final values, aka "finalized") in :meth:`finalize_options`,
    both of which must be defined by every command class. The "body" of the subroutine,
    (where it does all the work) is the :meth:`run` method.
    Between :meth:`initialize_options` and :meth:`finalize_options`, ``setuptools`` may set
    the values for options/attributes based on user's input (or circumstance),
    which means that the implementation should be careful to not overwrite values in
    :meth:`finalize_options` unless necessary.

    Please note that other commands (or other parts of setuptools) may also overwrite
    the values of the command's options/attributes multiple times during the build
    process.
    Therefore it is important to consistently implement :meth:`initialize_options` and
    :meth:`finalize_options`. For example, all derived attributes (or attributes that
    depend on the value of other attributes) **SHOULD** be recomputed in
    :meth:`finalize_options`.

    When overwriting existing commands, custom defined classes **MUST** abide by the
    same APIs implemented by the original class. They also **SHOULD** inherit from the
    original class.
    """

    command_consumes_arguments = False
    distribution: Distribution  # override distutils.dist.Distribution with setuptools.dist.Distribution

    # Any: The kwargs could match any Command attribute including from subclasses
    # and subclasses can further override it to include any type.
    def __init__(self, dist: Distribution, **kw: Any) -> None:
        """
        Construct the command for dist, updating
        vars(self) with any keyword parameters.
        """
        super().__init__(dist)
        vars(self).update(kw)

    @overload
    def reinitialize_command(
        self, command: str, reinit_subcommands: bool = False, **kw
    ) -> Command: ...  # override distutils.cmd.Command with setuptools.Command
    @overload
    def reinitialize_command(
        self, command: _CommandT, reinit_subcommands: bool = False, **kw
    ) -> _CommandT: ...
    def reinitialize_command(
        self, command: str | _Command, reinit_subcommands: bool = False, **kw
    ) -> Command | _Command:
        cmd = _Command.reinitialize_command(self, command, reinit_subcommands)
        vars(cmd).update(kw)
        return cmd  # pyright: ignore[reportReturnType] # pypa/distutils#307

    @abstractmethod
    def initialize_options(self) -> None:
        """
        Set or (reset) all options/attributes/caches used by the command
        to their default values. Note that these values may be overwritten during
        the build.
        """
        raise NotImplementedError

    @abstractmethod
    def finalize_options(self) -> None:
        """
        Set final values for all options/attributes used by the command.
        Most of the time, each option/attribute/cache should only be set if it does not
        have any value yet (e.g. ``if self.attr is None: self.attr = val``).
        """
        raise NotImplementedError

    @abstractmethod
    def run(self) -> None:
        """
        Execute the actions intended by the command.
        (Side effects **SHOULD** only take place when :meth:`run` is executed,
        for example, creating new files or writing to the terminal output).
        """
        raise NotImplementedError


def _find_all_simple(path):
    """
    Find all files under 'path'
    """
    results = (
        os.path.join(base, file)
        for base, dirs, files in os.walk(path, followlinks=True)
        for file in files
    )
    return filter(os.path.isfile, results)


def findall(dir=os.curdir):
    """
    Find all files under 'dir' and return the list of full filenames.
    Unless dir is '.', return full filenames with dir prepended.
    """
    files = _find_all_simple(dir)
    if dir == os.curdir:
        make_rel = functools.partial(os.path.relpath, start=dir)
        files = map(make_rel, files)
    return list(files)


class sic(str):
    """Treat this string as-is (https://en.wikipedia.org/wiki/Sic)"""


# Apply monkey patches
monkey.patch_all()
