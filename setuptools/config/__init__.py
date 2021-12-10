import os
import sys
import warnings
from functools import wraps
from textwrap import dedent
from typing import TYPE_CHECKING, Callable, Optional, TypeVar, Union

if sys.version_info[:1] >= (3, 8):  # pragma: no cover
    from typing import Literal

    Syntax = Optional[Literal["ini", "cfg", "toml"]]
else:  # pragma: no cover
    Syntax = Optional[str]

if TYPE_CHECKING:
    from setuptools.dist import Distribution

Fn = TypeVar("Fn", bound=Callable)
_Path = Union[os.PathLike, str]


__all__ = [
    "parse_configuration",
    "read_configuration",
    "read",
    "apply"
]


# -------- Backward compatibility -------


def _deprecation_notice(fn: Fn) -> Fn:
    from setuptools import SetuptoolsDeprecationWarning

    @wraps(fn)
    def _wrapper(*args, **kwargs):
        msg = f"""\
            As setuptools moves its configuration towards `pyproject.toml`,
            `{fn.__name__}` became deprecated.

            For the time being, the `setuptools.config.legacy_setupcfg` module
            provides backwards compatibility, but it might be removed in the future.
            Users are encouraged to use:

            `setuptools.config.read`: to obtain a dict corresponding to the
                 data-struct stored in the `pyproject.toml` format.
            `setuptools.config.apply`: to apply the configurations read into an
                existing `setuptools.dist.Distribution` object.
        """
        warnings.warn(dedent(msg), SetuptoolsDeprecationWarning)
        return fn(*args, **kwargs)

    return _wrapper


@_deprecation_notice
def read_configuration(filepath, find_others=False, ignore_option_errors=False):
    from .legacy_setupcfg import read_configuration as _legacy
    return _legacy(filepath, find_others, ignore_option_errors)


@_deprecation_notice
def parse_configuration(distribution, command_options, ignore_option_errors=False):
    from .legacy_setupcfg import parse_configuration as _legacy
    return _legacy(distribution, command_options, ignore_option_errors)


# -------- New API -------


def read(
    filepath: _Path,
    expand: bool = True,
    ignore_option_errors: bool = False,
    syntax: Syntax = None,
) -> dict:
    """Read configuration from ``pyproject.toml``.

    In the case a config file with the legacy ``setup.cfg`` format is provided,
    this function will attempt to automatically convert it to the new format.
    If this conversion goes wrong, a `FailedExperimentalConversion` error is raised.

    :param bool expand: Whether to expand directives and other computed values
        (i.e. post-process the given configuration)

    :param bool ignore_option_errors: Whether to silently ignore
        options, values of which could not be resolved (e.g. due to exceptions
        in directives such as file:, attr:, etc.).
        If False exceptions are propagated as expected.

    :param syntax: One of `ini` or `toml` (optional). When not provided setuptools
        will attempt to guess based on the file name.
    """
    from . import setupcfg, pyprojecttoml

    if syntax is None:
        _, ext = os.path.splitext(filepath)
        if ext not in {".ini", ".cfg", ".toml"}:
            msg = f"Could not infer the configuration language for {filepath!r}. "
            msg += 'Please specify the `syntax` argument (e.g. `syntax="toml"`)'
            raise ValueError(msg)
        syntax = ext.strip(".")

    if syntax != "toml":
        from ._backward_compatibility import ensure_compatible_conversion

        ensure_compatible_conversion(filepath, ignore_option_errors)
        # ^-- To support the transition period we do a comparison and fail if it differs
        #     TODO: Remove once the transition period ends
        return setupcfg.read_configuration(filepath, expand, ignore_option_errors)

    return pyprojecttoml.read_configuration(filepath, expand, ignore_option_errors)


def apply(
    config: dict,
    dist: "Distribution",
    source: str = "pyproject.toml"
) -> "Distribution":
    """Apply configurations from a dict (that was loaded via the ``read`` function)
    into a distribution object.
    """
    from setuptools import metadata, options

    meta = metadata.from_pyproject(config)
    metadata.apply(meta, dist)

    opts = options.from_pyproject(config)
    options.apply(opts, dist)

    return dist
