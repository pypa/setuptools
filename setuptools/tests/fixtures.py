import shutil

import pytest

from . import contexts


@pytest.fixture
def user_override(monkeypatch):
    """
    Override site.USER_BASE and site.USER_SITE with temporary directories in
    a context.
    """
    with contexts.tempdir() as user_base:
        monkeypatch.setattr('site.USER_BASE', user_base)
        with contexts.tempdir() as user_site:
            monkeypatch.setattr('site.USER_SITE', user_site)
            with contexts.save_user_site_setting():
                yield


@pytest.fixture
def tmpdir_cwd(tmpdir):
    with tmpdir.as_cwd() as orig:
        yield orig


@pytest.fixture
def tmp_src(request, tmp_path):
    """Make a copy of the source dir under `$tmp/src`.

    This fixture is useful whenever it's necessary to run `setup.py`
    or `pip install` against the source directory when there's no
    control over the number of simultaneous invocations. Such
    concurrent runs create and delete directories with the same names
    under the target directory and so they influence each other's runs
    when they are not being executed sequentially.
    """
    tmp_src_path = tmp_path / 'src'
    shutil.copytree(request.config.rootdir, tmp_src_path)
    return tmp_src_path
