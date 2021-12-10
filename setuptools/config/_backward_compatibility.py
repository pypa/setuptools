"""Simple checks to make sure the configuration that is automatically converted
to the ``pyproject.toml`` format results in the same outcome (in terms of the
``Distribution`` object parameters) as the one that would be previously obtained
via ``setup.cfg``.
"""
import os
import warnings
from textwrap import dedent
from typing import Union, Tuple, Optional


_Path = Union[os.PathLike, str]


EXCLUDED_FROM_COMPARISON = [
    "metadata_version",  # not currently handled/considered
    # Setuptools normalisations might make the following fields differ:
    "provides_extra", "requires_dist",
    # PEP 621 is specific about using Author/Maintainer-email when both
    # name and emails are provided
    "author", "maintainer", "author_email", "maintainer_email",
]


def ensure_compatible_conversion(filepath: _Path, ignore_option_errors: bool) -> bool:
    from setuptools import metadata, options
    from setuptools.diff_utils import diff

    new, legacy = _read_configs(filepath, ignore_option_errors)

    metas = (new["metadata"].copy(), legacy["metadata"].copy())
    for meta in metas:
        for field in EXCLUDED_FROM_COMPARISON:
            meta.pop(field, None)

    cmp = metadata.compare(*metas)
    is_compatible = cmp is True or cmp == -1  # -1 => first is superset of second
    if not is_compatible:
        labels = ("pyproject.toml-style metadata", "setupt.cfg-style metadata")
        raise NonEquivalentConversion(filepath, diff(*metas, *labels))

    cmp = options.compare(new["options"], legacy["options"])
    is_compatible = cmp is True or cmp == -1  # -1 => first is superset of second
    if not is_compatible:
        labels = ("pyproject.toml-style options", "setupt.cfg-style options")
        delta = diff(new["options"], legacy["options"], *labels)
        raise NonEquivalentConversion(filepath, delta)

    return True


def _read_configs(filepath: _Path, ignore_option_errors: bool) -> Tuple[dict, dict]:
    from setuptools import metadata, options
    from setuptools.dist import Distribution

    from . import setupcfg, legacy_setupcfg

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config = setupcfg.read_configuration(filepath, True, ignore_option_errors)
    except Exception as ex:
        raise FailedExperimentalConversion(filepath) from ex

    new = {
        "metadata": metadata.from_pyproject(config),
        "options": options.from_pyproject(config),
    }

    dist = Distribution()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        legacy_setupcfg._apply(filepath, dist, (), ignore_option_errors)

    legacy = {
        "metadata": metadata.from_dist(dist),
        "options": options.from_dist(dist),
    }

    return new, legacy


class FailedExperimentalConversion(Exception):
    """\
    Some errors happened when trying to automatically convert configurations
    form {file!r} (`setup.cfg` style) to `pyproject.toml` style.
    """

    _ISSUES_NOTE = """\
    Please make sure you have a valid package configuration.
    Note that setuptools support for configuration via `pyproject.toml` is
    still **EXPERIMENTAL**. You can help by reporting this issue to:
    \t- https://github.com/abravalheri/ini2toml/issues (automatic conversion)
    \t- https://github.com/abravalheri/validate_pyproject/issues (validation)
    \t- https://github.com/pypa/setuptools/issues (non conversion-related problems)
    Please provide as much information to replicate this error as possible.
    Pull requests are welcome and encouraged.
    """

    def __init__(self, filepath: _Path, msg: Optional[str] = None):
        msg = (msg or self.__class__.__doc__).format(file=os.path.abspath(filepath))
        super().__init__(dedent(msg) + "\n" + dedent(self._ISSUES_NOTE))

    def warn(self):
        """Issue a warn with the same error message.
        For situations that are possible to workaround, but it is good to tell the user
        """
        warnings.warn(str(self), category=FailedConversionWarning, stacklevel=2)


class NonEquivalentConversion(FailedExperimentalConversion):
    """\
    Failed automatic conversion of `setup.cfg`-style configuration to `pyproject.toml`,
    the outcome configuration is not equivalent:
    \n{diff}
    """

    def __init__(self, filepath: _Path, delta: str):
        super().__init__(filepath, self.__class__.__doc__.format(diff=delta))


class FailedConversionWarning(UserWarning):
    """Warning associated with ``FailedExperimentalConversion``"""
