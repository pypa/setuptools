import io
import os
import tarfile
import zipfile

import pytest

from setuptools import archive_util

from .compat.py39 import os_helper


@pytest.fixture
def tarfile_with_unicode(tmpdir):
    """
    Create a tarfile containing only a file whose name is
    a zero byte file called testimäge.png.
    """
    tarobj = io.BytesIO()

    with tarfile.open(fileobj=tarobj, mode="w:gz") as tgz:
        data = b""

        filename = "testimäge.png"

        t = tarfile.TarInfo(filename)
        t.size = len(data)

        tgz.addfile(t, io.BytesIO(data))

    target = tmpdir / 'unicode-pkg-1.0.tar.gz'
    with open(str(target), mode='wb') as tf:
        tf.write(tarobj.getvalue())
    return str(target)


@pytest.mark.xfail(reason="#710 and #712")
def test_unicode_files(tarfile_with_unicode, tmpdir):
    target = tmpdir / 'out'
    archive_util.unpack_archive(tarfile_with_unicode, str(target))


#: Member names that must never be extracted, whatever the platform. The
#: backslash variants only escape on Windows, but are rejected everywhere so
#: that the behavior (and this test) is not platform-dependent.
TRAVERSAL_NAMES = [
    '../escaped.txt',
    'sub/../../escaped.txt',
    '..\\escaped.txt',
    'sub\\..\\..\\escaped.txt',
    '/absolute.txt',
    'C:escaped.txt',
]


def _make_tarfile(path, names):
    with tarfile.open(path, mode='w:gz') as tgz:
        for name in names:
            data = name.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tgz.addfile(info, io.BytesIO(data))
    return str(path)


def _make_zipfile(path, names):
    with zipfile.ZipFile(path, mode='w') as zf:
        for name in names:
            # Assign the name after construction; ZipInfo rewrites os.sep to
            # '/' on Windows, which would defeat the backslash cases.
            info = zipfile.ZipInfo()
            info.filename = name
            zf.writestr(info, name.encode())
    return str(path)


drivers = pytest.mark.parametrize(
    ('suffix', 'make_archive'),
    [('.tar.gz', _make_tarfile), ('.zip', _make_zipfile)],
    ids=['tar', 'zip'],
)


@drivers
@pytest.mark.parametrize('name', TRAVERSAL_NAMES)
def test_unpack_rejects_traversal(tmp_path, name, suffix, make_archive):
    """
    A member that would land outside the extraction directory aborts the
    extraction rather than being silently skipped (GHSA-grgh-hr87-3jpw).
    """
    archive = make_archive(tmp_path / f'malicious{suffix}', [name])
    target = tmp_path / 'dest'

    with pytest.raises(archive_util.UnsafeMember):
        archive_util.unpack_archive(archive, str(target))

    # nothing was written outside of the target
    assert {path.name for path in tmp_path.iterdir()} <= {
        f'malicious{suffix}',
        'dest',
    }


@drivers
def test_unpack_extracts_safe_members(tmp_path, suffix, make_archive):
    """
    Ordinary members are unaffected by the containment check.
    """
    names = ['inside.txt', 'sub/nested.txt', './dot-prefixed.txt']
    archive = make_archive(tmp_path / f'safe{suffix}', names)
    target = tmp_path / 'dest'

    archive_util.unpack_archive(archive, str(target))

    assert (target / 'inside.txt').read_text(encoding='utf-8') == 'inside.txt'
    assert (target / 'sub' / 'nested.txt').exists()
    assert (target / 'dot-prefixed.txt').exists()


def test_unpack_zipfile_creates_directory_members(tmp_path):
    """
    A zip directory entry still creates the directory itself, not just its
    parent.
    """
    archive = _make_zipfile(tmp_path / 'dirs.zip', ['empty/'])
    target = tmp_path / 'dest'

    archive_util.unpack_archive(archive, str(target))

    assert (target / 'empty').is_dir()


@pytest.mark.skipif(not os_helper.can_symlink(), reason='Symlink support required')
def test_resolve_dest_rejects_symlinked_escape(tmp_path):
    """
    A member name that is harmless in isolation must still not escape through
    a symlink that already exists in the extraction directory.
    """
    target = tmp_path / 'dest'
    target.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (target / 'sub').symlink_to(outside, target_is_directory=True)

    with pytest.raises(archive_util.UnsafeMember):
        archive_util._resolve_dest(str(target), 'sub/file.txt')

    assert archive_util._resolve_dest(str(target), 'ok/file.txt')


def _make_tarfile_with_setuid(path):
    with tarfile.open(path, mode='w') as tar:
        data = b'echo hi'
        info = tarfile.TarInfo('script.sh')
        info.size = len(data)
        info.mode = 0o4755  # setuid + rwxr-xr-x
        tar.addfile(info, io.BytesIO(data))
    return str(path)


def test_iter_open_tar_applies_data_filter(tmp_path):
    """
    Each member handed to the driver is the tarfile data filter's sanitized
    copy: high mode bits (setuid/setgid/sticky) are stripped and archive
    ownership is cleared, so none of it reaches the filesystem (#5328).
    """
    archive = _make_tarfile_with_setuid(tmp_path / 'setuid.tar')

    with tarfile.open(archive) as tar:
        members = list(
            archive_util._iter_open_tar(
                tar, str(tmp_path / 'dest'), archive_util.default_filter
            )
        )

    assert len(members) == 1
    member, dst = members[0]
    assert member.mode & 0o7000 == 0
    assert member.mode & 0o755 == 0o755
    assert member.uid is None
    assert member.gid is None
    assert dst == os.path.join(str(tmp_path / 'dest'), 'script.sh')


@pytest.mark.skipif(os.name != 'posix', reason='POSIX permission bits required')
def test_unpack_tarfile_strips_high_mode_bits(tmp_path):
    """
    A setuid regular file is extracted without the setuid bit (PEP 706).
    """
    archive = _make_tarfile_with_setuid(tmp_path / 'setuid.tar')
    target = tmp_path / 'dest'

    archive_util.unpack_tarfile(archive, str(target))

    extracted = (target / 'script.sh').stat().st_mode
    assert extracted & 0o7000 == 0
    assert extracted & 0o500  # still readable/executable


def test_unpack_tarfile_resolves_links_to_targets(tmp_path):
    """
    Link members are materialized as copies of their archive-relative
    targets, resolved through the public member listing (#5328).
    """
    archive = tmp_path / 'links.tar'
    with tarfile.open(archive, mode='w') as tar:
        dir_info = tarfile.TarInfo('sub/')
        dir_info.type = tarfile.DIRTYPE
        tar.addfile(dir_info)

        data = b'payload'
        file_info = tarfile.TarInfo('sub/data.txt')
        file_info.size = len(data)
        tar.addfile(file_info, io.BytesIO(data))

        file_link = tarfile.TarInfo('filelink')
        file_link.type = tarfile.LNKTYPE
        file_link.linkname = 'sub/data.txt'
        tar.addfile(file_link)

    target = tmp_path / 'dest'
    archive_util.unpack_tarfile(archive, str(target))

    assert (target / 'filelink').is_file()
    assert (target / 'filelink').read_bytes() == b'payload'
