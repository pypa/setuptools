import csv
import hashlib
import io
import itertools
import logging
import os
import stat
import time
from base64 import urlsafe_b64encode
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple, Union
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .discovery import _Filter

_Path = Union[str, Path]
_Timestamp = Tuple[int, int, int, int, int, int]
_TextOrIter = Union[str, bytes, Iterable[str], Iterable[bytes]]

_HASH_ALG = "sha256"
_HASH_BUF_SIZE = 65536
_MINIMUM_TIMESTAMP = 315532800  # 1980-01-01 00:00:00 UTC
_DEFAULT_COMPRESSION = ZIP_DEFLATED
_WHEEL_VERSION = "1.0"
_META_TEMPLATE = f"""\
Wheel-Version: {_WHEEL_VERSION}
Generator: {{generator}}
Root-Is-Purelib: {{root_is_purelib}}
"""

_logger = logging.getLogger(__name__)


class WheelBuilder:
    """Wrapper around ZipFile that abstracts some aspects of creating a ``.whl`` file
    It should be used as a context manager and before closing will add the ``WHEEL``
    and ``RECORD`` files to the end of the archive.
    The caller is responsible for writing files/dirs in a suitable order,
    (which includes ensuring ``.dist-info`` is written last).
    """

    def __init__(
        self,
        path: _Path,
        root_is_purelib: bool = True,
        compression: int = _DEFAULT_COMPRESSION,
        generator: Optional[str] = None,
        timestamp: Optional[int] = None,
    ):
        self._path = Path(path)
        self._root_is_purelib = root_is_purelib
        self._generator = generator
        self._compression = compression
        self._zip = ZipFile(self._path, "w", compression=compression)
        self._records: Dict[str, Tuple[str, int]] = {}

        basename = str(self._path.with_suffix("").name)
        parts = basename.split("-")
        self._distribution, self._version = parts[:2]
        self._tags = parts[-3:]
        self._build = parts[2] if len(parts) > 5 else ""
        self._dist_info = f"{self._distribution}-{self._version}.dist-info"
        self._timestamp = _get_timestamp(timestamp, int(time.time()))
        assert len(self._tags), f"Invalid wheel name: {self._path}"

    def __enter__(self) -> "WheelBuilder":
        self._zip.__enter__()
        _logger.debug(f"creating '{str(self._path)!r}'")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._add_wheel_meta()
        self._save_record()
        return self._zip.__exit__(exc_type, exc_value, traceback)

    def _default_generator(self) -> str:
        from setuptools.version import __version__

        return f"setuptools ({__version__})"

    def add_existing_file(self, arcname: str, file: _Path):
        """Add a file that already exists in the file system to the wheel."""
        hashsum = hashlib.new(_HASH_ALG)
        file_stat = os.stat(file)
        zipinfo = ZipInfo(arcname, self._timestamp)
        attr = stat.S_IMODE(file_stat.st_mode) | stat.S_IFMT(file_stat.st_mode)
        zipinfo.external_attr = attr << 16
        zipinfo.compress_type = self._compression

        with open(file, "rb") as src, self._zip.open(zipinfo, "w") as dst:
            while True:
                buffer = src.read(_HASH_BUF_SIZE)
                if not buffer:
                    file_size = src.tell()
                    break
                dst.write(buffer)
                hashsum.update(buffer)

        _logger.debug(f"adding {str(arcname)!r} [{attr:o}]")
        hash_digest = urlsafe_b64encode(hashsum.digest()).decode('ascii').rstrip('=')
        self._records[arcname] = (hash_digest, file_size)

    def add_tree(
        self, path: _Path, prefix: Optional[str] = None, exclude: Iterable[str] = ()
    ):
        """
        Add the file tree **UNDER** ``path`` to the wheel file (does not include
        the parent directory itself).
        You can use ``prefix`` to create a new parent directory.
        """
        should_exclude = _Filter(*exclude)
        for root, dirs, files in os.walk(path):
            # Use sorted to improve determinism.
            dirs[:] = [x for x in sorted(dirs) if x != "__pycache__"]
            for name in sorted(files):
                file = os.path.normpath(os.path.join(root, name))
                arcname = os.path.relpath(file, path).replace(os.path.sep, "/")
                if not os.path.isfile(file) or should_exclude(arcname):
                    continue
                if prefix:
                    arcname = os.path.join(prefix, arcname)
                self.add_existing_file(arcname, file)

    def new_file(self, arcname: str, contents: _TextOrIter, permissions: int = 0o664):
        """
        Create a new entry in the wheel named ``arcname`` that contains
        the UTF-8 text specified by ``contents``.
        """
        zipinfo = ZipInfo(arcname, self._timestamp)
        zipinfo.external_attr = (permissions | stat.S_IFREG) << 16
        zipinfo.compress_type = self._compression
        hashsum = hashlib.new(_HASH_ALG)
        file_size = 0
        iter_contents = [contents] if isinstance(contents, (str, bytes)) else contents
        with self._zip.open(zipinfo, "w") as fp:
            for part in iter_contents:
                bpart = bytes(part, "utf-8") if isinstance(part, str) else part
                file_size += fp.write(bpart)
                hashsum.update(bpart)
        hash_digest = urlsafe_b64encode(hashsum.digest()).decode('ascii').rstrip('=')
        self._records[arcname] = (hash_digest, file_size)

    def _save_record(self):
        arcname = f"{self._dist_info}/RECORD"
        zipinfo = ZipInfo(arcname, self._timestamp)
        zipinfo.external_attr = (0o664 | stat.S_IFREG) << 16
        zipinfo.compress_type = self._compression
        out = self._zip.open(zipinfo, "w")
        buf = io.TextIOWrapper(out, encoding="utf-8")
        with out, buf:
            writer = csv.writer(buf, delimiter=",", quotechar='"', lineterminator="\n")
            for file, (hash_digest, size) in self._records.items():
                writer.writerow((file, f"{_HASH_ALG}={hash_digest}", size))
            writer.writerow((arcname, "", ""))

    def _add_wheel_meta(self):
        arcname = f"{self._dist_info}/WHEEL"
        beginning = _META_TEMPLATE.format(
            generator=self._generator or self._default_generator(),
            root_is_purelib=self._root_is_purelib,
        )
        impl_tag, abi_tag, plat_tag = self._tags
        tags = (
            f"Tag: {impl}-{abi}-{plat}\n"
            for impl in impl_tag.split(".")
            for abi in abi_tag.split(".")
            for plat in plat_tag.split(".")
        )
        build = [f"Build: {self._build}\n"] if self._build else []
        contents = itertools.chain([beginning], tags, build)
        self.new_file(arcname, contents)


def _get_timestamp(
    given: Optional[int] = None,
    fallback: int = _MINIMUM_TIMESTAMP,
) -> _Timestamp:
    timestamp = given or int(os.environ.get("SOURCE_DATE_EPOCH", fallback))
    timestamp = max(timestamp, _MINIMUM_TIMESTAMP)
    return time.gmtime(timestamp)[0:6]
