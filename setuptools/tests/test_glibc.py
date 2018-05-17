import warnings

from setuptools.glibc import check_glibc_version


class TestGlibc(object):
    def test_manylinux1_check_glibc_version(self):
        """
        Test that the check_glibc_version function is robust against weird
        glibc version strings.
        """
        for two_twenty in ["2.20",
                           # used by "linaro glibc", see gh-3588
                           "2.20-2014.11",
                           # weird possibilities that I just made up
                           "2.20+dev",
                           "2.20-custom",
                           "2.20.1",
                           ]:
            assert check_glibc_version(two_twenty, 2, 15)
            assert check_glibc_version(two_twenty, 2, 20)
            assert not check_glibc_version(two_twenty, 2, 21)
            assert not check_glibc_version(two_twenty, 3, 15)
            assert not check_glibc_version(two_twenty, 1, 15)

        # For strings that we just can't parse at all, we should warn and
        # return false
        for bad_string in ["asdf", "", "foo.bar"]:
            with warnings.catch_warnings(record=True) as ws:
                warnings.filterwarnings("always")
                assert not check_glibc_version(bad_string, 2, 5)
                for w in ws:
                    if "Expected glibc version with" in str(w.message):
                        break
                else:
                    # Didn't find the warning we were expecting
                    assert False
