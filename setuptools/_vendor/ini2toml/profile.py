import inspect
from typing import Optional, Sequence, TypeVar

from .types import IntermediateProcessor, ProfileAugmentationFn, TextProcessor

P = TypeVar("P", bound="Profile")


def replace(self: P, **changes) -> P:
    """Works similarly to :func:`dataclasses.replace`"""
    sig = inspect.signature(self.__class__)
    kwargs = {x: getattr(self, x) for x in sig.parameters}
    kwargs.update(changes)
    return self.__class__(**kwargs)


class Profile:
    """Profile object that follows the public API defined in
    :class:`ini2toml.types.Profile`.
    """

    def __init__(
        self,
        name: str,
        help_text: str = "",
        pre_processors: Sequence[TextProcessor] = (),
        intermediate_processors: Sequence[IntermediateProcessor] = (),
        post_processors: Sequence[TextProcessor] = (),
        ini_parser_opts: Optional[dict] = None,
    ):
        self.name = name
        self.help_text = help_text
        self.pre_processors = list(pre_processors)
        self.intermediate_processors = list(intermediate_processors)
        self.post_processors = list(post_processors)
        self.ini_parser_opts = ini_parser_opts

    replace = replace


class ProfileAugmentation:
    def __init__(
        self,
        fn: ProfileAugmentationFn,
        active_by_default: bool = False,
        name: str = "",
        help_text: str = "",
    ):
        self.fn = fn
        self.active_by_default = active_by_default
        self.name = name
        self.help_text = help_text

    def is_active(self, explicitly_active: Optional[bool] = None) -> bool:
        """``explicitly_active`` is a tree-state variable: ``True`` if the user
        explicitly asked for the augmentation, ``False`` if the user explicitly denied
        the augmentation, or ``None`` otherwise.
        """
        activation = explicitly_active
        return activation is True or (activation is None and self.active_by_default)
