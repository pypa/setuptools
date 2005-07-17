"""PyPI and direct package downloading"""

import sys, os.path, re, urlparse, urllib2
from pkg_resources import *
from distutils import log
from distutils.errors import DistutilsError

HREF = re.compile(r"""href\s*=\s*['"]?([^'"> ]+)""", re.I)
URL_SCHEME = re.compile('([-+.a-z0-9]{2,}):',re.I).match
EXTENSIONS = ".tar.gz .tar.bz2 .tar .zip .tgz".split()

__all__ = [
    'PackageIndex', 'distros_for_url', 'parse_bdist_wininst',
    'interpret_distro_name',
]


def parse_bdist_wininst(name):
    """Return (base,pyversion) or (None,None) for possible .exe name"""

    lower = name.lower()
    base, py_ver = None, None

    if lower.endswith('.exe'):
        if lower.endswith('.win32.exe'):
            base = name[:-10]
        elif lower.startswith('.win32-py',-16):
            py_ver = name[-7:-4]
            base = name[:-16]

    return base,py_ver










def distros_for_url(url, metadata=None):
    """Yield egg or source distribution objects that might be found at a URL"""

    path = urlparse.urlparse(url)[2]
    base = urllib2.unquote(path.split('/')[-1])
    return distros_for_filename(url, base, metadata)


def distros_for_filename(url_or_path, basename, metadata=None):
    """Yield egg or source distribution objects based on basename"""
    if basename.endswith('.egg.zip'):
        basename = basename[:-4]    # strip the .zip

    if basename.endswith('.egg'):   # only one, unambiguous interpretation       
        return [Distribution.from_location(url_or_path, basename, metadata)]

    if basename.endswith('.exe'):
        win_base, py_ver = parse_bdist_wininst(basename)
        if win_base is not None:
            return interpret_distro_name(
                url_or_path, win_base, metadata, py_ver, BINARY_DIST, "win32"
            )

    # Try source distro extensions (.zip, .tgz, etc.)
    #
    for ext in EXTENSIONS:
        if basename.endswith(ext):
            basename = basename[:-len(ext)]
            return interpret_distro_name(url_or_path, basename, metadata)

    return []  # no extension matched










def interpret_distro_name(url_or_path, basename, metadata,
    py_version=None, distro_type=SOURCE_DIST, platform=None
):

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

    parts = basename.split('-')
    for p in range(1,len(parts)+1):
        yield Distribution(
            url_or_path, metadata, '-'.join(parts[:p]), '-'.join(parts[p:]),
            py_version=py_version, distro_type = distro_type,
            platform = platform
        )


















class PackageIndex(AvailableDistributions):
    """A distribution index that scans web pages for download URLs"""

    def __init__(self,index_url="http://www.python.org/pypi",*args,**kw):
        AvailableDistributions.__init__(self,*args,**kw)
        self.index_url = index_url + "/"[:not index_url.endswith('/')]
        self.scanned_urls = {}
        self.fetched_urls = {}
        self.package_pages = {}

    def process_url(self, url, retrieve=False):
        """Evaluate a URL as a possible download, and maybe retrieve it"""

        if url in self.scanned_urls and not retrieve:
            return

        self.scanned_urls[url] = True

        if not URL_SCHEME(url):
            # process filenames or directories
            if os.path.isfile(url):
                dists = list(
                    distros_for_filename(
                        os.path.realpath(url), os.path.basename(url)
                    )
                )
            elif os.path.isdir(url):
                url = os.path.realpath(url)
                for item in os.listdir(url):
                    self.process_url(os.path.join(url,item))
                return
            else:
                self.warn("Not found: %s", url)
                return
        else:
            dists = list(distros_for_url(url))

        if dists:
            self.debug("Found link: %s", url)


        if dists or not retrieve or url in self.fetched_urls:
            for dist in dists:
                self.add(dist)
            # don't need the actual page
            return

        self.info("Reading %s", url)
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

        for match in HREF.finditer(page):
            link = urlparse.urljoin(base, match.group(1))
            self.process_url(link)


















    def process_index(self,url,page):
        """Process the contents of a PyPI page"""

        def scan(link):
            # Process a URL to see if it's for a package page
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











    def find_packages(self, requirement):
        self.scan_url(self.index_url + requirement.project_name+'/')
        if not self.package_pages.get(requirement.key):
            # We couldn't find the target package, so search the index page too
            self.warn(
                "Couldn't find index page for %r (maybe misspelled?)",
                requirement.project_name
            )
            if self.index_url not in self.fetched_urls:
                self.warn(
                    "Scanning index of all packages (this may take a while)"
                )
            self.scan_url(self.index_url)

        for url in self.package_pages.get(requirement.key,()):
            # scan each page that might be related to the desired package
            self.scan_url(url)

    def obtain(self, requirement, installer=None):
        self.find_packages(requirement)
        for dist in self.get(requirement.key, ()):
            if dist in requirement:
                return dist
            self.debug("%s does not match %s", requirement, dist)
        return super(PackageIndex, self).obtain(requirement,installer)
















    def download(self, spec, tmpdir):
        """Locate and/or download `spec` to `tmpdir`, returning a local path

        `spec` may be a ``Requirement`` object, or a string containing a URL,
        an existing local filename, or a project/version requirement spec
        (i.e. the string form of a ``Requirement`` object).

        If `spec` is a ``Requirement`` object or a string containing a
        project/version requirement spec, this method is equivalent to
        the ``fetch()`` method.  If `spec` is a local, existing file or
        directory name, it is simply returned unchanged.  If `spec` is a URL,
        it is downloaded to a subpath of `tmpdir`, and the local filename is
        returned.  Various errors may be raised if a problem occurs during
        downloading.
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
                    raise DistutilsError(
                        "Not a URL, existing file, or requirement spec: %r" %
                        (spec,)
                    )

        return self.fetch(spec, tmpdir, force_scan)







    def fetch(self, requirement, tmpdir, force_scan=False):
        """Obtain a file suitable for fulfilling `requirement`

        `requirement` must be a ``pkg_resources.Requirement`` instance.
        If necessary, or if the `force_scan` flag is set, the requirement is
        searched for in the (online) package index as well as the locally
        installed packages.  If a distribution matching `requirement` is found,
        the return value is the same as if you had called the ``download()``
        method with the matching distribution's URL.  If no matching
        distribution is found, returns ``None``.
        """

        # process a Requirement
        self.info("Searching for %s", requirement)

        if force_scan:
            self.find_packages(requirement)

        dist = self.best_match(requirement, [])     # XXX

        if dist is not None:
            self.info("Best match: %s", dist)
            return self.download(dist.path, tmpdir)

        self.warn(
            "No local packages or download links found for %s", requirement
        )
        return None













    dl_blocksize = 8192

    def _download_to(self, url, filename):
        self.info("Downloading %s", url)

        # Download the file
        fp, tfp = None, None
        try:
            fp = self.open_url(url)
            if isinstance(fp, urllib2.HTTPError):
                raise DistutilsError(
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
            raise DistutilsError("Download error: %s" % v.reason)


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

        if name.endswith('.egg.zip'):
            name = name[:-4]    # strip the extra .zip before download

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

    def scan_url(self, url):
        self.process_url(url, True)


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
        raise DistutilsError("Unexpected HTML page found at "+url)


    def _download_svn(self, url, filename):
        self.info("Doing subversion checkout from %s to %s", url, filename)
        os.system("svn checkout -q %s %s" % (url, filename))
        return filename

    def debug(self, msg, *args):
        log.debug(msg, *args)

    def info(self, msg, *args):
        log.info(msg, *args)

    def warn(self, msg, *args):
        log.warn(msg, *args)

    def _download_sourceforge(self, source_url, sf_page, tmpdir):
        """Download package from randomly-selected SourceForge mirror"""

        self.debug("Processing SourceForge mirror page")

        mirror_regex = re.compile(r'HREF=(/.*?\?use_mirror=[^>]*)')
        urls = [m.group(1) for m in mirror_regex.finditer(sf_page)]
        if not urls:
            raise DistutilsError(
                "URL looks like a Sourceforge mirror page, but no URLs found"
            )

        import random
        url = urlparse.urljoin(source_url, random.choice(urls))

        self.info(
            "Requesting redirect to (randomly selected) %r mirror",
            url.split('=',1)[-1]
        )

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
            raise DistutilsError(
                'No META HTTP-EQUIV="refresh" found in Sourceforge page at %s'
                % url
            )





