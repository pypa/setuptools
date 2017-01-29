from setuptools.dep_util import newer_pairwise_group
import os
import pytest


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
