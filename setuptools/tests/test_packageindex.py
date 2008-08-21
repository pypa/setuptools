"""Package Index Tests
"""
# More would be better!

import os, shutil, tempfile, unittest, urllib2
import pkg_resources
import setuptools.package_index

class TestPackageIndex(unittest.TestCase):

    def test_bad_urls(self):
        index = setuptools.package_index.PackageIndex()
        url = 'http://127.0.0.1/nonesuch/test_package_index'
        try:
            v = index.open_url(url)
        except Exception, v:
            self.assert_(url in str(v))
        else:
            self.assert_(isinstance(v,urllib2.HTTPError))

    def test_url_ok(self):
        index = setuptools.package_index.PackageIndex(
            hosts=('www.example.com',)
        )
        url = 'file:///tmp/test_package_index'
        self.assert_(index.url_ok(url, True))

