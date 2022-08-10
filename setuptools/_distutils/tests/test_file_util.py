"""Tests for distutils.file_util."""
import os
import errno
import unittest.mock as mock

from distutils.file_util import move_file, copy_file
from distutils import log
from distutils.tests import support
from distutils.errors import DistutilsFileError
from .py38compat import unlink
import pytest


@pytest.fixture(autouse=True)
def stuff(request, monkeypatch, distutils_managed_tempdir):
    self = request.instance
    self._logs = []
    tmp_dir = self.mkdtemp()
    self.source = os.path.join(tmp_dir, 'f1')
    self.target = os.path.join(tmp_dir, 'f2')
    self.target_dir = os.path.join(tmp_dir, 'd1')
    monkeypatch.setattr(log, 'info', self._log)


class TestFileUtil(support.TempdirManager):
    def _log(self, msg, *args):
        if len(args) > 0:
            self._logs.append(msg % args)
        else:
            self._logs.append(msg)

    def test_move_file_verbosity(self):
        f = open(self.source, 'w')
        try:
            f.write('some content')
        finally:
            f.close()

        move_file(self.source, self.target, verbose=0)
        wanted = []
        assert self._logs == wanted

        # back to original state
        move_file(self.target, self.source, verbose=0)

        move_file(self.source, self.target, verbose=1)
        wanted = ['moving {} -> {}'.format(self.source, self.target)]
        assert self._logs == wanted

        # back to original state
        move_file(self.target, self.source, verbose=0)

        self._logs = []
        # now the target is a dir
        os.mkdir(self.target_dir)
        move_file(self.source, self.target_dir, verbose=1)
        wanted = ['moving {} -> {}'.format(self.source, self.target_dir)]
        assert self._logs == wanted

    def test_move_file_exception_unpacking_rename(self):
        # see issue 22182
        with mock.patch("os.rename", side_effect=OSError("wrong", 1)), pytest.raises(
            DistutilsFileError
        ):
            with open(self.source, 'w') as fobj:
                fobj.write('spam eggs')
            move_file(self.source, self.target, verbose=0)

    def test_move_file_exception_unpacking_unlink(self):
        # see issue 22182
        with mock.patch(
            "os.rename", side_effect=OSError(errno.EXDEV, "wrong")
        ), mock.patch("os.unlink", side_effect=OSError("wrong", 1)), pytest.raises(
            DistutilsFileError
        ):
            with open(self.source, 'w') as fobj:
                fobj.write('spam eggs')
            move_file(self.source, self.target, verbose=0)

    def test_copy_file_hard_link(self):
        with open(self.source, 'w') as f:
            f.write('some content')
        # Check first that copy_file() will not fall back on copying the file
        # instead of creating the hard link.
        try:
            os.link(self.source, self.target)
        except OSError as e:
            self.skipTest('os.link: %s' % e)
        else:
            unlink(self.target)
        st = os.stat(self.source)
        copy_file(self.source, self.target, link='hard')
        st2 = os.stat(self.source)
        st3 = os.stat(self.target)
        assert os.path.samestat(st, st2), (st, st2)
        assert os.path.samestat(st2, st3), (st2, st3)
        with open(self.source) as f:
            assert f.read() == 'some content'

    def test_copy_file_hard_link_failure(self):
        # If hard linking fails, copy_file() falls back on copying file
        # (some special filesystems don't support hard linking even under
        #  Unix, see issue #8876).
        with open(self.source, 'w') as f:
            f.write('some content')
        st = os.stat(self.source)
        with mock.patch("os.link", side_effect=OSError(0, "linking unsupported")):
            copy_file(self.source, self.target, link='hard')
        st2 = os.stat(self.source)
        st3 = os.stat(self.target)
        assert os.path.samestat(st, st2), (st, st2)
        assert not os.path.samestat(st2, st3), (st2, st3)
        for fn in (self.source, self.target):
            with open(fn) as f:
                assert f.read() == 'some content'
