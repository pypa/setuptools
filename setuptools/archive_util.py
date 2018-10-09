"""Utilities for extracting common archive formats"""

import zipfile
import tarfile
import os
import shutil
import struct
import time
import posixpath
import contextlib
from distutils.errors import DistutilsError
from distutils.dir_util import mkpath
from distutils import log

try:
    from pwd import getpwnam
except ImportError:
    getpwnam = None

try:
    from grp import getgrnam
except ImportError:
    getgrnam = None

try:
    import lzma
except:
    lzma = None

from pkg_resources import ensure_directory

__all__ = [
    "unpack_archive", "unpack_zipfile", "unpack_tarfile", "default_filter",
    "UnrecognizedFormat", "extraction_drivers", "unpack_directory",
    "make_archive",
]


class UnrecognizedFormat(DistutilsError):
    """Couldn't recognize the archive type"""


def default_filter(src, dst):
    """The default progress/filter callback; returns True for all files"""
    return dst


def unpack_archive(filename, extract_dir, progress_filter=default_filter,
        drivers=None):
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
    else:
        raise UnrecognizedFormat(
            "Not a recognized archive type: %s" % filename
        )


def unpack_directory(filename, extract_dir, progress_filter=default_filter):
    """"Unpack" a directory, using the same interface as for archives

    Raises ``UnrecognizedFormat`` if `filename` is not a directory
    """
    if not os.path.isdir(filename):
        raise UnrecognizedFormat("%s is not a directory" % filename)

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


def unpack_zipfile(filename, extract_dir, progress_filter=default_filter):
    """Unpack zip `filename` to `extract_dir`

    Raises ``UnrecognizedFormat`` if `filename` is not a zipfile (as determined
    by ``zipfile.is_zipfile()``).  See ``unpack_archive()`` for an explanation
    of the `progress_filter` argument.
    """

    if not zipfile.is_zipfile(filename):
        raise UnrecognizedFormat("%s is not a zip file" % (filename,))

    with zipfile.ZipFile(filename) as z:
        for info in z.infolist():
            name = info.filename

            # don't extract absolute paths or ones with .. in them
            if name.startswith('/') or '..' in name.split('/'):
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            target = progress_filter(name, target)
            if not target:
                continue
            if name.endswith('/'):
                # directory
                ensure_directory(target)
            else:
                # file
                ensure_directory(target)
                data = z.read(info.filename)
                with open(target, 'wb') as f:
                    f.write(data)
            unix_attributes = info.external_attr >> 16
            if unix_attributes:
                os.chmod(target, unix_attributes)


def unpack_tarfile(filename, extract_dir, progress_filter=default_filter):
    """Unpack tar/tar.gz/tar.bz2 `filename` to `extract_dir`

    Raises ``UnrecognizedFormat`` if `filename` is not a tarfile (as determined
    by ``tarfile.open()``).  See ``unpack_archive()`` for an explanation
    of the `progress_filter` argument.
    """
    try:
        tarobj = tarfile.open(filename)
    except tarfile.TarError:
        raise UnrecognizedFormat(
            "%s is not a compressed or uncompressed tar file" % (filename,)
        )
    with contextlib.closing(tarobj):
        # don't do any chowning!
        tarobj.chown = lambda *args: None
        for member in tarobj:
            name = member.name
            # don't extract absolute paths or ones with .. in them
            if not name.startswith('/') and '..' not in name.split('/'):
                prelim_dst = os.path.join(extract_dir, *name.split('/'))

                # resolve any links and to extract the link targets as normal
                # files
                while member is not None and (member.islnk() or member.issym()):
                    linkpath = member.linkname
                    if member.issym():
                        base = posixpath.dirname(member.name)
                        linkpath = posixpath.join(base, linkpath)
                        linkpath = posixpath.normpath(linkpath)
                    member = tarobj._getmember(linkpath)

                if member is not None and (member.isfile() or member.isdir()):
                    final_dst = progress_filter(name, prelim_dst)
                    if final_dst:
                        if final_dst.endswith(os.sep):
                            final_dst = final_dst[:-1]
                        try:
                            # XXX Ugh
                            tarobj._extract_member(member, final_dst)
                        except tarfile.ExtractError:
                            # chown/chmod/mkfifo/mknode/makedev failed
                            pass
        return True


extraction_drivers = unpack_directory, unpack_zipfile, unpack_tarfile


def _get_gid(name):
    """Returns a gid, given a group name."""
    if getgrnam is None or name is None:
        return None
    try:
        result = getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None

def _get_uid(name):
    """Returns an uid, given a user name."""
    if getpwnam is None or name is None:
        return None
    try:
        result = getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None

def _find_sorted(base_dir):
    yield base_dir
    for path in sorted(
        os.path.join(root, name)
        for root, dirs, files in os.walk(base_dir)
        for name in dirs + files
    ):
        yield path


def make_tarball(base_name, base_dir, compress="gzip", verbose=0, dry_run=0,
                 owner=None, group=None, timestamp=None):
    """Create a (possibly compressed) tar file from all the files under
    'base_dir'.

    'compress' must be "gzip" (the default), "bzip2", "xz", "compress", or
    None.  ("compress" will be deprecated in Python 3.2)

    'owner' and 'group' can be used to define an owner and a group for the
    archive that is being built. If not provided, the current owner and group
    will be used.

    'compress' is used to set the header timestamp when using "gzip".

    The output tar file will be named 'base_dir' +  ".tar", possibly plus
    the appropriate compression extension (".gz", ".bz2", ".xz" or ".Z").

    Returns the output filename.
    """
    tar_compression = {'gzip': 'gz', 'bzip2': 'bz2', 'xz': 'xz', None: ''}
    compress_ext = {'gzip': '.gz', 'bzip2': '.bz2', 'xz': '.xz'}

    # flags for compression program, each element of list will be an argument
    if compress is not None and compress not in compress_ext.keys():
        raise ValueError(
              "bad value for 'compress': must be None, 'gzip', 'bzip2', "
              "'xz' or 'compress'")

    archive_name = base_name + '.tar'
    archive_name += compress_ext.get(compress, '')

    mkpath(os.path.dirname(archive_name), dry_run=dry_run)

    log.info('Creating tar archive')

    if dry_run:
        return archive_name

    uid = _get_uid(owner)
    gid = _get_gid(group)

    def _set_uid_gid(tarinfo):
        if gid is not None:
            tarinfo.gid = gid
            tarinfo.gname = group
        if uid is not None:
            tarinfo.uid = uid
            tarinfo.uname = owner
        if timestamp is not None:
            tarinfo.mtime = timestamp
        return tarinfo

    tar = tarfile.open(archive_name, 'w|%s' % tar_compression[compress])
    try:
        for path in _find_sorted(base_dir):
            tar.add(path, recursive=False, filter=_set_uid_gid)
    finally:
        tar.close()

    # Patch gzip header to use the timestamp
    # provided instead of the current time.
    if compress == 'gzip' and timestamp is not None:
        with open(archive_name, 'r+b') as fp:
            fp.seek(4)
            fp.write(struct.pack('<L', timestamp))

    return archive_name

def make_zipfile(base_name, base_dir, verbose=0, dry_run=0, timestamp=None):
    """Create a zip file from all the files under 'base_dir'.

    The output zip file will be named 'base_name' + ".zip".
    Returns the name of the output zip file.
    """
    zip_filename = base_name + ".zip"
    mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

    log.info("creating '%s' and adding '%s' to it",
             zip_filename, base_dir)

    if dry_run:
        return zip_filename

    compression = zipfile.ZIP_DEFLATED
    try:
        zip = zipfile.ZipFile(zip_filename, "w",
                              compression=compression)
    except RuntimeError:
        compression = zipfile.ZIP_STORED
        zip = zipfile.ZipFile(zip_filename, "w",
                              compression=compression)
    try:
        for path in filter(os.path.isfile, _find_sorted(base_dir)):
            st = os.stat(path)
            date_time = time.localtime(
                st.st_mtime if timestamp is None else timestamp
            )[0:6]
            info = zipfile.ZipInfo(path, date_time)
            info.compress_type = compression
            info.external_attr = st.st_mode << 16
            with open(path, 'rb') as fp:
                zip.writestr(info, fp.read())
            log.info("adding '%s'", path)
    finally:
        zip.close()

    return zip_filename

ARCHIVE_FORMATS = {
    'gztar': (make_tarball, [('compress', 'gzip')], "gzip'ed tar-file"),
    'bztar': (make_tarball, [('compress', 'bzip2')], "bzip2'ed tar-file"),
    'tar':   (make_tarball, [('compress', None)], "uncompressed tar file"),
    'zip':   (make_zipfile, [],"ZIP file")
    }
if lzma is not None:
    ARCHIVE_FORMATS.update({
        'xztar': (make_tarball, [('compress', 'xz')], "xz'ed tar-file"),
    })

def check_archive_formats(formats):
    """Returns the first format from the 'format' list that is unknown.

    If all formats are known, returns None
    """
    for format in formats:
        if format not in ARCHIVE_FORMATS:
            return format
    return None

def make_archive(base_name, format, root_dir=None, base_dir=None, verbose=0,
                 dry_run=0, owner=None, group=None, timestamp=None):
    """Create an archive file (eg. zip or tar).

    'base_name' is the name of the file to create, minus any format-specific
    extension; 'format' is the archive format: one of "zip", "tar", "gztar",
    "bztar", "xztar", or "ztar".

    'root_dir' is a directory that will be the root directory of the
    archive; ie. we typically chdir into 'root_dir' before creating the
    archive.  'base_dir' is the directory where we start archiving from;
    ie. 'base_dir' will be the common prefix of all files and
    directories in the archive.  'root_dir' and 'base_dir' both default
    to the current directory.  Returns the name of the archive file.

    'owner' and 'group' are used when creating a tar archive. By default,
    uses the current owner and group.

    'timestamp' is used when creating a gzip'ed tar-file, to set the
    gzip header timestamp.
    """
    save_cwd = os.getcwd()
    if root_dir is not None:
        log.debug("changing into '%s'", root_dir)
        base_name = os.path.abspath(base_name)
        if not dry_run:
            os.chdir(root_dir)

    if base_dir is None:
        base_dir = os.curdir

    kwargs = {'dry_run': dry_run}

    try:
        format_info = ARCHIVE_FORMATS[format]
    except KeyError:
        raise ValueError("unknown archive format '%s'" % format)

    func = format_info[0]
    for arg, val in format_info[1]:
        kwargs[arg] = val

    if format != 'zip':
        kwargs['owner'] = owner
        kwargs['group'] = group

    if timestamp is not None:
        kwargs['timestamp'] = timestamp

    try:
        filename = func(base_name, base_dir, **kwargs)
    finally:
        if root_dir is not None:
            log.debug("changing back to '%s'", save_cwd)
            os.chdir(save_cwd)

    return filename
