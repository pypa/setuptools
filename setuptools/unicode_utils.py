import unicodedata
import sys

from .compat import py39


# HFS Plus uses decomposed UTF-8
def decompose(path):
    if isinstance(path, str):
        return unicodedata.normalize('NFD', path)
    try:
        path = path.decode('utf-8')
        path = unicodedata.normalize('NFD', path)
        path = path.encode('utf-8')
    except UnicodeError:
        pass  # Not UTF-8
    return path


def filesys_decode(path):
    """
    Ensure that the given path is decoded,
    ``None`` when no expected encoding works
    """

    if isinstance(path, str):
        return path

    fs_enc = sys.getfilesystemencoding() or 'utf-8'
    candidates = fs_enc, 'utf-8'

    for enc in candidates:
        try:
            return path.decode(enc)
        except UnicodeDecodeError:
            continue

    return None


def try_encode(string, enc):
    "turn unicode encoding into a functional routine"
    try:
        return string.encode(enc)
    except UnicodeEncodeError:
        return None


def _read_utf8_with_fallback(file: str, fallback_encoding=py39.LOCALE_ENCODING) -> str:
    """
    First try to read the file with UTF-8, if there is an error fallback to a
    different encoding ("locale" by default). Returns the content of the file.
    Also useful when reading files that might have been produced by an older version of
    setuptools.
    """
    try:
        with open(file, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:  # pragma: no cover
        with open(file, "r", encoding=fallback_encoding) as f:
            return f.read()
