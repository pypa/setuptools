from collections.abc import Callable, Iterable
from typing import Literal, TypeVar

from _typeshed import StrOrBytesPath

_SourcesT = TypeVar("_SourcesT", bound=StrOrBytesPath)
_TargetsT = TypeVar("_TargetsT", bound=StrOrBytesPath)

def newer(source: StrOrBytesPath, target: StrOrBytesPath) -> bool: ...
def newer_pairwise(
    sources: Iterable[_SourcesT],
    targets: Iterable[_TargetsT],
    newer: Callable[[_SourcesT, _TargetsT], bool] = newer,
) -> tuple[list[_SourcesT], list[_TargetsT]]: ...
def newer_group(
    sources: Iterable[StrOrBytesPath],
    target: StrOrBytesPath,
    missing: Literal["error", "ignore", "newer"] = "error",
) -> bool: ...
def newer_pairwise_group(
    sources: Iterable[_SourcesT],
    targets: Iterable[_TargetsT],
    *,
    newer: Callable[[_SourcesT, _TargetsT], bool] = newer,
) -> tuple[list[_SourcesT], list[_TargetsT]]: ...
