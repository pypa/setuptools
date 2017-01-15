"""Tests for distutils._modified."""
import os

from distutils._modified import newer, newer_pairwise, newer_group, newer_pairwise_group
from distutils.errors import DistutilsFileError
from distutils.tests import support
import pytest


class TestDepUtil(support.TempdirManager):
    def test_newer(self):
        tmpdir = self.mkdtemp()
        new_file = os.path.join(tmpdir, 'new')
        old_file = os.path.abspath(__file__)

        # Raise DistutilsFileError if 'new_file' does not exist.
        with pytest.raises(DistutilsFileError):
            newer(new_file, old_file)

        # Return true if 'new_file' exists and is more recently modified than
        # 'old_file', or if 'new_file' exists and 'old_file' doesn't.
        self.write_file(new_file)
        assert newer(new_file, 'I_dont_exist')
        assert newer(new_file, old_file)

        # Return false if both exist and 'old_file' is the same age or younger
        # than 'new_file'.
        assert not newer(old_file, new_file)

    def _setup_1234(self):
        tmpdir = self.mkdtemp()
        sources = os.path.join(tmpdir, 'sources')
        targets = os.path.join(tmpdir, 'targets')
        os.mkdir(sources)
        os.mkdir(targets)
        one = os.path.join(sources, 'one')
        two = os.path.join(sources, 'two')
        three = os.path.abspath(__file__)  # I am the old file
        four = os.path.join(targets, 'four')
        self.write_file(one)
        self.write_file(two)
        self.write_file(four)
        return one, two, three, four

    def test_newer_pairwise(self):
        one, two, three, four = self._setup_1234()

        assert newer_pairwise([one, two], [three, four]) == ([one], [three])

    def test_newer_pairwise_mismatch(self):
        one, two, three, four = self._setup_1234()

        with pytest.raises(ValueError):
            newer_pairwise([one], [three, four])

        with pytest.raises(ValueError):
            newer_pairwise([one, two], [three])

    def test_newer_pairwise_empty(self):
        assert newer_pairwise([], []) == ([], [])

    def test_newer_pairwise_fresh(self):
        one, two, three, four = self._setup_1234()

        assert newer_pairwise([one, three], [two, four]) == ([], [])

    def test_newer_group(self):
        tmpdir = self.mkdtemp()
        sources = os.path.join(tmpdir, 'sources')
        os.mkdir(sources)
        one = os.path.join(sources, 'one')
        two = os.path.join(sources, 'two')
        three = os.path.join(sources, 'three')
        old_file = os.path.abspath(__file__)

        # return true if 'old_file' is out-of-date with respect to any file
        # listed in 'sources'.
        self.write_file(one)
        self.write_file(two)
        self.write_file(three)
        assert newer_group([one, two, three], old_file)
        assert not newer_group([one, two, old_file], three)

        # missing handling
        os.remove(one)
        with pytest.raises(OSError):
            newer_group([one, two, old_file], three)

        assert not newer_group([one, two, old_file], three, missing='ignore')

        assert newer_group([one, two, old_file], three, missing='newer')


@pytest.fixture
def groups_target(tmpdir):
    """Sets up some older sources, a target and newer sources.
    Returns a 3-tuple in this order.
    """
    creation_order = ['older.c', 'older.h', 'target.o', 'newer.c', 'newer.h']
    mtime = 0

    for i in range(len(creation_order)):
        creation_order[i] = os.path.join(str(tmpdir), creation_order[i])
        with open(creation_order[i], 'w'):
            pass

        # make sure modification times are sequential
        os.utime(creation_order[i], (mtime, mtime))
        mtime += 1

    return creation_order[:2], creation_order[2], creation_order[3:]


def test_newer_pairwise_group(groups_target):
    older = newer_pairwise_group([groups_target[0]], [groups_target[1]])
    newer = newer_pairwise_group([groups_target[2]], [groups_target[1]])
    assert older == ([], [])
    assert newer == ([groups_target[2]], [groups_target[1]])
