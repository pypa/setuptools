from collections.abc import Iterable
from typing import TypeVar, overload

from _typeshed import BytesPath, StrOrBytesPath, StrPath

_StrPathT = TypeVar("_StrPathT", bound=StrPath)
_BytesPathT = TypeVar("_BytesPathT", bound=BytesPath)

@overload
def copy_file(
    src: StrPath,
    dst: _StrPathT,
    preserve_mode: bool = True,
    preserve_times: bool = True,
    update: bool = False,
    link: str | None = None,
    verbose: bool = True,
    dry_run: bool = False,
) -> tuple[_StrPathT | str, bool]: ...
@overload
def copy_file(
    src: BytesPath,
    dst: _BytesPathT,
    preserve_mode: bool = True,
    preserve_times: bool = True,
    update: bool = False,
    link: str | None = None,
    verbose: bool = True,
    dry_run: bool = False,
) -> tuple[_BytesPathT | bytes, bool]: ...
@overload
def move_file(
    src: StrPath,
    dst: _StrPathT,
    verbose: bool = False,
    dry_run: bool = False,
) -> _StrPathT | str: ...
@overload
def move_file(
    src: BytesPath,
    dst: _BytesPathT,
    verbose: bool = False,
    dry_run: bool = False,
) -> _BytesPathT | bytes: ...
def write_file(filename: StrOrBytesPath, contents: Iterable[str]) -> None: ...
