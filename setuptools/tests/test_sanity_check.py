def test_packaging_version():
    from packaging import __version__

    version = __version__.strip("v")
    assert version.startswith("26")
