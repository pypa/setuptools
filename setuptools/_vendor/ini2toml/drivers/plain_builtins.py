"""The purpose of this module is to "collapse" the intermediate representation of a TOML
document into Python buitin data types (mainly a composition of :class:`dict`,
:class:`list`, :class:`int`, :class:`float`, :class:`bool`, :class:`str`).

This is **not a loss-less** process, since comments are not preserved.
"""
from collections.abc import Mapping, MutableMapping
from functools import singledispatch
from typing import Any, TypeVar

from ..errors import InvalidTOMLKey
from ..types import Commented, CommentedKV, CommentedList, HiddenKey, IntermediateRepr

__all__ = [
    "convert",
    "collapse",
]

M = TypeVar("M", bound=MutableMapping)


def convert(irepr: IntermediateRepr) -> dict:
    return collapse(irepr)


@singledispatch
def collapse(obj):
    # Catch all
    return obj


@collapse.register(Commented)
def _collapse_commented(obj: Commented) -> Any:
    return obj.value_or(None)


@collapse.register(CommentedList)
def _collapse_commented_list(obj: CommentedList) -> list:
    return [collapse(v) for v in obj.as_list()]


@collapse.register(CommentedKV)
def _collapse_commented_kv(obj: CommentedKV) -> dict:
    return {k: collapse(v) for k, v in obj.as_dict().items()}


@collapse.register(Mapping)
def _collapse_mapping(obj: Mapping) -> dict:
    return _convert_irepr_to_dict(obj, {})


@collapse.register(list)
def _collapse_list(obj: list) -> list:
    return [collapse(e) for e in obj]


def _convert_irepr_to_dict(irepr: Mapping, out: M) -> M:
    for key, value in irepr.items():
        if isinstance(key, HiddenKey):
            continue
        elif isinstance(key, tuple):
            parent_key, *rest = key
            if not isinstance(parent_key, str):
                raise InvalidTOMLKey(key)
            p = out.setdefault(parent_key, {})
            if not isinstance(p, MutableMapping):
                msg = f"Value for `{parent_key}` expected to be Mapping, found {p!r}"
                raise ValueError(msg)
            nested_key = rest[0] if len(rest) == 1 else tuple(rest)
            _convert_irepr_to_dict({nested_key: value}, p)
        elif isinstance(key, (int, str)):
            out[str(key)] = collapse(value)
    return out
