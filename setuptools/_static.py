from collections import abc
from functools import singledispatch

import packaging.specifiers


class Static:
    """
    Wrapper for butil-in object types that are allow setuptools to identify
    static core metadata (in opposition to ``Dynamic``, as defined :pep:`643`).

    The trick is to mark values with :class:`Static` when they come from
    ``pyproject.toml`` or ``setup.cfg``, so if any plugin overwrite the value
    with a built-in, setuptools will be able to recognise the change.

    We inherit from built-in classes, so that we don't need to change the existing
    code base to deal with the new types.
    We also prefer "immutable-ish" objects to avoid changes after the initial parsing.
    """


class Str(str, Static):
    pass


class Tuple(tuple, Static):
    pass


class Mapping(dict, Static):
    pass


def _do_not_modify(*_, **__):
    raise NotImplementedError("Direct modification disallowed (statically defined)")


# Make `Mapping` immutable-ish (we cannot inherit from types.MappingProxyType):
for _method in (
    '__delitem__',
    '__ior__',
    '__setitem__',
    'clear',
    'pop',
    'popitem',
    'setdefault',
    'update',
):
    setattr(Mapping, _method, _do_not_modify)


class SpeficierSet(packaging.specifiers.SpecifierSet, Static):
    """Not exactly a builtin type but useful for ``requires-python``"""


@singledispatch
def convert(value):
    return value


@convert.register
def _(value: str) -> Str:
    return Str(value)


@convert.register
def _(value: str) -> Str:
    return Str(value)


@convert.register
def _(value: tuple) -> Tuple:
    return Tuple(value)


@convert.register
def _(value: list) -> Tuple:
    return Tuple(value)


@convert.register
def _(value: abc.Mapping) -> Mapping:
    return Mapping(value)
