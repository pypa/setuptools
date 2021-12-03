from textwrap import dedent
from typing import Callable, List, Mapping, Sequence

from . import types


class UndefinedProfile(ValueError):
    """The given profile ('{name}') is not registered with ``ini2toml``.
    Are you sure you have the right plugins installed and loaded?
    """

    def __init__(self, name: str, available: Sequence[str]):
        msg = self.__class__.__doc__ or ""
        super().__init__(msg.format(name=name) + f"Available: {', '.join(available)})")

    @classmethod
    def check(cls, name: str, available: List[str]):
        if name not in available:
            raise cls(name, available)


class AlreadyRegisteredAugmentation(ValueError):
    """The profile augmentation '{name}' is already registered for '{existing}'.

    Some installed plugins seem to be in conflict with each other,
    please check '{new}' and '{existing}'.
    If you are the developer behind one of them, please use a different name.
    """

    def __init__(self, name: str, new: Callable, existing: Callable):
        existing_id = f"{existing.__module__}.{existing.__qualname__}"
        new_id = f"{new.__module__}.{new.__qualname__}"
        msg = dedent(self.__class__.__doc__ or "")
        super().__init__(msg.format(name=name, new=new_id, existing=existing_id))

    @classmethod
    def check(
        cls, name: str, fn: Callable, registry: Mapping[str, types.ProfileAugmentation]
    ):
        if name in registry:
            raise cls(name, fn, registry[name].fn)


class InvalidAugmentationName(ValueError):
    """Profile augmentations should be valid python identifiers"""

    def __init__(self, name: str):
        msg = self.__class__.__doc__ or ""
        super().__init__(f"{msg} ('{name}' given)")

    @classmethod
    def check(cls, name: str):
        if not name.isidentifier():
            raise cls(name)


class InvalidTOMLKey(ValueError):
    """{key!r} is not a valid key in the intermediate TOML representation"""

    def __init__(self, key):
        msg = self.__doc__.format(key=key)
        super().__init__(msg)


class InvalidCfgBlock(ValueError):  # pragma: no cover -- not supposed to happen
    """Something is wrong with the provided CFG AST, the given block is not valid."""

    def __init__(self, block):
        super().__init__(f"{block.__class__}: {block}", {"block_object": block})
