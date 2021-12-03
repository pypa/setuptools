import logging
import re
import string
from itertools import chain
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------------------
# PEP 440

VERSION_PATTERN = r"""
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""

VERSION_REGEX = re.compile(r"^\s*" + VERSION_PATTERN + r"\s*$", re.X | re.I)


def pep440(version: str) -> bool:
    return VERSION_REGEX.match(version) is not None


# -------------------------------------------------------------------------------------
# PEP 508

PEP508_IDENTIFIER_PATTERN = r"([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])"
PEP508_IDENTIFIER_REGEX = re.compile(f"^{PEP508_IDENTIFIER_PATTERN}$", re.I)


def pep508_identifier(name: str) -> bool:
    return PEP508_IDENTIFIER_REGEX.match(name) is not None


try:
    try:
        from packaging import requirements as _req
    except ImportError:  # pragma: no cover
        # let's try setuptools vendored version
        from setuptools._vendor.packaging import requirements as _req  # type: ignore

    def pep508(value: str) -> bool:
        try:
            _req.Requirement(value)
            return True
        except _req.InvalidRequirement:
            return False


except ImportError:  # pragma: no cover
    _logger.warning(
        "Could not find an installation of `packaging`. Requirements, dependencies and "
        "versions might not be validated. "
        "To enforce validation, please install `packaging`."
    )

    def pep508(value: str) -> bool:
        return True


def pep508_versionspec(value: str) -> bool:
    """Expression that can be used to specify/lock versions (including ranges)"""
    if any(c in value for c in (";", "]", "@")):
        # In PEP 508:
        # conditional markers, extras and URL specs are not included in the
        # versionspec
        return False
    # Let's pretend we have a dependency called `requirement` with the given
    # version spec, then we can re-use the pep508 function for validation:
    return pep508(f"requirement{value}")


# -------------------------------------------------------------------------------------
# PEP 517


def pep517_backend_reference(value: str) -> bool:
    module, _, obj = value.partition(":")
    identifiers = (i.strip() for i in chain(module.split("."), obj.split(".")))
    return all(python_identifier(i) for i in identifiers if i)


# -------------------------------------------------------------------------------------
# Classifiers - PEP 301


try:
    from trove_classifiers import classifiers as _trove_classifiers

    def trove_classifier(value: str) -> bool:
        return value in _trove_classifiers


except ImportError:  # pragma: no cover

    class _TroveClassifier:
        def __init__(self):
            self._warned = False
            self.__name__ = "trove-classifier"

        def __call__(self, value: str) -> bool:
            if self._warned is False:
                self._warned = True
                _logger.warning("Install ``trove-classifiers`` to ensure validation.")
            return True

    trove_classifier = _TroveClassifier()


# -------------------------------------------------------------------------------------
# Non-PEP related


def url(value: str) -> bool:
    try:
        parts = urlparse(value)
        return bool(parts.scheme and parts.netloc)
        # ^  TODO: should we enforce schema to be http(s)?
    except Exception:
        return False


# https://packaging.python.org/specifications/entry-points/
ENTRYPOINT_PATTERN = r"[^\[\s=]([^=]*[^\s=])?"
ENTRYPOINT_REGEX = re.compile(f"^{ENTRYPOINT_PATTERN}$", re.I)
RECOMMEDED_ENTRYPOINT_PATTERN = r"[\w.-]+"
RECOMMEDED_ENTRYPOINT_REGEX = re.compile(f"^{RECOMMEDED_ENTRYPOINT_PATTERN}$", re.I)
ENTRYPOINT_GROUP_PATTERN = r"\w+(\.\w+)*"
ENTRYPOINT_GROUP_REGEX = re.compile(f"^{ENTRYPOINT_GROUP_PATTERN}$", re.I)


def python_identifier(value: str) -> bool:
    return value.isidentifier()


def python_qualified_identifier(value: str) -> bool:
    if value.startswith(".") or value.endswith("."):
        return False
    return all(python_identifier(m) for m in value.split("."))


def python_module_name(value: str) -> bool:
    return python_qualified_identifier(value)


def python_entrypoint_group(value: str) -> bool:
    return ENTRYPOINT_GROUP_REGEX.match(value) is not None


def python_entrypoint_name(value: str) -> bool:
    if not ENTRYPOINT_REGEX.match(value):
        return False
    if not RECOMMEDED_ENTRYPOINT_REGEX.match(value):
        msg = f"Entry point `{value}` does not follow recommended pattern: "
        msg += RECOMMEDED_ENTRYPOINT_PATTERN
        _logger.warning(msg)
    return True


def python_entrypoint_reference(value: str) -> bool:
    if ":" not in value:
        return False
    module, _, rest = value.partition(":")
    if "[" in rest:
        obj, _, extras_ = rest.partition("[")
        if extras_.strip()[-1] != "]":
            return False
        extras = (x.strip() for x in extras_.strip(string.whitespace + "[]").split(","))
        if not all(pep508_identifier(e) for e in extras):
            return False
        _logger.warning(f"`{value}` - using extras for entry points is not recommended")
    else:
        obj = rest

    identifiers = chain(module.split("."), obj.split("."))
    return all(python_identifier(i.strip()) for i in identifiers)
