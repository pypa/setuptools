from collections.abc import Iterable

from _typeshed import StrOrBytesPath, StrPath

def mkpath(
    name: str,
    mode: int = 0o777,
    verbose: bool = True,
    dry_run: bool = False,
) -> list[str]: ...
def create_tree(
    base_dir: StrPath,
    files: Iterable[StrPath],
    mode: int = 0o777,
    verbose: bool = True,
    dry_run: bool = False,
) -> None: ...
def copy_tree(
    src: StrPath,
    dst: str,
    preserve_mode: bool = True,
    preserve_times: bool = True,
    preserve_symlinks: bool = False,
    update: bool = False,
    verbose: bool = True,
    dry_run: bool = False,
) -> list[str]: ...
def remove_tree(
    directory: StrOrBytesPath, verbose: bool = True, dry_run: bool = False
) -> None: ...
