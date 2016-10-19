

from setuptools import dist as dist_mod


class TestCheckNSP:
    def test_namespace_package_implies_package(self):
        """
        When a namespace package is declared, that declaration
        implies the package of the same name, so it should
        ensure that the name appears in the list of packages.
        """
        attrs = dict(namespace_packages=['foo'])
        dist_ob = dist_mod.Distribution(attrs)
        for attr, value in attrs.items():
            dist_mod.check_nsp(dist_ob, attr, value)
        assert 'foo' in dist_ob.packages
