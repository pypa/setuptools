from zipfile import BadZipfile

import py.path

import pytest

import ez_setup


def test_download(tmpdir_cwd):
    cwd = py.path.local()
    ez_setup.download_setuptools()
    res, = cwd.listdir()
    assert res.basename.startswith('setuptools-')
    assert res.basename.endswith('.zip')
    # file should be bigger than 64k
    assert res.size() > 2**16


def test_message_corrupted_setuptools(tmpdir_cwd):
    cwd = py.path.local()
    ez_setup.download_setuptools()
    res, = cwd.listdir()
    res.write('CORRUPT ME')
    with pytest.raises(BadZipfile) as excinfo:
        with ez_setup.archive_context(res.strpath):
            pass
    msg = ez_setup.MEANINGFUL_INVALID_ZIP_ERR_MSG.format(res.strpath)
    assert msg in str(excinfo.value)
