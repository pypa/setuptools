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

        # issue 16
        # easy_install inquant.contentmirror.plone breaks because of a typo
        # in its home URL
        index = setuptools.package_index.PackageIndex(
            hosts=('www.example.com',)
        )

        url = 'url:%20https://svn.plone.org/svn/collective/inquant.contentmirror.plone/trunk'
        try:
            v = index.open_url(url)
        except Exception, v:
            self.assert_(url in str(v))
        else:
            self.assert_(isinstance(v, urllib2.HTTPError))

        def _urlopen(*args):
            import httplib
            raise httplib.BadStatusLine('line')

        old_urlopen = urllib2.urlopen
        urllib2.urlopen = _urlopen
        url = 'http://example.com'
        try:
            try:
                v = index.open_url(url)
            except Exception, v:
                self.assert_('line' in str(v))
            else:
                raise AssertionError('Should have raise here!')
        finally:
            urllib2.urlopen = old_urlopen

        # issue 20
        url = 'http://http://svn.pythonpaste.org/Paste/wphp/trunk'
        try:
            index.open_url(url)
        except Exception, v:
            self.assert_('nonnumeric port' in str(v))

    def test_url_ok(self):
        index = setuptools.package_index.PackageIndex(
            hosts=('www.example.com',)
        )
        url = 'file:///tmp/test_package_index'
        self.assert_(index.url_ok(url, True))

