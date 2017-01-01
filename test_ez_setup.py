import py.path

import ez_setup


def test_download(tmpdir_cwd):
    cwd = py.path.local()
    ez_setup.download_setuptools()
    res, = cwd.listdir()
    assert res.basename.startswith('setuptools-')
    assert res.basename.endswith('.zip')
    # file should be bigger than 64k
    assert res.size() > 2**16
