import io
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
