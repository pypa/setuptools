# coding: utf-8

from __future__ import unicode_literals

from contextlib import contextmanager
from os.path import splitdrive
import io
import os
import sys
import tarfile

from distutils.spawn import find_executable, spawn

from setuptools.extern import six

import pytest

from setuptools import archive_util

try:
    import grp
    import pwd
    UID_GID_SUPPORT = True
except ImportError:
    UID_GID_SUPPORT = False

try:
    import zipfile
    ZIP_SUPPORT = True
except ImportError:
    ZIP_SUPPORT = find_executable('zip')

try:
    import zlib
    ZLIB_SUPPORT = True
except ImportError:
    ZLIB_SUPPORT = False

try:
    import bz2
except ImportError:
    bz2 = None

try:
    import lzma
except ImportError:
    lzma = None


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
        if six.PY2:
            filename = filename.decode('utf-8')

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
    archive_util.unpack_archive(tarfile_with_unicode, six.text_type(target))


def can_fs_encode(filename):
    """
    Return True if the filename can be saved in the file system.
    """
    if os.path.supports_unicode_filenames:
        return True
    try:
        filename.encode(sys.getfilesystemencoding())
    except UnicodeEncodeError:
        return False
    return True


class ArchiveUtilTestHelper:

    _created_files = ('dist', 'dist/file1', 'dist/file2',
                      'dist/sub', 'dist/sub/file3', 'dist/sub2')

    def __init__(self, monkeypatch, tmpdir_factory):
        self.monkeypatch = monkeypatch
        self.tmpdir_factory = tmpdir_factory

    def mkdtemp(self):
        return str(self.tmpdir_factory.mktemp('tmp'))

    @contextmanager
    def chdir(self, directory):
        with self.monkeypatch.context() as m:
            m.chdir(directory)
            yield

    def _make_tarball(self, tmpdir, target_name, suffix, **kwargs):
        tmpdir2 = self.mkdtemp()
        pytest.mark.skipif(not splitdrive(tmpdir)[0] == splitdrive(tmpdir2)[0],
                            "source and target should be on same drive")

        base_name = os.path.join(tmpdir2, target_name)

        # working with relative paths to avoid tar warnings
        with self.chdir(tmpdir):
            archive_util.make_tarball(splitdrive(base_name)[1], 'dist', **kwargs)

        # check if the compressed tarball was created
        tarball = base_name + suffix
        assert os.path.exists(tarball)
        assert self._tarinfo(tarball) == self._created_files

    @staticmethod
    def _tarinfo(path):
        tar = tarfile.open(path)
        try:
            names = tar.getnames()
            names.sort()
            return tuple(names)
        finally:
            tar.close()

    @staticmethod
    def write_file(path_components, contents):
        with open(os.path.join(*path_components), 'w') as fp:
            fp.write(contents)

    def _create_files(self):
        # creating something to tar
        tmpdir = self.mkdtemp()
        dist = os.path.join(tmpdir, 'dist')
        os.mkdir(dist)
        self.write_file([dist, 'file1'], 'xxx')
        self.write_file([dist, 'file2'], 'xxx')
        os.mkdir(os.path.join(dist, 'sub'))
        self.write_file([dist, 'sub', 'file3'], 'xxx')
        os.mkdir(os.path.join(dist, 'sub2'))
        return tmpdir

@pytest.fixture
def helper(monkeypatch, tmpdir_factory):
    return ArchiveUtilTestHelper(monkeypatch, tmpdir_factory)

@pytest.mark.skipif(not ZLIB_SUPPORT, reason='Need zlib support to run')
def test_make_tarball(helper, name='archive'):
    # creating something to tar
    tmpdir = helper._create_files()
    helper._make_tarball(tmpdir, name, '.tar.gz')
    # trying an uncompressed one
    helper._make_tarball(tmpdir, name, '.tar', compress=None)

@pytest.mark.skipif(not ZLIB_SUPPORT, reason='Need zlib support to run')
def test_make_tarball_gzip(helper):
    tmpdir = helper._create_files()
    helper._make_tarball(tmpdir, 'archive', '.tar.gz', compress='gzip')

@pytest.mark.skipif(not bz2, reason='Need bz2 support to run')
def test_make_tarball_bzip2(helper):
    tmpdir = helper._create_files()
    helper._make_tarball(tmpdir, 'archive', '.tar.bz2', compress='bzip2')

@pytest.mark.skipif(not lzma, reason='Need lzma support to run')
def test_make_tarball_xz(helper):
    tmpdir = helper._create_files()
    helper._make_tarball(tmpdir, 'archive', '.tar.xz', compress='xz')

@pytest.mark.skipif(not can_fs_encode('årchiv'),
    reason='File system cannot handle this filename')
def test_make_tarball_latin1(helper):
    """
    Mirror test_make_tarball, except filename contains latin characters.
    """
    test_make_tarball(helper, 'årchiv') # note this isn't a real word

@pytest.mark.skipif(not can_fs_encode('のアーカイブ'),
                    reason='File system cannot handle this filename')
def test_make_tarball_extended(helper):
    """
    Mirror test_make_tarball, except filename contains extended
    characters outside the latin charset.
    """
    test_make_tarball(helper, 'のアーカイブ') # japanese for archive

@pytest.mark.skipif(not (find_executable('tar') and
                         find_executable('gzip') and
                         ZLIB_SUPPORT),
                    reason='Need the tar, gzip and zlib command to run')
def test_tarfile_vs_tar(helper):
    tmpdir =  helper._create_files()
    tmpdir2 = helper.mkdtemp()
    base_name = os.path.join(tmpdir2, 'archive')
    with helper.chdir(tmpdir):
        archive_util.make_tarball(base_name, 'dist')

    # check if the compressed tarball was created
    tarball = base_name + '.tar.gz'
    assert os.path.exists(tarball)

    # now create another tarball using `tar`
    tarball2 = os.path.join(tmpdir, 'archive2.tar.gz')
    tar_cmd = ['tar', '-cf', 'archive2.tar', 'dist']
    gzip_cmd = ['gzip', '-f', '-9', 'archive2.tar']
    with helper.chdir(tmpdir):
        spawn(tar_cmd)
        spawn(gzip_cmd)

    assert os.path.exists(tarball2)
    # let's compare both tarballs
    assert helper._tarinfo(tarball) == helper._created_files
    assert helper._tarinfo(tarball2) == helper._created_files

    # trying an uncompressed one
    base_name = os.path.join(tmpdir2, 'archive')
    with helper.chdir(tmpdir):
        archive_util.make_tarball(base_name, 'dist', compress=None)
    tarball = base_name + '.tar'
    assert os.path.exists(tarball)

    # now for a dry_run
    base_name = os.path.join(tmpdir2, 'archive')
    with helper.chdir(tmpdir):
        archive_util.make_tarball(base_name, 'dist', compress=None, dry_run=True)
    tarball = base_name + '.tar'
    assert os.path.exists(tarball)

@pytest.mark.skipif(not ZIP_SUPPORT and ZLIB_SUPPORT,
                    reason='Need zip and zlib support to run')
def test_make_zipfile(helper):
    # creating something to tar
    tmpdir = helper._create_files()
    base_name = os.path.join(helper.mkdtemp(), 'archive')
    with helper.chdir(tmpdir):
        archive_util.make_zipfile(base_name, 'dist')

    # check if the compressed tarball was created
    tarball = base_name + '.zip'
    assert os.path.exists(tarball)
    with zipfile.ZipFile(tarball) as zf:
        assert sorted(zf.namelist()) == ['dist/file1', 'dist/file2',
                                         'dist/sub/file3']

@pytest.mark.skipif(not ZIP_SUPPORT, reason='Need zip support to run')
def test_make_zipfile_no_zlib(helper):
    helper.monkeypatch.setattr(archive_util.zipfile, 'zlib', None)  # force zlib ImportError

    called = []
    zipfile_class = zipfile.ZipFile
    def fake_zipfile(*a, **kw):
        if kw.get('compression', None) == zipfile.ZIP_STORED:
            called.append((a, kw))
        return zipfile_class(*a, **kw)

    helper.monkeypatch.setattr(archive_util.zipfile, 'ZipFile', fake_zipfile)

    # create something to tar and compress
    tmpdir = helper._create_files()
    base_name = os.path.join(tmpdir, 'archive')
    with helper.chdir(tmpdir):
        archive_util.make_zipfile(base_name, 'dist')

    tarball = base_name + '.zip'
    assert called == [((tarball, "w"), {'compression': zipfile.ZIP_STORED})]
    assert os.path.exists(tarball)
    with zipfile.ZipFile(tarball) as zf:
        assert sorted(zf.namelist()) == ['dist/file1', 'dist/file2', 'dist/sub/file3']

def test_check_archive_formats(helper):
    assert archive_util.check_archive_formats(['gztar', 'xxx', 'zip']) == 'xxx'
    formats = ['gztar', 'bztar', 'tar', 'zip']
    if lzma is not None:
        formats.append('xztar')
    assert archive_util.check_archive_formats(formats) is None

def test_make_archive(tmpdir):
    base_name = os.path.join(str(tmpdir), 'archive')
    with pytest.raises(ValueError):
        archive_util.make_archive(base_name, 'xxx')

def test_make_archive_cwd(tmpdir):
    current_dir = os.getcwd()
    def _breaks(*args, **kw):
        raise RuntimeError()
    archive_util.ARCHIVE_FORMATS['xxx'] = (_breaks, [], 'xxx file')
    try:
        try:
            archive_util.make_archive('xxx', 'xxx', root_dir=tmpdir)
        except:
            pass
        assert os.getcwd() == current_dir
    finally:
        del archive_util.ARCHIVE_FORMATS['xxx']

def test_make_archive_tar(helper):
    tmpdir = helper._create_files()
    base_name = os.path.join(tmpdir , 'archive')
    res = archive_util.make_archive(base_name, 'tar', tmpdir, 'dist')
    assert os.path.exists(res)
    assert os.path.basename(res) == 'archive.tar'
    assert helper._tarinfo(res) == helper._created_files

@pytest.mark.skipif(not ZLIB_SUPPORT, reason='Need zlib support to run')
def test_make_archive_gztar(helper, tmpdir):
    tmpdir = helper._create_files()
    base_name = os.path.join(tmpdir, 'archive')
    res = archive_util.make_archive(base_name, 'gztar', tmpdir, 'dist')
    assert os.path.exists(res)
    assert os.path.basename(res) == 'archive.tar.gz'
    assert helper._tarinfo(res) == helper._created_files

@pytest.mark.skipif(not bz2, reason='Need bz2 support to run')
def test_make_archive_bztar(helper, tmpdir):
    tmpdir = helper._create_files()
    base_name = os.path.join(tmpdir , 'archive')
    res = archive_util.make_archive(base_name, 'bztar', tmpdir, 'dist')
    assert os.path.exists(res)
    assert os.path.basename(res) == 'archive.tar.bz2'
    assert helper._tarinfo(res) == helper._created_files

@pytest.mark.skipif(not lzma, reason='Need xz support to run')
def test_make_archive_xztar(helper):
    base_dir =  helper._create_files()
    base_name = os.path.join(helper.mkdtemp(), 'archive')
    res = archive_util.make_archive(base_name, 'xztar', base_dir, 'dist')
    assert os.path.exists(res)
    assert os.path.basename(res) == 'archive.tar.xz'
    assert helper._tarinfo(res) == helper._created_files

def test_make_archive_owner_group(helper):
    # testing make_archive with owner and group, with various combinations
    # this works even if there's not gid/uid support
    if UID_GID_SUPPORT:
        group = grp.getgrgid(0)[0]
        owner = pwd.getpwuid(0)[0]
    else:
        group = owner = 'root'

    base_dir = helper._create_files()
    root_dir = helper.mkdtemp()
    base_name = os.path.join(helper.mkdtemp(), 'archive')
    res = archive_util.make_archive(base_name, 'zip', root_dir, base_dir,
                                    owner=owner, group=group)
    assert os.path.exists(res)

    res = archive_util.make_archive(base_name, 'zip', root_dir, base_dir)
    assert os.path.exists(res)

    res = archive_util.make_archive(base_name, 'tar', root_dir, base_dir,
                                    owner=owner, group=group)
    assert os.path.exists(res)

    res = archive_util.make_archive(base_name, 'tar', root_dir, base_dir,
                                    owner='kjhkjhkjg', group='oihohoh')
    assert os.path.exists(res)

@pytest.mark.skipif(not ZLIB_SUPPORT, reason="Requires zlib")
@pytest.mark.skipif(not UID_GID_SUPPORT, reason="Requires grp and pwd support")
def test_tarfile_root_owner(helper):
    tmpdir =  helper._create_files()
    base_name = os.path.join(helper.mkdtemp(), 'archive')
    group = grp.getgrgid(0)[0]
    owner = pwd.getpwuid(0)[0]
    with helper.chdir(tmpdir):
        archive_name = archive_util.make_tarball(base_name, 'dist', compress=None,
                                                 owner=owner, group=group)

    # check if the compressed tarball was created
    assert os.path.exists(archive_name)

    # now checks the rights
    with tarfile.open(archive_name) as archive:
        for member in archive.getmembers():
            assert member.uid == 0
            assert member.gid == 0
