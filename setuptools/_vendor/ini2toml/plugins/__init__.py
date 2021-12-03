# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'tests/examples/pyscaffold'

import sys
from textwrap import dedent
from typing import Callable, Iterable, List, Optional

from .. import __version__
from ..types import Plugin

ENTRYPOINT_GROUP = "ini2toml.processing"

try:
    if sys.version_info[:2] >= (3, 8):  # pragma: no cover
        # TODO: Import directly (no conditional) when `python_requires = >= 3.8`
        from importlib.metadata import EntryPoint, entry_points
    else:  # pragma: no cover
        from importlib_metadata import EntryPoint, entry_points

    def iterate_entry_points(group=ENTRYPOINT_GROUP) -> Iterable[EntryPoint]:
        """Produces a generator yielding an EntryPoint object for each plugin registered
        via `setuptools`_ entry point mechanism.

        This method can be used in conjunction with :obj:`load_from_entry_point` to
        filter the plugins before actually loading them.


        .. _setuptools: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
        """  # noqa
        entries = entry_points()
        if hasattr(entries, "select"):
            # The select method was introduced in importlib_metadata 3.9/3.10
            # and the previous dict interface was declared deprecated
            entries_ = entries.select(group=group)  # type: ignore
        else:
            # TODO: Once Python 3.10 becomes the oldest version supported, this fallback
            #       and conditional statement can be removed.
            entries_ = (plugin for plugin in entries.get(group, []))
        return sorted(entries_, key=lambda e: e.name)

except ImportError:  # pragma: no cover
    from pkg_resources import EntryPoint, iter_entry_points  # type: ignore

    def iterate_entry_points(group=ENTRYPOINT_GROUP) -> Iterable[EntryPoint]:
        return iter_entry_points(group)


def load_from_entry_point(entry_point: EntryPoint) -> Plugin:
    """Carefully load the plugin, raising a meaningful message in case of errors"""
    try:
        return entry_point.load()
    except Exception as ex:
        raise ErrorLoadingPlugin(entry_point=entry_point) from ex


def list_from_entry_points(
    group: str = ENTRYPOINT_GROUP,
    filtering: Callable[[EntryPoint], bool] = lambda _: True,
) -> List[Plugin]:
    """Produces a list of plugin objects for each plugin registered
    via `setuptools`_ entry point mechanism.

    Args:
        group: name of the setuptools' entry_point group where plugins is being
            registered
        filtering: function returning a boolean deciding if the entry point should be
            loaded and included (or not) in the final list. A ``True`` return means the
            plugin should be included.

    .. _setuptools: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    """  # noqa
    return [
        load_from_entry_point(e) for e in iterate_entry_points(group) if filtering(e)
    ]


class ErrorLoadingPlugin(RuntimeError):
    """There was an error loading '{plugin}'.
    Please make sure you have installed a version of the plugin that is compatible
    with {package} {version}. You can also try uninstalling it.
    """

    def __init__(self, plugin: str = "", entry_point: Optional[EntryPoint] = None):
        if entry_point and not plugin:
            plugin = getattr(entry_point, "module", entry_point.name)

        sub = dict(package=__package__, version=__version__, plugin=plugin)
        msg = dedent(self.__doc__ or "").format(**sub).splitlines()
        super().__init__(f"{msg[0]}\n{' '.join(msg[1:])}")
