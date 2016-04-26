import pytest


@pytest.yield_fixture
def tmpdir_as_cwd(tmpdir):
    try:
        orig = tmpdir.chdir()
        yield tmpdir
    finally:
        orig.chdir()
