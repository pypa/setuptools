"""Utilities for extracting common archive formats"""

import contextlib
import ntpath
import os
import posixpath
import shutil
import tarfile
import zipfile

if not hasattr(tarfile, "data_filter"):  # pragma: no cover
    # CPython added the PEP 706 extraction filters in 3.12 and backported
    # them to 3.10.12 / 3.11.4. On older patch releases, use the vendored
    # backport so the hardened, public filter API is always available.
    from ._vendor.backports import tarfile  # noqa: E402  # isort:skip

from ._path import ensure_directory

from distutils.errors import DistutilsError

__all__ = [
    "UnrecognizedFormat",
    "UnsafeMember",
    "default_filter",
    "extraction_drivers",
    "unpack_archive",
    "unpack_directory",
    "unpack_tarfile",
    "unpack_zipfile",
]


class UnrecognizedFormat(DistutilsError):
    """Couldn't recognize the archive type"""


class UnsafeMember(DistutilsError):
    """An archive member that would be extracted outside the destination

    Deliberately not an `UnrecognizedFormat`, which ``unpack_archive`` catches
    to fall through to the next driver; an unsafe member must abort the
    extraction rather than hand the archive to another driver.
    """


def default_filter(src, dst):
    """The default progress/filter callback; returns True for all files"""
    return dst


def _resolve_dest(extract_dir, name):
    r"""
    Return the path where archive member `name` belongs under `extract_dir`,
    raising `UnsafeMember` if the member would be written outside of it.

    Both the tar and zip formats specify '/' as the only path separator, so a
    backslash is never a legitimate separator in a member name and must not be
    allowed to act as one on Windows (GHSA-grgh-hr87-3jpw). Names that are
    absolute, drive-qualified, or UNC are rejected for the same reason.

    A directory member keeps its trailing separator, as callers rely on it to
    distinguish a directory from a file.

    >>> _resolve_dest('dest', 'sub/file.txt') == os.path.join('dest', 'sub', 'file.txt')
    True
    >>> _resolve_dest('dest', 'sub/dir/') == os.path.join('dest', 'sub', 'dir', '')
    True
    >>> _resolve_dest('dest', '..\\escaped.txt')
    Traceback (most recent call last):
    ...
    setuptools.archive_util.UnsafeMember: '..\\escaped.txt' would be extracted outside of 'dest'
    """
    if name.startswith('/') or '\\' in name or ntpath.splitdrive(name)[0]:
        raise UnsafeMember(f"{name!r} would be extracted outside of {extract_dir!r}")

    parts = name.split('/')

    if '..' in parts:
        raise UnsafeMember(f"{name!r} would be extracted outside of {extract_dir!r}")

    dest = os.path.join(extract_dir, *parts)

    # Belt and braces: confirm the result really does resolve within the root,
    # catching an escape through a symlink already present in the destination.
    root = os.path.realpath(extract_dir)
    resolved = os.path.realpath(dest)
    if resolved != root and not resolved.startswith(os.path.join(root, '')):
        raise UnsafeMember(f"{name!r} would be extracted outside of {extract_dir!r}")

    return dest


def unpack_archive(
    filename, extract_dir, progress_filter=default_filter, drivers=None
) -> None:
    """Unpack `filename` to `extract_dir`, or raise ``UnrecognizedFormat``

    `progress_filter` is a function taking two arguments: a source path
    internal to the archive ('/'-separated), and a filesystem path where it
    will be extracted.  The callback must return the desired extract path
    (which may be the same as the one passed in), or else ``None`` to skip
    that file or directory.  The callback can thus be used to report on the
    progress of the extraction, as well as to filter the items extracted or
    alter their extraction paths.

    `drivers`, if supplied, must be a non-empty sequence of functions with the
    same signature as this function (minus the `drivers` argument), that raise
    ``UnrecognizedFormat`` if they do not support extracting the designated
    archive type.  The `drivers` are tried in sequence until one is found that
    does not raise an error, or until all are exhausted (in which case
    ``UnrecognizedFormat`` is raised).  If you do not supply a sequence of
    drivers, the module's ``extraction_drivers`` constant will be used, which
    means that ``unpack_zipfile`` and ``unpack_tarfile`` will be tried, in that
    order.
    """
    for driver in drivers or extraction_drivers:
        try:
            driver(filename, extract_dir, progress_filter)
        except UnrecognizedFormat:
            continue
        else:
            return
    raise UnrecognizedFormat(f"Not a recognized archive type: {filename}")


def unpack_directory(filename, extract_dir, progress_filter=default_filter) -> None:
    """ "Unpack" a directory, using the same interface as for archives

    Raises ``UnrecognizedFormat`` if `filename` is not a directory
    """
    if not os.path.isdir(filename):
        raise UnrecognizedFormat(f"{filename} is not a directory")

    paths = {
        filename: ('', extract_dir),
    }
    for base, dirs, files in os.walk(filename):
        src, dst = paths[base]
        for d in dirs:
            paths[os.path.join(base, d)] = src + d + '/', os.path.join(dst, d)
        for f in files:
            target = os.path.join(dst, f)
            target = progress_filter(src + f, target)
            if not target:
                # skip non-files
                continue
            ensure_directory(target)
            f = os.path.join(base, f)
            shutil.copyfile(f, target)
            shutil.copystat(f, target)


def unpack_zipfile(filename, extract_dir, progress_filter=default_filter) -> None:
    """Unpack zip `filename` to `extract_dir`

    Raises ``UnrecognizedFormat`` if `filename` is not a zipfile (as determined
    by ``zipfile.is_zipfile()``).  See ``unpack_archive()`` for an explanation
    of the `progress_filter` argument.
    """

    if not zipfile.is_zipfile(filename):
        raise UnrecognizedFormat(f"{filename} is not a zip file")

    with zipfile.ZipFile(filename) as z:
        _unpack_zipfile_obj(z, extract_dir, progress_filter)


def _unpack_zipfile_obj(zipfile_obj, extract_dir, progress_filter=default_filter):
    """Internal/private API used by other parts of setuptools.
    Similar to ``unpack_zipfile``, but receives an already opened :obj:`zipfile.ZipFile`
    object instead of a filename.
    """
    for info in zipfile_obj.infolist():
        name = info.filename

        target = _resolve_dest(extract_dir, name)
        target = progress_filter(name, target)
        if not target:
            continue
        if name.endswith('/'):
            # directory
            ensure_directory(target)
        else:
            # file
            ensure_directory(target)
            data = zipfile_obj.read(info.filename)
            with open(target, 'wb') as f:
                f.write(data)
        unix_attributes = info.external_attr >> 16
        if unix_attributes:
            os.chmod(target, unix_attributes)


def _resolve_tar_file_or_dir(members_by_name, tar_member_obj):
    """Resolve any links and extract link targets as normal files.

    ``members_by_name`` maps member names to their (last-declared) TarInfo,
    matching how tarfile used to resolve link names internally: its private
    lookup scanned members bottom-to-top, so a repeated name resolved to the
    last occurrence — which is what keeps a dict built in iteration order.
    """
    while tar_member_obj is not None and (
        tar_member_obj.islnk() or tar_member_obj.issym()
    ):
        linkpath = tar_member_obj.linkname
        if tar_member_obj.issym():
            base = posixpath.dirname(tar_member_obj.name)
            linkpath = posixpath.join(base, linkpath)
            linkpath = posixpath.normpath(linkpath)
        tar_member_obj = members_by_name.get(linkpath)

    is_file_or_dir = tar_member_obj is not None and (
        tar_member_obj.isfile() or tar_member_obj.isdir()
    )
    if is_file_or_dir:
        return tar_member_obj

    raise LookupError('Got unknown file type')


def _apply_data_filter(member, extract_dir):
    """Run ``tarfile.data_filter`` on ``member``, translating rejection.

    The stdlib's data filter treats an unsafe member (absolute or escaping
    link target, special file) as fatal by raising ``tarfile.FilterError``;
    only ``extractall`` with a per-member error handler or the
    ``fully_trusted`` filter turns that into a skip. Extraction here must
    fail loudly instead of silently dropping the member, so the rejection
    is translated to ``UnsafeMember`` -- a ``DistutilsError``, deliberately
    not an ``UnrecognizedFormat``, so ``unpack_archive`` cannot fall through
    to another driver with files missing.
    """
    try:
        return tarfile.data_filter(member, extract_dir)
    except tarfile.FilterError as e:
        raise UnsafeMember(
            f"{member.name!r} was rejected by the tar data filter: {e}"
        ) from e


def _iter_open_tar(tar_obj, extract_dir, progress_filter):
    """Emit member-destination pairs from a tar archive.

    Every emitted member has been vetted through :func:`tarfile.data_filter`
    (PEP 706), so extraction inherits the stdlib's data-extraction hardening:
    sanitized permission bits (setuid/setgid/sticky stripped), dropped
    ownership (the filter nulls uid/gid, which makes tarfile's chown a
    -1/-1 no-op), rejected absolute and escaping link targets, and rejected
    special files — rather than setuptools hand-maintaining pieces of that
    logic against private ``tarfile`` APIs.

    ``progress_filter`` still runs afterwards on the preliminary destination
    and may redirect or skip members as documented (see ``unpack_archive``),
    which is why containment is validated here against ``extract_dir``
    rather than against the callback-chosen destination.
    """
    with contextlib.closing(tar_obj):
        # Index every member by name up front so a link member can resolve its
        # target, matching tarfile's private lookup: it scanned members
        # bottom-to-top and returned the first hit, i.e. the *last* declared
        # member of that name — which is what a dict built in iteration order
        # keeps. Members are needed here either way, as data_filter and the
        # link resolution both require the whole catalog.
        members = tar_obj.getmembers()
        members_by_name: dict[str, tarfile.TarInfo] = {
            member.name: member for member in members
        }
        for member in members:
            name = member.name
            prelim_dst = _resolve_dest(extract_dir, name)

            try:
                resolved = _resolve_tar_file_or_dir(members_by_name, member)
            except LookupError:
                # Either a link whose target is not in the archive or a
                # special file. Give the data filter the final word: it
                # rejects absolute/escaping links and special files, and
                # translating that rejection raises loudly. A merely
                # dangling-but-safe link passes the filter and is skipped,
                # matching the historical behavior.
                _apply_data_filter(member, extract_dir)
                continue

            resolved = _apply_data_filter(resolved, extract_dir)

            final_dst = progress_filter(name, prelim_dst)
            if not final_dst:
                continue

            if final_dst.endswith(os.sep):
                final_dst = final_dst[:-1]

            yield resolved, final_dst


def unpack_tarfile(filename, extract_dir, progress_filter=default_filter) -> bool:
    """Unpack tar/tar.gz/tar.bz2 `filename` to `extract_dir`

    Raises ``UnrecognizedFormat`` if `filename` is not a tarfile (as determined
    by ``tarfile.open()``).  See ``unpack_archive()`` for an explanation
    of the `progress_filter` argument.
    """
    try:
        tarobj = tarfile.open(filename)  # noqa: SIM115 # handle managed explicitly
    except tarfile.TarError as e:
        raise UnrecognizedFormat(
            f"{filename} is not a compressed or uncompressed tar file"
        ) from e

    for member, final_dst in _iter_open_tar(
        tarobj,
        extract_dir,
        progress_filter,
    ):
        try:
            # XXX Ugh
            tarobj._extract_member(member, final_dst)
        except tarfile.ExtractError:
            # chown/chmod/mkfifo/mknode/makedev failed
            pass

    return True


extraction_drivers = unpack_directory, unpack_zipfile, unpack_tarfile
