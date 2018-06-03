import warnings

import pytest

from setuptools.glibc import check_glibc_version

__metaclass__ = type


@pytest.fixture(params=[
    "2.20",
    # used by "linaro glibc", see gh-3588
    "2.20-2014.11",
    # weird possibilities that I just made up
    "2.20+dev",
    "2.20-custom",
    "2.20.1",
    ])
def two_twenty(request):
    return request.param


@pytest.fixture(params=["asdf", "", "foo.bar"])
def bad_string(request):
    return request.param


class TestGlibc:
    def test_manylinux1_check_glibc_version(self, two_twenty):
        """
        Test that the check_glibc_version function is robust against weird
        glibc version strings.
        """
        assert check_glibc_version(two_twenty, 2, 15)
        assert check_glibc_version(two_twenty, 2, 20)
        assert not check_glibc_version(two_twenty, 2, 21)
        assert not check_glibc_version(two_twenty, 3, 15)
        assert not check_glibc_version(two_twenty, 1, 15)

    def test_bad_versions(self, bad_string):
        """
        For unparseable strings, warn and return False
        """
        with warnings.catch_warnings(record=True) as ws:
            warnings.filterwarnings("always")
            assert not check_glibc_version(bad_string, 2, 5)
            for w in ws:
                if "Expected glibc version with" in str(w.message):
                    break
            else:
                # Didn't find the warning we were expecting
                assert False
