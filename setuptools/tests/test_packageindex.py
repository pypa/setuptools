"""Package Index Tests
"""
# More would be better!
import sys
import os, shutil, tempfile, unittest, urllib2
import pkg_resources
import setuptools.package_index
from server import IndexServer

class TestPackageIndex(unittest.TestCase):

    def test_bad_urls(self):
        index = setuptools.package_index.PackageIndex()
        url = 'http://127.0.0.1:0/nonesuch/test_package_index'
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


        # issue #160
        if sys.version_info[0] == 2 and sys.version_info[1] == 7:
            # this should not fail
            url = 'http://example.com'
            page = ('<a href="http://www.famfamfam.com]('
                    'http://www.famfamfam.com/">')
            index.process_index(url, page)


    def test_url_ok(self):
        index = setuptools.package_index.PackageIndex(
            hosts=('www.example.com',)
        )
        url = 'file:///tmp/test_package_index'
        self.assert_(index.url_ok(url, True))

    def test_links_priority(self):
        """
        Download links from the pypi simple index should be used before
        external download links.
        http://bitbucket.org/tarek/distribute/issue/163/md5-validation-error

        Usecase :
        - someone uploads a package on pypi, a md5 is generated
        - someone manually copies this link (with the md5 in the url) onto an
          external page accessible from the package page.
        - someone reuploads the package (with a different md5)
        - while easy_installing, an MD5 error occurs because the external link
          is used
        -> Distribute should use the link from pypi, not the external one.
        """
        # start an index server
        server = IndexServer()
        server.start()
        index_url = server.base_url() + 'test_links_priority/simple/'

        # scan a test index
        pi = setuptools.package_index.PackageIndex(index_url)
        requirement = pkg_resources.Requirement.parse('foobar')
        pi.find_packages(requirement)
        server.stop()

        # the distribution has been found
        self.assert_('foobar' in pi)
        # we have only one link, because links are compared without md5
        self.assert_(len(pi['foobar'])==1)
        # the link should be from the index
        self.assert_('correct_md5' in pi['foobar'][0].location)

    def test_parse_bdist_wininst(self):
        self.assertEqual(setuptools.package_index.parse_bdist_wininst(
            'reportlab-2.5.win32-py2.4.exe'), ('reportlab-2.5', '2.4', 'win32'))
        self.assertEqual(setuptools.package_index.parse_bdist_wininst(
            'reportlab-2.5.win32.exe'), ('reportlab-2.5', None, 'win32'))
        self.assertEqual(setuptools.package_index.parse_bdist_wininst(
            'reportlab-2.5.win-amd64-py2.7.exe'), ('reportlab-2.5', '2.7', 'win-amd64'))
        self.assertEqual(setuptools.package_index.parse_bdist_wininst(
            'reportlab-2.5.win-amd64.exe'), ('reportlab-2.5', None, 'win-amd64'))


