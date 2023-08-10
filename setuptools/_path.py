import os
import sys
from typing import Union
from pathlib import Path

_Path = Union[str, os.PathLike]


def ensure_directory(path):
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)


def safe_samefile(path1: _Path, path2: _Path) -> bool:
    """Similar to os.path.samefile but returns False instead of raising exception"""
    try:
        return os.path.samefile(path1, path2)
    except OSError:
        return False


def same_path(p1: _Path, p2: _Path) -> bool:
    """Differs from os.path.samefile because it does not require paths to exist.
    Purely string based (no comparison between i-nodes).
    >>> same_path("a/b", "./a/b")
    True
    >>> same_path("a/b", "a/./b")
    True
    >>> same_path("a/b", "././a/b")
    True
    >>> same_path("a/b", "./a/b/c/..")
    True
    >>> same_path("a/b", "../a/b/c")
    False
    >>> same_path("a", "a/b")
    False
    """
    return normpath(p1) == normpath(p2)


def normpath(filename: _Path) -> str:
    """Normalize a file/dir name for comparison purposes."""
    # See pkg_resources.normalize_path for notes about cygwin
    file = os.path.abspath(filename) if sys.platform == 'cygwin' else filename
    return os.path.normcase(os.path.realpath(os.path.normpath(file)))


def besteffort_internal_path(root: _Path, file: _Path) -> str:
    """Process ``file`` and return an equivalent relative path contained into root
    (POSIX style, with no ``..`` segments).
    It may raise an ``ValueError`` if that is not possible.
    If ``file`` is not absolute, it will be assumed to be relative to ``root``.
    """
    path = os.path.join(root, file)  # will ignore root if file is absolute
    resolved = Path(path).resolve()
    logical = Path(os.path.abspath(path))

    # Prefer logical paths, since a parent directory can be symlinked inside root
    if same_path(resolved, logical) or safe_samefile(resolved, logical):
        return logical.relative_to(root).as_posix()

    # Since ``resolved`` is used, it makes sense to resolve root too.
    return resolved.relative_to(Path(root).resolve()).as_posix()
