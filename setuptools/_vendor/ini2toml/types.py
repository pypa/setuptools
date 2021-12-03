import sys
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, Callable, List, Optional, TypeVar, Union

from .intermediate_repr import (
    KV,
    Commented,
    CommentedKV,
    CommentedList,
    CommentKey,
    HiddenKey,
    IntermediateRepr,
    Key,
    WhitespaceKey,
)

if sys.version_info <= (3, 8):  # pragma: no cover
    # TODO: Import directly when `python_requires = >= 3.8`
    if TYPE_CHECKING:
        from typing_extensions import Protocol
    else:
        # Not a real replacement but allows getting rid of the dependency
        from abc import ABC as Protocol
else:  # pragma: no cover
    from typing import Protocol


R = TypeVar("R", bound=IntermediateRepr)
T = TypeVar("T")
M = TypeVar("M", bound=MutableMapping)

Scalar = Union[int, float, bool, str]  # TODO: missing time and datetime
CoerceFn = Callable[[str], T]
Transformation = Union[Callable[[str], Any], Callable[[M], M]]

TextProcessor = Callable[[str], str]
IntermediateProcessor = Callable[[R], R]


IniLoadsFn = Callable[[str, Mapping], IntermediateRepr]
IReprCollapseFn = Callable[[IntermediateRepr], T]
TomlDumpsFn = IReprCollapseFn[str]


class CLIChoice(Protocol):
    name: str
    help_text: str


class Profile(Protocol):
    name: str
    help_text: str
    pre_processors: List[TextProcessor]
    intermediate_processors: List[IntermediateProcessor]
    post_processors: List[TextProcessor]


class ProfileAugmentation(Protocol):
    active_by_default: bool
    name: str
    help_text: str

    def fn(self, profile: Profile):
        ...

    def is_active(self, explicitly_active: Optional[bool] = None) -> bool:
        """``explicitly_active`` is a tree-state variable: ``True`` if the user
        explicitly asked for the augmentation, ``False`` if the user explicitly denied
        the augmentation, or ``None`` otherwise.
        """


class Translator(Protocol):
    def __getitem__(self, profile_name: str) -> Profile:
        """Create and register (and return) a translation :class:`Profile`
        (or return a previously registered one) (see :ref:`core-concepts`).
        """

    def augment_profiles(
        self,
        fn: "ProfileAugmentationFn",
        active_by_default: bool = False,
        name: str = "",
        help_text: str = "",
    ):
        """Register a profile augmentation function (see :ref:`core-concepts`).
        The keyword ``name`` and ``help_text`` can be used to customise the description
        featured in ``ini2toml``'s CLI, but when these arguments are not given (or empty
        strings), ``name`` is taken from ``fn.__name__`` and ``help_text`` is taken from
        ``fn.__doc__`` (docstring).
        """


Plugin = Callable[[Translator], None]
ProfileAugmentationFn = Callable[[Profile], None]


__all__ = [
    "CLIChoice",
    "CommentKey",
    "Commented",
    "CommentedKV",
    "CommentedList",
    "HiddenKey",
    "IniLoadsFn",
    "IntermediateProcessor",
    "IntermediateRepr",
    "Key",
    "KV",
    "Plugin",
    "Profile",
    "ProfileAugmentation",
    "ProfileAugmentationFn",
    "TextProcessor",
    "Translator",
    "TomlDumpsFn",
    "WhitespaceKey",
    "Scalar",
    "CoerceFn",
    "Transformation",
]
