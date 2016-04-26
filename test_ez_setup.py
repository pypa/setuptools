import ez_setup


def test_download(tmpdir_cwd):
    ez_setup.download_setuptools()
    res, = tmpdir_cwd.listdir()
    assert res.basename.startswith('setuptools-')
    assert res.basename.endswith('.zip')
    # file should be bigger than 64k
    assert res.size() > 2**16
