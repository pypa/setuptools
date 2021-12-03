"""Intermediate representations used by ``ini2toml`` when transforming between
the INI and TOML syntaxes.
"""
from collections import UserList
from enum import Enum
from itertools import chain
from pprint import pformat
from textwrap import indent
from types import MappingProxyType
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)
from uuid import uuid4

T = TypeVar("T")
S = TypeVar("S")
R = TypeVar("R", bound="IntermediateRepr")

KV = Tuple[str, T]

NotGiven = Enum("NotGiven", "NOT_GIVEN")
NOT_GIVEN = NotGiven.NOT_GIVEN

EMPTY: Mapping = MappingProxyType({})


class HiddenKey:
    __slots__ = ("_value",)

    def __init__(self):
        self._value = uuid4().int

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self._value == other._value

    def __hash__(self):
        return hash((self.__class__.__name__, self._value))

    def __str__(self):
        return f"{self.__class__.__name__}()"

    __repr__ = __str__


class WhitespaceKey(HiddenKey):
    pass


class CommentKey(HiddenKey):
    pass


Key = Union[str, HiddenKey, Tuple[Union[str, HiddenKey], ...]]


class IntermediateRepr(MutableMapping):
    def __init__(
        self,
        elements: Mapping[Key, Any] = EMPTY,
        order: Sequence[Key] = (),
        inline_comment: str = "",
        **kwargs,
    ):
        el = chain(elements.items(), kwargs.items())
        self.elements: Dict[Key, Any] = {}
        self.order: List[Key] = []
        self.inline_comment = inline_comment
        self.elements.update(el)
        self.order.extend(order or self.elements.keys())
        elem_not_in_order = any(k not in self.order for k in self.elements)
        order_not_in_elem = any(k not in self.elements for k in self.order)
        if elem_not_in_order or order_not_in_elem:
            raise ValueError(f"{order} and {elements} need to have the same keys")

    def __repr__(self):
        inner = ",\n".join(
            indent(f"{k}={pformat(getattr(self, k))}", "    ")
            for k in ("elements", "order", "inline_comment")
        )
        return f"{self.__class__.__name__}(\n{inner}\n)"

    def __eq__(self, other):
        L = len(self)
        if not (
            isinstance(other, self.__class__)
            and self.inline_comment == other.inline_comment
            and len(other) == L
        ):
            return False
        self_ = [(str(k), v) for k, v in self.items()]
        other_ = [(str(k), v) for k, v in other.items()]
        return all(self_[i] == other_[i] for i in range(L))

    def rename(self, old_key: Key, new_key: Key, ignore_missing=False):
        """This method renames an existing key, without changing its position.
        Notice that ``new_key`` cannot be already present, and that trying to rename
        a non-pre-existing key will also result in error (unless
        ``ignore_missing=True``).
        """
        if old_key == new_key:
            return self
        if new_key in self.order:
            raise KeyError(f"new_key={new_key!r} already exists")
        if old_key not in self.order and ignore_missing:
            return self
        i = self.order.index(old_key)
        self.order[i] = new_key
        self.elements[new_key] = self.elements.pop(old_key)
        return self

    def insert(self, position: int, key: Key, value: Any):
        """Simulate the position-aware :meth:`collections.abc.MutableMapping.insert`
        method, but also require a ``key`` to be specified.
        """
        if key in self.order:
            raise KeyError(f"key={key!r} already exists")
        self.order.insert(position, key)
        self.elements[key] = value

    def index(self, key: Key) -> int:
        """Find the position of ``key``"""
        return self.order.index(key)

    def append(self, key: Key, value: Any):
        """Simulate the position-aware :meth:`collections.abc.MutableMapping.append`
        method, but also require a ``key`` to be specified.
        """
        self.insert(len(self.order), key, value)

    def copy(self: R) -> R:
        return self.__class__(self.elements.copy(), self.order[:], self.inline_comment)

    def replace_first_remove_others(
        self, existing_keys: Sequence[Key], new_key: Key, value: Any
    ):
        """Find the first key in ``existing_keys`` that existing in the intermediate
        representation, and replaces it with ``new_key`` (similar to
        :meth:`replace`).
        All the other keys in ``existing_keys`` are removed and the value of
        ``new_key`` is set to ``value``.
        """
        idx = [self.index(k) for k in existing_keys if k in self]
        if not idx:
            i = len(self)
        else:
            i = sorted(idx)[0]
            for key in existing_keys:
                self.pop(key, None)
        self.insert(i, new_key, value)
        return i

    def __getitem__(self, key: Key):
        return self.elements[key]

    def __setitem__(self, key: Key, value: Any):
        if key not in self.elements:
            self.order.append(key)
        self.elements[key] = value

    def __delitem__(self, key: Key):
        del self.elements[key]
        self.order.remove(key)

    def __iter__(self):
        return iter(self.order)

    def __len__(self):
        return len(self.order)


# These objects hold information about the processed values + comments
# in such a way that we can later convert them to TOML while still preserving
# the comments (if we want to).


class Commented(Generic[T]):
    def __init__(
        self,
        value: Union[T, NotGiven] = NOT_GIVEN,
        comment: Optional[str] = None,
    ):
        self.value = value
        self.comment = comment

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__
            and self.value == other.value
            and self.comment == other.comment
        )

    def comment_only(self):
        return self.value is NOT_GIVEN

    def has_comment(self):
        return bool(self.comment)

    def value_or(self, fallback: S) -> Union[T, S]:
        return fallback if self.value is NOT_GIVEN else self.value

    def as_commented_list(self) -> "CommentedList[T]":
        value = [] if self.value is NOT_GIVEN else [self.value]
        return CommentedList([Commented(value, self.comment)])

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r}, {self.comment!r})"


class CommentedList(Generic[T], UserList):
    def __init__(self, data: Sequence[Commented[List[T]]] = ()):
        super().__init__(data)

    def as_list(self) -> list:
        out = []
        for entry in self:
            values = entry.value_or([])
            for value in values:
                out.append(value)
        return out

    def insert_line(self, i, values: Iterable[T], comment: Optional[str] = None):
        values = list(values)
        if values or comment:
            self.insert(i, Commented(values, comment))


class CommentedKV(Generic[T], UserList):
    def __init__(self, data: Sequence[Commented[List[KV[T]]]] = ()):
        super().__init__(data)

    def find(self, key: str) -> Optional[Tuple[int, int]]:
        for i, row in enumerate(self):
            for j, item in enumerate(row.value_or([])):
                if item[0] == key:
                    return (i, j)
        return None

    def insert_line(self, i, values: Iterable[KV[T]], comment: Optional[str] = None):
        values = list(values)
        if values or comment:
            self.insert(i, Commented(values, comment))
        return self

    def as_dict(self) -> dict:
        out = {}
        for entry in self:
            values = (v for v in entry.value_or([cast(KV, ())]) if v)
            for k, v in values:
                out[k] = v
        return out

    def to_ir(self) -> IntermediateRepr:
        """:class:`CommentedKV` are usually intended to represent INI options, while
        :class:`IntermediateRepr` are usually intended to represent INI sections.
        Therefore this function allows "promoting" an option-equivalent to a
        section-equivalent representation.
        """
        irepr = IntermediateRepr()
        for row in self:
            for key, value in row.value_or([]):
                irepr[key] = value
            if row.has_comment():
                irepr[key] = Commented(value, row.comment)

        return irepr
