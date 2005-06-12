#!python
"""\

Easy Install
------------

A tool for doing automatic download/extract/build of distutils-based Python
packages.  For detailed documentation, see the accompanying EasyInstall.txt
file, or visit the `EasyInstall home page`__.

__ http://peak.telecommunity.com/DevCenter/EasyInstall

"""

import sys
import os.path
import pkg_resources
import re
import zipimport
import shutil
import urlparse
import urllib2
import tempfile

from setuptools.sandbox import run_setup
from setuptools.archive_util import unpack_archive
from distutils.sysconfig import get_python_lib
from pkg_resources import *













HREF = re.compile(r"""href\s*=\s*['"]?([^'"> ]+)""", re.I)
EXTENSIONS = ".tar.gz .tar.bz2 .tar .zip .tgz".split()

def distros_for_url(url, metadata=None):
    """Yield egg or source distribution objects that might be found at a URL"""

    path = urlparse.urlparse(url)[2]
    base = urllib2.unquote(path.split('/')[-1])

    if base.endswith('.egg'):
        dist = Distribution.from_filename(base, metadata)
        dist.path = url
        yield dist
        return  # only one, unambiguous interpretation

    for ext in EXTENSIONS:
        if base.endswith(ext):
            base = base[:-len(ext)]
            break
    else:
        return  # no extension matched

    # Generate alternative interpretations of a source distro name
    # Because some packages are ambiguous as to name/versions split
    # e.g. "adns-python-1.1.0", "egenix-mx-commercial", etc.
    # So, we generate each possible interepretation (e.g. "adns, python-1.1.0"
    # "adns-python, 1.1.0", and "adns-python-1.1.0, no version").  In practice,
    # the spurious interpretations should be ignored, because in the event
    # there's also an "adns" package, the spurious "python-1.1.0" version will
    # compare lower than any numeric version number, and is therefore unlikely
    # to match a request for it.  It's still a potential problem, though, and
    # in the long run PyPI and the distutils should go for "safe" names and
    # versions in distribution archive names (sdist and bdist).

    parts = base.split('-')
    for p in range(1,len(parts)+1):
        yield Distribution(
            url, metadata, '-'.join(parts[:p]), '-'.join(parts[p:]),
            distro_type = SOURCE_DIST
        )

class PackageIndex(AvailableDistributions):
    """A distribution index that scans web pages for download URLs"""

    def __init__(self,index_url="http://www.python.org/pypi",*args,**kw):
        AvailableDistributions.__init__(self,*args,**kw)
        self.index_url = index_url + "/"[:not index_url.endswith('/')]
        self.scanned_urls = {}
        self.fetched_urls = {}
        self.package_pages = {}

    def scan_url(self, url):
        self.process_url(url, True)

    def process_url(self, url, retrieve=False):
        if url in self.scanned_urls and not retrieve:
            return

        self.scanned_urls[url] = True
        dists = list(distros_for_url(url))
        map(self.add, dists)

        if dists or not retrieve or url in self.fetched_urls:
            # don't need the actual page
            return

        f = self.open_url(url)
        self.fetched_urls[url] = self.fetched_urls[f.url] = True
        if 'html' not in f.headers['content-type'].lower():
            f.close()   # not html, we can't process it
            return

        base = f.url     # handle redirects
        page = f.read()
        f.close()
        if url.startswith(self.index_url):
            self.process_index(url, page)
        else:
            for match in HREF.finditer(page):
                link = urlparse.urljoin(base, match.group(1))
                self.process_url(link)

    def find_packages(self,requirement):
        self.scan_url(self.index_url + requirement.distname)
        if not self.package_pages.get(requirement.key):
            # We couldn't find the target package, so search the index page too
            self.scan_url(self.index_url)
        for url in self.package_pages.get(requirement.key,()):
            # scan each page that might be related to the desired package
            self.scan_url(url)

    def process_index(self,url,page):
        def scan(link):
            if link.startswith(self.index_url):
                parts = map(
                    urllib2.unquote, link[len(self.index_url):].split('/')
                )
                if len(parts)==2:
                    # it's a package page, sanitize and index it
                    pkg = safe_name(parts[0])
                    ver = safe_version(parts[1])
                    self.package_pages.setdefault(pkg.lower(),{})[link] = True
        if url==self.index_url or 'Index of Packages</title>' in page:
            # process an index page into the package-page index
            for match in HREF.finditer(page):
                scan( urlparse.urljoin(url, match.group(1)) )
        else:
            scan(url)   # ensure this page is in the page index
            # process individual package page
            for tag in ("<th>Home Page", "<th>Download URL"):
                pos = page.find(tag)
                if pos!=-1:
                    match = HREF.search(page,pos)
                    if match:
                        # Process the found URL
                        self.scan_url(urlparse.urljoin(url, match.group(1)))

    def obtain(self,requirement):
        self.find_packages(requirement)
        for dist in self.get(requirement.key, ()):
            if dist in requirement:
                return dist

    def download(self, spec, tmpdir):
        """Locate and/or download `spec`, returning a local filename

        `spec` may be a ``Requirement`` object, or a string containing a URL,
        an existing local filename, or a package/version requirement spec
        (i.e. the string form of a ``Requirement`` object).

        If necessary, the requirement is searched for in the package index.
        If the download is successful, the return value is a local file path,
        and it is a subpath of `tmpdir` if the distribution had to be
        downloaded.  If no matching distribution is found, return ``None``.
        Various errors may be raised if a problem occurs during downloading.
        """

        if not isinstance(spec,Requirement):
            scheme = URL_SCHEME(spec)
            if scheme:
                # It's a url, download it to tmpdir
                return self._download_url(scheme.group(1), spec, tmpdir)

            elif os.path.exists(spec):
                # Existing file or directory, just return it
                return spec
            else:
                try:
                    spec = Requirement.parse(spec)
                except ValueError:
                    raise RuntimeError(
                        "Not a URL, existing file, or requirement spec: %r" %
                        (spec,)
                    )

        # process a Requirement
        dist = self.best_match(spec,[])
        if dist is not None:
            return self.download(dist.path, tmpdir)

        return None



    dl_blocksize = 8192
    
    def _download_to(self, url, filename):
        # Download the file
        fp, tfp = None, None
        try:
            fp = self.open_url(url)
            if isinstance(fp, urllib2.HTTPError):
                raise RuntimeError(
                    "Can't download %s: %s %s" % (url, fp.code,fp.msg)
                )

            headers = fp.info()
            blocknum = 0
            bs = self.dl_blocksize
            size = -1

            if "content-length" in headers:
                size = int(headers["Content-Length"])
                self.reporthook(url, filename, blocknum, bs, size)

            tfp = open(filename,'wb')      
            while True:
                block = fp.read(bs)
                if block:
                    tfp.write(block)
                    blocknum += 1
                    self.reporthook(url, filename, blocknum, bs, size)
                else:
                    break
            return headers

        finally:
            if fp: fp.close()
            if tfp: tfp.close()

    def reporthook(self, url, filename, blocknum, blksize, size):
        pass    # no-op



    def open_url(self, url):
        try:
            return urllib2.urlopen(url)
        except urllib2.HTTPError, v:
            return v
        except urllib2.URLError, v:
            raise RuntimeError("Download error: %s" % v.reason)


    def _download_url(self, scheme, url, tmpdir):

        # Determine download filename
        #
        name = filter(None,urlparse.urlparse(url)[2].split('/'))
        if name:
            name = name[-1]
            while '..' in name:
                name = name.replace('..','.').replace('\\','_')
        else:
            name = "__downloaded__"    # default if URL has no path contents

        filename = os.path.join(tmpdir,name)

        # Download the file
        #
        if scheme=='svn' or scheme.startswith('svn+'):
            return self._download_svn(url, filename)
        else:
            headers = self._download_to(url, filename)
            if 'html' in headers['content-type'].lower():
                return self._download_html(url, headers, filename, tmpdir)
            else:
                return filename








    def _download_html(self, url, headers, filename, tmpdir):
        # Check for a sourceforge URL
        sf_url = url.startswith('http://prdownloads.')
        file = open(filename)
        for line in file:
            if line.strip():
                # Check for a subversion index page
                if re.search(r'<title>Revision \d+:', line):
                    # it's a subversion index page:
                    file.close()
                    os.unlink(filename)
                    return self._download_svn(url, filename)
                # Check for a SourceForge header
                elif sf_url:
                    if re.search(r'^<HTML><HEAD>', line, re.I):
                        continue    # skip first line
                    elif re.search(r'<TITLE>Select a Mirror for File:',line):
                        # Sourceforge mirror page
                        page = file.read()
                        file.close()
                        os.unlink(filename)
                        return self._download_sourceforge(url, page, tmpdir)
                break   # not an index page
        file.close()
        raise RuntimeError("Unexpected HTML page found at "+url)


    def _download_svn(self, url, filename):
        os.system("svn checkout -q %s %s" % (url, filename))
        return filename











    def _download_sourceforge(self, source_url, sf_page, tmpdir):
        """Download package from randomly-selected SourceForge mirror"""

        mirror_regex = re.compile(r'HREF=(/.*?\?use_mirror=[^>]*)')
        urls = [m.group(1) for m in mirror_regex.finditer(sf_page)]
        if not urls:
            raise RuntimeError(
                "URL looks like a Sourceforge mirror page, but no URLs found"
            )

        import random
        url = urlparse.urljoin(source_url, random.choice(urls))
        f = self.open_url(url)
        match = re.search(
            r'<META HTTP-EQUIV="refresh" content=".*?URL=(.*?)"',
            f.read()
        )
        f.close()

        if match:
            download_url = match.group(1)
            scheme = URL_SCHEME(download_url)
            return self._download_url(scheme.group(1), download_url, tmpdir)
        else:
            raise RuntimeError(
                'No META HTTP-EQUIV="refresh" found in Sourceforge page at %s'
                % url
            )













class Installer:
    """Manage a download/build/install process"""

    pth_file = None
    cleanup = False

    def __init__(self, instdir=None, multi=None):
        site_packages = get_python_lib()
        if instdir is None or self.samefile(site_packages,instdir):
            instdir = site_packages
            self.pth_file = PthDistributions(
                os.path.join(instdir,'easy-install.pth')
            )
        elif multi is None:
            multi = True

        elif not multi:
            # explicit false, raise an error
            raise RuntimeError(
                "Can't do single-version installs outside site-packages"
            )

        self.instdir = instdir
        self.multi = multi


    def samefile(self,p1,p2):
        if hasattr(os.path,'samefile') and (
            os.path.exists(p1) and os.path.exists(p2)
        ):
            return os.path.samefile(p1,p2)
        return (
            os.path.normpath(os.path.normcase(p1)) ==
            os.path.normpath(os.path.normcase(p2))
        )






    def install_eggs(self, dist_filename, zip_ok, tmpdir):
        # .egg dirs or files are already built, so just return them
        if dist_filename.lower().endswith('.egg'):
            return [self.install_egg(dist_filename, True, tmpdir)]

        # Anything else, try to extract and build
        if os.path.isfile(dist_filename):
            unpack_archive(dist_filename, tmpdir)  # XXX add progress log

        # Find the setup.py file
        from glob import glob
        setup_script = os.path.join(tmpdir, 'setup.py')
        if not os.path.exists(setup_script):
            setups = glob(os.path.join(tmpdir, '*', 'setup.py'))
            if not setups:
                raise RuntimeError(
                    "Couldn't find a setup script in %s" % dist_filename
                )
            if len(setups)>1:
                raise RuntimeError(
                    "Multiple setup scripts in %s" % dist_filename
                )
            setup_script = setups[0]

        from setuptools.command import bdist_egg
        sys.modules.setdefault('distutils.command.bdist_egg', bdist_egg)
        try:
            run_setup(setup_script, ['-q', 'bdist_egg'])
        except SystemExit, v:
            raise RuntimeError(
                "Setup script exited with %s" % (v.args[0],)
            )

        eggs = []
        for egg in glob(
            os.path.join(os.path.dirname(setup_script),'dist','*.egg')
        ):
            eggs.append(self.install_egg(egg, zip_ok, tmpdir))

        return eggs

    def install_egg(self, egg_path, zip_ok, tmpdir):

        destination = os.path.join(self.instdir, os.path.basename(egg_path))
        ensure_directory(destination)

        if not self.samefile(egg_path, destination):
            if os.path.isdir(destination):
                shutil.rmtree(destination)
            elif os.path.isfile(destination):
                os.unlink(destination)

            if zip_ok:
                if egg_path.startswith(tmpdir):
                    shutil.move(egg_path, destination)
                else:
                    shutil.copy2(egg_path, destination)

            elif os.path.isdir(egg_path):
                shutil.move(egg_path, destination)

            else:
                os.mkdir(destination)
                unpack_archive(egg_path, destination)   # XXX add progress??

        if os.path.isdir(destination):
            dist = Distribution.from_filename(
                destination, metadata=PathMetadata(
                    destination, os.path.join(destination,'EGG-INFO')
                )
            )
        else:
            metadata = EggMetadata(zipimport.zipimporter(destination))
            dist = Distribution.from_filename(destination,metadata=metadata)

        self.update_pth(dist)
        return dist





    def installation_report(self, dist):
        """Helpful installation message for display to package users"""

        msg = "Installed %(eggloc)s to %(instdir)s"
        if self.multi:
            msg += """

Because this distribution was installed --multi-version or --install-dir,
before you can import modules from this package in an application, you
will need to 'import pkg_resources' and then use a 'require()' call
similar to one of these examples, in order to select the desired version:

    pkg_resources.require("%(name)s")  # latest installed version
    pkg_resources.require("%(name)s==%(version)s")  # this exact version
    pkg_resources.require("%(name)s>=%(version)s")  # this version or higher
"""
        if not self.samefile(get_python_lib(),self.instdir):
            msg += """

Note also that the installation directory must be on sys.path at runtime for
this to work.  (e.g. by being the application's script directory, by being on
PYTHONPATH, or by being added to sys.path by your code.)
"""
        eggloc = os.path.basename(dist.path)
        instdir = os.path.realpath(self.instdir)
        name = dist.name
        version = dist.version
        return msg % locals()

    def update_pth(self,dist):
        if self.pth_file is not None:
            remove = self.pth_file.remove
            for d in self.pth_file.get(dist.key,()):    # drop old entries
                remove(d)
            if not self.multi:
                self.pth_file.add(dist) # add new entry
            self.pth_file.save()




class PthDistributions(AvailableDistributions):
    """A .pth file with Distribution paths in it"""

    dirty = False

    def __init__(self, filename):
        self.filename = filename; self._load()
        AvailableDistributions.__init__(
            self, list(yield_lines(self.paths)), None, None
        )

    def _load(self):
        self.paths = []
        if os.path.isfile(self.filename):
            self.paths = [line.rstrip() for line in open(self.filename,'rt')]
            while self.paths and not self.paths[-1].strip(): self.paths.pop()

    def save(self):
        """Write changed .pth file back to disk"""
        if self.dirty:
            data = '\n'.join(self.paths+[''])
            f = open(self.filename,'wt')
            f.write(data)
            f.close()
            self.dirty = False

    def add(self,dist):
        """Add `dist` to the distribution map"""
        if dist.path not in self.paths:
            self.paths.append(dist.path); self.dirty = True
        AvailableDistributions.add(self,dist)

    def remove(self,dist):
        """Remove `dist` from the distribution map"""
        while dist.path in self.paths:
            self.paths.remove(dist.path); self.dirty = True
        AvailableDistributions.remove(self,dist)




URL_SCHEME = re.compile('([-+.a-z0-9]{2,}):',re.I).match

def main(argv, installer_type=Installer, index_type=PackageIndex):

    from optparse import OptionParser

    parser = OptionParser(usage = "usage: %prog [options] url [url...]")
    parser.add_option("-d", "--install-dir", dest="instdir", default=None,
                      help="install package to DIR", metavar="DIR")

    parser.add_option("-z", "--zip",
                      action="store_true", dest="zip_ok", default=False,
                      help="install package as a zipfile")

    parser.add_option("-m", "--multi-version",
                      action="store_true", dest="multi", default=None,
                      help="make apps have to require() a version")

    parser.add_option("-b", "--build-directory", dest="tmpdir", metavar="DIR",
                      default=None,
                      help="download/extract/build in DIR; keep the results")

    parser.add_option("-u", "--index-url", dest="index_url", metavar="URL",
                      default="http://www.python.org/pypi",
                      help="base URL of Python Package Index")

    parser.add_option("-s", "--scan-url", dest="scan_urls", metavar="URL",
                      action="append",
                      help="additional URL(s) to search for packages")

    (options, args) = parser.parse_args()

    if not args:
        parser.error("No urls, filenames, or requirements specified")
    elif len(args)>1 and options.tmpdir is not None:
        parser.error("Build directory can only be set when using one URL")





    def alloc_tmp():
        if options.tmpdir is None:
            return tempfile.mkdtemp(prefix="easy_install-")
        elif not os.path.isdir(options.tmpdir):
            os.makedirs(options.tmpdir)
        return os.path.realpath(options.tmpdir)

    try:
        index = index_type(options.index_url)
        inst = installer_type(options.instdir, options.multi)

        if options.scan_urls:
            for url in options.scan_urls:
                index.scan_url(url)

        for spec in args:
            tmpdir = alloc_tmp()
            try:
                print "Downloading", spec
                download = index.download(spec, tmpdir)
                if download is None:
                    raise RuntimeError(
                        "Could not find distribution for %r" % spec
                    )

                print "Installing", os.path.basename(download)
                for dist in inst.install_eggs(download,options.zip_ok, tmpdir):
                    index.add(dist)
                    print inst.installation_report(dist)

            finally:
                if options.tmpdir is None:
                    shutil.rmtree(tmpdir)

    except RuntimeError, v:
        print >>sys.stderr,"error:",v
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])

