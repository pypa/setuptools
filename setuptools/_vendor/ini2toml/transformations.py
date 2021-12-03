"""Reusable value and type casting transformations"""
import warnings
from collections.abc import MutableMapping
from functools import reduce, wraps
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from .types import Commented, CommentedKV, CommentedList

CP = ("#", ";")
"""Default Comment Prefixes"""

S = TypeVar("S")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
X = TypeVar("X")
Y = TypeVar("Y")
M = TypeVar("M", bound=MutableMapping)
KV = Tuple[str, T]

FN = Callable[[X], Y]

Scalar = Union[int, float, bool, str]  # TODO: missing time and datetime
"""Simple data types with TOML correspondence"""

CoerceFn = Callable[[str], T]
"""Functions that know how to parser/coerce string values into different types"""

Transformation = Union[Callable[[str], Any], Callable[[M], M]]
"""There are 2 main types of transformation:

- The first one is a simple transformation that processes a string value (coming from an
  option in the original CFG/INI file) into a value with an equivalent TOML data type.
  For example: transforming ``"2"`` (string) into ``2`` (integer).
- The second one tries to preserve metadata (such as comments) from the original CFG/INI
  file. This kind of transformation processes a string value into an intermediary
  representation (e.g. :obj:`Commented`, :obj:`CommentedList`, obj:`CommentedKV`)
  that needs to be properly handled before adding to the TOML document.

In a higher level we can also consider an ensemble of transformations that transform an
entire table of the TOML document.
"""

TF = TypeVar("TF", bound=Transformation)


# ---- Simple value processors ----
# These functions return plain objects, that can be directly added to the TOML document


def noop(x: T) -> T:
    return x


def is_true(value: str) -> bool:
    value = value.lower()
    return value in ("true", "1", "yes", "on")


def is_false(value: str) -> bool:
    value = value.lower()
    return value in ("false", "0", "no", "off", "none", "null", "nil")


def is_float(value: str) -> bool:
    cleaned = value.lower().lstrip("+-").replace(".", "").replace("_", "")
    return cleaned.isdecimal() and value.count(".") <= 1 or cleaned in ("inf", "nan")


def coerce_bool(value: str) -> bool:
    if is_true(value):
        return True
    if is_false(value):
        return False
    raise ValueError(f"{value!r} cannot be converted to boolean")


def coerce_scalar(value: str) -> Scalar:
    """Try to convert the given string to a proper "scalar" type (e.g. integer, float,
    bool, ...) with an direct TOML equivalent.
    If the conversion is unknown or not possible, it will return the same input value
    (as string).

    .. note:: This function "guesses" the value type based in heuristics and/or regular
       expressions, therefore there is no guarantee the output has the same type as
       intended by the original author.

    .. note:: Currently date/time-related types are not supported.
    """
    value = value.strip()
    if value.isdecimal():
        return int(value)
    if is_float(value):
        return float(value)
    if is_true(value):
        return True
    elif is_false(value):
        return False
    # Do we need this? Or is there a better way? How about time objects
    # > try:
    # >     return datetime.fromisoformat(value)
    # > except ValueError:
    # >     pass
    return value


def kebab_case(field: str) -> str:
    return field.lower().replace("_", "-")


def deprecated(
    name: str, fn: TF = noop, instead: str = ""  # type: ignore[assignment]
) -> TF:
    """Wrapper around the ``fn`` transformation to warn user about deprecation."""
    extra = f". Use {instead!r} instead" if instead else ""

    @wraps(fn)
    def _fn(*args, **kwargs):
        warnings.warn(f"{name!r} is deprecated{extra}", DeprecationWarning)
        return fn(*args, **kwargs)

    return cast(TF, _fn)


# ---- Complex value processors ----
# These functions return an intermediate representation of the value,
# that need `apply` to be added to a container


@overload
def split_comment(value: str, *, comment_prefixes=CP) -> Commented[str]:
    ...


@overload
def split_comment(
    value: str, coerce_fn: CoerceFn[T], comment_prefixes=CP
) -> Commented[T]:
    ...


def split_comment(value, coerce_fn=noop, comment_prefixes=CP):
    if not isinstance(value, str):
        return value
    value = value.strip()
    prefixes = [p for p in comment_prefixes if p in value]

    # We just process inline comments for single line options
    if not prefixes or len(value.splitlines()) > 1:
        return Commented(coerce_fn(value))

    if any(value.startswith(p) for p in comment_prefixes):
        return Commented(comment=_strip_comment(value, comment_prefixes))

    prefix = prefixes[0]  # We can only analyse one...
    value, _, cmt = value.partition(prefix)
    return Commented(coerce_fn(value.strip()), _strip_comment(cmt, comment_prefixes))


def split_scalar(value: str, *, comment_prefixes=CP) -> Commented[Scalar]:
    return split_comment(value, coerce_scalar, comment_prefixes)


@overload
def split_list(
    value: str, sep: str = ",", *, subsplit_dangling=True, comment_prefixes=CP
) -> CommentedList[str]:
    ...


@overload
def split_list(
    value: str,
    sep: str = ",",
    *,
    coerce_fn: CoerceFn[T],
    subsplit_dangling=True,
    comment_prefixes=CP,
) -> CommentedList[T]:
    ...


@overload
def split_list(
    value: str,
    sep: str,
    coerce_fn: CoerceFn[T],
    subsplit_dangling=True,
    comment_prefixes=CP,
) -> CommentedList[T]:
    ...


def split_list(
    value, sep=",", coerce_fn=noop, subsplit_dangling=True, comment_prefixes=CP
):
    """Value encoded as a (potentially) dangling list values separated by ``sep``.

    This function will first try to split the value by lines (dangling list) using
    :func:`str.splitlines`. Then, if ``subsplit_dangling=True``, it will split each line
    using ``sep``. As a result a list of items is obtained.
    For each item in this list ``coerce_fn`` is applied.
    """
    if not isinstance(value, str):
        return value
    comment_prefixes = [p for p in comment_prefixes if sep not in p]

    values = value.strip().splitlines()
    if not subsplit_dangling and len(values) > 1:
        sep += "\n"  # force a pattern that cannot be found in a split line

    def _split(line: str) -> list:
        return [coerce_fn(v.strip()) for v in line.split(sep) if v]

    return CommentedList([split_comment(v, _split, comment_prefixes) for v in values])


@overload
def split_kv_pairs(
    value: str,
    key_sep: str = "=",
    *,
    pair_sep=",",
    subsplit_dangling=True,
    comment_prefixes=CP,
) -> CommentedKV[str]:
    ...


@overload
def split_kv_pairs(
    value: str,
    key_sep: str = "=",
    *,
    coerce_fn: CoerceFn[T],
    pair_sep=",",
    subsplit_dangling=True,
    comment_prefixes=CP,
) -> CommentedKV[T]:
    ...


@overload
def split_kv_pairs(
    value: str,
    key_sep: str,
    coerce_fn: CoerceFn[T],
    pair_sep=",",
    subsplit_dangling=True,
    comment_prefixes=CP,
) -> CommentedKV[T]:
    ...


def split_kv_pairs(
    value,
    key_sep="=",
    coerce_fn=noop,
    pair_sep=",",
    subsplit_dangling=True,
    comment_prefixes=CP,
):
    """Value encoded as a (potentially) dangling list of key-value pairs.

    This function will first try to split the value by lines (dangling list) using
    :func:`str.splitlines`. Then, if ``subsplit_dangling=True``, it will split each line
    using ``pair_sep``. As a result a list of key-value pairs is obtained.
    For each item in this list, the key is separated from the value by ``key_sep``.
    ``coerce_fn`` is used to convert the value in each pair.
    """
    prefixes = [p for p in comment_prefixes if key_sep not in p and pair_sep not in p]

    values = value.strip().splitlines()
    if not subsplit_dangling and len(values) > 1:
        pair_sep += "\n"  # force a pattern that cannot be found in a split line

    def _split_kv(line: str) -> List[KV]:
        pairs = (
            item.split(key_sep, maxsplit=1)
            for item in line.strip().split(pair_sep)
            if key_sep in item
        )
        return [(k.strip(), coerce_fn(v.strip())) for k, v in pairs]

    return CommentedKV([split_comment(v, _split_kv, prefixes) for v in values])


# ---- Public Helpers ----


def remove_prefixes(text: str, prefixes: Sequence[str]):
    text = text.strip()
    for prefix in prefixes:
        if prefix and text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def apply(x, fn):
    """Useful to reduce over a list of functions"""
    return fn(x)


@overload
def pipe(fn1: FN[S, T], fn2: FN[T, U]) -> FN[S, U]:
    ...


@overload
def pipe(fn1: FN[S, T], fn2: FN[T, U], fn3: FN[U, V]) -> FN[S, V]:
    ...


@overload
def pipe(fn1: FN[S, T], fn2: FN[T, U], fn3: FN[U, V], fn4: FN[V, X]) -> FN[S, X]:
    ...


@overload
def pipe(
    fn1: FN[S, T], fn2: FN[T, U], fn3: FN[U, V], fn4: FN[V, X], fn5: FN[X, Y]
) -> FN[S, Y]:
    ...


@overload
def pipe(
    fn1: FN[S, T],
    fn2: FN[T, U],
    fn3: FN[U, V],
    fn4: FN[V, X],
    fn5: FN[X, Y],
    *fn: FN[Y, Y],
) -> FN[S, Y]:
    ...


def pipe(*fns):
    """Compose 1-argument functions respecting the sequence they should be applied:

    .. code-block:: python

        pipe(fn1, fn2, fn3, ..., fnN)(x) == fnN(...(fn3(fn2(fn1(x)))))
    """
    return lambda x: reduce(apply, fns, x)


# ---- Private Helpers ----


def _strip_comment(msg: Optional[str], prefixes: Sequence[str] = CP) -> Optional[str]:
    if not msg:
        return None
    return remove_prefixes(msg, prefixes)
