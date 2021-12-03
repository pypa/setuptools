from functools import reduce
from types import MappingProxyType
from typing import Dict, Generic, List, Mapping, Sequence, TypeVar

from . import types  # Structural/Abstract types
from .errors import (
    AlreadyRegisteredAugmentation,
    InvalidAugmentationName,
    UndefinedProfile,
)
from .profile import Profile, ProfileAugmentation
from .transformations import apply

T = TypeVar("T")
EMPTY = MappingProxyType({})  # type: ignore


class BaseTranslator(Generic[T]):
    """Translator object that follows the public API defined in
    :class:`ini2toml.types.Translator`. See :doc:`dev-guide` for a quick explanation of
    concepts such as plugins, profiles, profile augmentations, etc.

    Arguments
    ---------

    ini_loads_fn:
        function to convert the ``.ini/.cfg`` file into an :class:`intermediate
        representation <ini2toml.intermediate_repr.IntermediateRepr>` object.
        Possible values for this argument include:

        - :func:`ini2toml.drivers.configparser.parse` (when comments can be simply
          removed)
        - :func:`ini2toml.drivers.configupdater.parse` (when you wish to preserve
          comments in the TOML output)

    toml_dumps_fn:
        function to convert the :class:`intermediate representation
        <ini2toml.intermediate_repr.IntermediateRepr>` object into (ideally)
        a TOML string.
        If you don't exactly need a TOML string (maybe you want your TOML to
        be represented by :class:`bytes` or simply the equivalent :obj:`dict`) you can
        also pass a ``Callable[[IntermediateRepr], T]`` function for any desired ``T``.

        Possible values for this argument include:

        - :func:`ini2toml.drivers.lite_toml.convert` (when comments can be simply
          removed)
        - :func:`ini2toml.drivers.full_toml.convert` (when you wish to preserve
          comments in the TOML output)
        - :func:`ini2toml.drivers.plain_builtins.convert` (when you wish to retrieve a
          :class:`dict` equivalent to the TOML, instead of string with the TOML syntax)

    plugins:
        list of plugins activation functions. By default no plugin will be activated.
    profiles:
        list of profile objects, by default no profile will be pre-loaded (plugins can
        still add them).
    profile_augmentations:
        list of profile augmentations. By default no profile augmentation will be
        preloaded (plugins can still add them)
    ini_parser_opts:
        syntax options for parsing ``.ini/.cfg`` files (see
        :mod:`~configparser.ConfigParser` and :mod:`~configupdater.ConfigUpdater`).
        By default it uses the standard configuration of the selected parser (depending
        on the choice of ``ini_loads_fn``).

    Tip
    ---

    Most of the times the usage of :class:`~ini2toml.translator.Translator` is preferred
    over :class:`~ini2toml.base_translator.BaseTranslator` (unless you are vendoring
    ``ini2toml`` and wants to reduce the number of files included in your project).
    """

    profiles: Dict[str, types.Profile]
    plugins: List[types.Plugin]

    def __init__(
        self,
        ini_loads_fn: types.IniLoadsFn,
        toml_dumps_fn: types.IReprCollapseFn[T],
        plugins: Sequence[types.Plugin] = (),
        profiles: Sequence[types.Profile] = (),
        profile_augmentations: Sequence[types.ProfileAugmentation] = (),
        ini_parser_opts: Mapping = EMPTY,
    ):
        self.plugins = list(plugins)
        self.ini_parser_opts = ini_parser_opts
        self.profiles = {p.name: p for p in profiles}
        self.augmentations: Dict[str, types.ProfileAugmentation] = {
            (p.name or p.fn.__name__): p for p in profile_augmentations
        }

        self._loads_fn = ini_loads_fn
        self._dumps_fn = toml_dumps_fn

        for activate in self.plugins:
            activate(self)

    def loads(self, text: str) -> types.IntermediateRepr:
        return self._loads_fn(text, self.ini_parser_opts)

    def dumps(self, irepr: types.IntermediateRepr) -> T:
        return self._dumps_fn(irepr)

    def __getitem__(self, profile_name: str) -> types.Profile:
        """Retrieve an existing profile (or create a new one)."""
        if profile_name not in self.profiles:
            profile = Profile(profile_name)
            if self.ini_parser_opts:
                profile = profile.replace(ini_parser_opts=self.ini_parser_opts)
            self.profiles[profile_name] = profile
        return self.profiles[profile_name]

    def augment_profiles(
        self,
        fn: types.ProfileAugmentationFn,
        active_by_default: bool = False,
        name: str = "",
        help_text: str = "",
    ):
        """Register a profile augmentation function to be called after the
        profile is selected and before the actual translation (see :doc:`dev-guide`).
        """
        name = (name or fn.__name__).strip()
        InvalidAugmentationName.check(name)
        AlreadyRegisteredAugmentation.check(name, fn, self.augmentations)
        help_text = help_text or fn.__doc__ or ""
        obj = ProfileAugmentation(fn, active_by_default, name, help_text)
        self.augmentations[name] = obj

    def _add_augmentations(
        self, profile: types.Profile, explicit_activation: Mapping[str, bool] = EMPTY
    ) -> types.Profile:
        for aug in self.augmentations.values():
            if aug.is_active(explicit_activation.get(aug.name)):
                aug.fn(profile)
        return profile

    def translate(
        self,
        ini: str,
        profile_name: str,
        active_augmentations: Mapping[str, bool] = EMPTY,
    ) -> T:
        UndefinedProfile.check(profile_name, list(self.profiles.keys()))
        profile = self._add_augmentations(self[profile_name], active_augmentations)

        ini = reduce(apply, profile.pre_processors, ini)
        irepr = self.loads(ini)
        irepr = reduce(apply, profile.intermediate_processors, irepr)
        toml = self.dumps(irepr)
        return reduce(apply, profile.post_processors, toml)
