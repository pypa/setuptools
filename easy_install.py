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
import zipfile
import tarfile
import shutil
import urlparse
import urllib
import tempfile
import __builtin__

from distutils.sysconfig import get_python_lib
from shutil import rmtree   # must have, because it can be called from __del__
from pkg_resources import *
_os = sys.modules[os.name]
_open = open

class Opener(urllib.FancyURLopener):
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        """Default error handling -- don't raise an exception."""
        info = urllib.addinfourl(fp, headers, "http:" + url)
        info.status, info.reason = errcode, errmsg
        return info
opener = Opener()

HREF = re.compile(r"""href\s*=\s*['"]?([^'"> ]+)""", re.I)
EXTENSIONS = ".tar.gz .tar.bz2 .tar .zip .tgz".split()

def distros_for_url(url, metadata=None):
    """Yield egg or source distribution objects that might be found at a URL"""

    path = urlparse.urlparse(url)[2]
    base = urllib.unquote(path.split('/')[-1])

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
    # versions in source distribution names.

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

        f = opener.open(url)
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
                    urllib.unquote, link[len(self.index_url):].split('/')
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

class Installer:
    """Manage a download/build/install process"""

    pth_file = None
    cleanup = False

    def __init__(self,
        instdir=None, zip_ok=False, multi=None, tmpdir=None, index=None
    ):
        if index is None:
            index = AvailableDistributions()
        if tmpdir is None:
            tmpdir = tempfile.mkdtemp(prefix="easy_install-")
            self.cleanup = True
        elif not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)
        self.tmpdir = os.path.realpath(tmpdir)

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
        self.index = index
        self.instdir = instdir
        self.zip_ok = zip_ok
        self.multi = multi

    def close(self):
        if self.cleanup and os.path.isdir(self.tmpdir):
            rmtree(self.tmpdir,True)

    def __del__(self):
        self.close()

    def samefile(self,p1,p2):
        if hasattr(os.path,'samefile') and (
            os.path.exists(p1) and os.path.exists(p2)
        ):
            return os.path.samefile(p1,p2)
        return (
            os.path.normpath(os.path.normcase(p1)) ==
            os.path.normpath(os.path.normcase(p2))
        )

    def download(self, spec):
        """Locate and/or download or `spec`, returning a local filename"""
        if isinstance(spec,Requirement):
            pass
        else:
            scheme = URL_SCHEME(spec)
            if scheme:
                # It's a url, download it to self.tmpdir
                return self._download_url(scheme.group(1), spec)

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
        dist = self.index.best_match(spec,[])
        if dist is not None:
            return self.download(dist.path)
        return None

    def install_eggs(self, dist_filename):
        # .egg dirs or files are already built, so just return them
        if dist_filename.lower().endswith('.egg'):
            return [self.install_egg(dist_filename,True)]

        # Anything else, try to extract and build
        if os.path.isfile(dist_filename):
            self._extract_file(dist_filename)

        # Find the setup.py file
        from glob import glob
        setup_script = os.path.join(self.tmpdir, 'setup.py')
        if not os.path.exists(setup_script):
            setups = glob(os.path.join(self.tmpdir, '*', 'setup.py'))
            if not setups:
                raise RuntimeError(
                    "Couldn't find a setup script in %s" % dist_filename
                )
            if len(setups)>1:
                raise RuntimeError(
                    "Multiple setup scripts in %s" % dist_filename
                )
            setup_script = setups[0]

        self._run_setup(setup_script)

        eggs = []
        for egg in glob(
            os.path.join(os.path.dirname(setup_script),'dist','*.egg')
        ):
            eggs.append(self.install_egg(egg, self.zip_ok))

        return eggs








    def _extract_zip(self,zipname,extract_dir):
        z = zipfile.ZipFile(zipname)
        try:
            for info in z.infolist():
                name = info.filename

                # don't extract absolute paths or ones with .. in them
                if name.startswith('/') or '..' in name:
                    continue

                target = os.path.join(extract_dir,name)
                if name.endswith('/'):
                    # directory
                    ensure_directory(target)
                else:
                    # file
                    ensure_directory(target)
                    data = z.read(info.filename)
                    f = open(target,'wb')
                    try:
                        f.write(data)
                    finally:
                        f.close()
                        del data
        finally:
            z.close()

    def _extract_tar(self,tarobj):
        try:
            tarobj.chown = lambda *args: None   # don't do any chowning!
            for member in tarobj:
                if member.isfile() or member.isdir():
                    name = member.name
                    # don't extract absolute paths or ones with .. in them
                    if not name.startswith('/') and '..' not in name:
                        tarobj.extract(member,self.tmpdir)
        finally:
            tarobj.close()



    def _run_setup(self, setup_script):
        from setuptools.command import bdist_egg
        sys.modules.setdefault('distutils.command.bdist_egg', bdist_egg)
        old_dir = os.getcwd()
        save_argv = sys.argv[:]
        save_path = sys.path[:]
        try:
            os.chdir(os.path.dirname(setup_script))
            try:
                sys.argv[:] = [setup_script, '-q', 'bdist_egg']
                sys.path.insert(0,os.getcwd())
                DirectorySandbox(self.tmpdir).run(
                    lambda: execfile(
                        "setup.py",
                        {'__file__':setup_script, '__name__':'__main__'}
                    )
                )
            except SystemExit, v:
                if v.args and v.args[0]:
                    raise RuntimeError(
                        "Setup script exited with %s" % (v.args[0],)
                    )
        finally:
            os.chdir(old_dir)
            sys.path[:] = save_path
            sys.argv[:] = save_argv















    def install_egg(self, egg_path, zip_ok):

        destination = os.path.join(self.instdir, os.path.basename(egg_path))
        ensure_directory(destination)

        if not self.samefile(egg_path, destination):
            if os.path.isdir(destination):
                shutil.rmtree(destination)
            elif os.path.isfile(destination):
                os.unlink(destination)

            if zip_ok:
                if egg_path.startswith(self.tmpdir):
                    shutil.move(egg_path, destination)
                else:
                    shutil.copy2(egg_path, destination)

            elif os.path.isdir(egg_path):
                shutil.move(egg_path, destination)

            else:
                os.mkdir(destination)
                self._extract_zip(egg_path, destination)

        if os.path.isdir(destination):
            dist = Distribution.from_filename(
                destination, metadata=PathMetadata(
                    destination, os.path.join(destination,'EGG-INFO')
                )
            )
        else:
            metadata = EggMetadata(zipimport.zipimporter(destination))
            dist = Distribution.from_filename(destination,metadata=metadata)
            self.index.add(dist)
        if self.pth_file is not None:
            map(self.pth_file.remove, self.pth_file.get(dist.key,())) # drop old
            if not self.multi:
                self.pth_file.add(dist) # add new
            self.pth_file.save()
        return dist

    def _download_url(self, scheme, url):

        # Determine download filename
        name = filter(None,urlparse.urlparse(url)[2].split('/'))[-1]

        while '..' in name:
            name = name.replace('..','.').replace('\\','_')

        filename = os.path.join(self.tmpdir,name)

        if scheme=='svn' or scheme.startswith('svn+'):
            return self._download_svn(url, filename)

        # Download the file
        class _opener(urllib.FancyURLopener):
            http_error_default = urllib.URLopener.http_error_default

        try:
            filename,headers = _opener().retrieve(
                url,filename
            )
        except IOError,v:
            if v.args and v.args[0]=='http error':
                raise RuntimeError(
                    "Download error: %s %s" % v.args[1:3]
                )
            else:
                raise

        if 'html' in headers['content-type'].lower():
            return self._download_html(url, headers, filename)

        # and return its filename
        return filename







    def _extract_file(self, dist_filename):
        if zipfile.is_zipfile(dist_filename):
            self._extract_zip(dist_filename, self.tmpdir)
        else:
            try:
                tar = tarfile.open(dist_filename)
            except tarfile.TarError:
                raise RuntimeError(
                    "Not a valid tar or zip archive: %s" % dist_filename
                )
            else:
                self._extract_tar(tar)


    def _download_html(self, url, headers, filename):
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
                        return self._download_sourceforge(url, page)
                break   # not an index page
        file.close()
        raise RuntimeError("Unexpected HTML page found at "+url)


    def _download_svn(self, url, filename):
        os.system("svn checkout -q %s %s" % (url, filename))
        return filename

    def _download_sourceforge(self, source_url, sf_page):
        """Download package from randomly-selected SourceForge mirror"""

        mirror_regex = re.compile(r'HREF=(/.*?\?use_mirror=[^>]*)')
        urls = [m.group(1) for m in mirror_regex.finditer(sf_page)]
        if not urls:
            raise RuntimeError(
                "URL looks like a Sourceforge mirror page, but no URLs found"
            )

        import random
        url = urlparse.urljoin(source_url, random.choice(urls))
        f = urllib.urlopen(url)
        match = re.search(
            r'<META HTTP-EQUIV="refresh" content=".*?URL=(.*?)"',
            f.read()
        )
        f.close()

        if match:
            download_url = match.group(1)
            scheme = URL_SCHEME(download_url)
            return self._download_url(scheme.group(1), download_url)
        else:
            raise RuntimeError(
                'No META HTTP-EQUIV="refresh" found in Sourceforge page at %s'
                % url
            )









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













class AbstractSandbox:
    """Wrap 'os' module and 'open()' builtin for virtualizing setup scripts"""

    _active = False

    def __init__(self):
        self._attrs = [
            name for name in dir(_os)
                if not name.startswith('_') and hasattr(self,name)
        ]

    def _copy(self, source):
        for name in self._attrs:
            setattr(os, name, getattr(source,name))

    def run(self, func):
        """Run 'func' under os sandboxing"""
        try:
            self._copy(self)
            __builtin__.open = __builtin__.file = self._open
            self._active = True
            return func()
        finally:
            self._active = False
            __builtin__.open = __builtin__.file = _open
            self._copy(_os)


    def _mk_dual_path_wrapper(name):
        original = getattr(_os,name)
        def wrap(self,src,dst,*args,**kw):
            if self._active:
                src,dst = self._remap_pair(name,src,dst,*args,**kw)
            return original(src,dst,*args,**kw)
        return wrap


    for name in ["rename", "link", "symlink"]:
        if hasattr(_os,name): locals()[name] = _mk_dual_path_wrapper(name)


    def _mk_single_path_wrapper(name, original=None):
        original = original or getattr(_os,name)
        def wrap(self,path,*args,**kw):
            if self._active:
                path = self._remap_input(name,path,*args,**kw)
            return original(path,*args,**kw)
        return wrap

    _open = _mk_single_path_wrapper('file', _open)
    for name in [
        "stat", "listdir", "chdir", "open", "chmod", "chown", "mkdir",
        "remove", "unlink", "rmdir", "utime", "lchown", "chroot", "lstat",
        "startfile", "mkfifo", "mknod", "pathconf", "access"
    ]:
        if hasattr(_os,name): locals()[name] = _mk_single_path_wrapper(name)


    def _mk_single_with_return(name):
        original = getattr(_os,name)
        def wrap(self,path,*args,**kw):
            if self._active:
                path = self._remap_input(name,path,*args,**kw)
                return self._remap_output(name, original(path,*args,**kw))
            return original(path,*args,**kw)
        return wrap

    for name in ['readlink', 'tempnam']:
        if hasattr(_os,name): locals()[name] = _mk_single_with_return(name)

    def _mk_query(name):
        original = getattr(_os,name)
        def wrap(self,*args,**kw):
            retval = original(*args,**kw)
            if self._active:
                return self._remap_output(name, retval)
            return retval
        return wrap

    for name in ['getcwd', 'tmpnam']:
        if hasattr(_os,name): locals()[name] = _mk_query(name)

    def _validate_path(self,path):
        """Called to remap or validate any path, whether input or output"""
        return path

    def _remap_input(self,operation,path,*args,**kw):
        """Called for path inputs"""
        return self._validate_path(path)

    def _remap_output(self,operation,path):
        """Called for path outputs"""
        return self._validate_path(path)

    def _remap_pair(self,operation,src,dst,*args,**kw):
        """Called for path pairs like rename, link, and symlink operations"""
        return (
            self._remap_input(operation+'-from',src,*args,**kw),
            self._remap_input(operation+'-to',dst,*args,**kw)
        )


class DirectorySandbox(AbstractSandbox):
    """Restrict operations to a single subdirectory - pseudo-chroot"""

    write_ops = dict.fromkeys([
        "open", "chmod", "chown", "mkdir", "remove", "unlink", "rmdir",
        "utime", "lchown", "chroot", "mkfifo", "mknod", "tempnam",
    ])

    def __init__(self,sandbox):
        self._sandbox = os.path.realpath(sandbox)
        self._prefix = os.path.join(self._sandbox,'')
        AbstractSandbox.__init__(self)

    def _violation(self, operation, *args, **kw):
        raise SandboxViolation(operation, args, kw)

    def _open(self, path, mode='r', *args, **kw):
        if mode not in ('r', 'rt', 'rb', 'rU') and not self._ok(path):
            self._violation("open", path, mode, *args, **kw)
        return _open(path,mode,*args,**kw)

    def tmpnam(self):
        self._violation("tmpnam")

    def _ok(self,path):
        active = self._active
        try:
            self._active = False
            realpath = os.path.realpath(path)
            if realpath==self._sandbox or realpath.startswith(self._prefix):
                return True
        finally:
            self._active = active

    def _remap_input(self,operation,path,*args,**kw):
        """Called for path inputs"""
        if operation in self.write_ops and not self._ok(path):
            self._violation(operation, os.path.realpath(path), *args, **kw)
        return path

    def _remap_pair(self,operation,src,dst,*args,**kw):
        """Called for path pairs like rename, link, and symlink operations"""
        if not self._ok(src) or not self._ok(dst):
            self._violation(operation, src, dst, *args, **kw)
        return (src,dst)


class SandboxViolation(RuntimeError):
    """A setup script attempted to modify the filesystem outside the sandbox"""

    def __str__(self):
        return """SandboxViolation: %s%r %s

The package setup script has attempted to modify files on your system
that are not within the EasyInstall build area, and has been aborted.

This package cannot be safely installed by EasyInstall, and may not
support alternate installation locations even if you run its setup
script by hand.  Please inform the package's author and the EasyInstall
maintainers to find out if a fix or workaround is available.""" % self.args


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

def main(argv, factory=Installer):

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





    try:
        index = PackageIndex(options.index_url)
        if options.scan_urls:
            for url in options.scan_urls:
                index.scan_url(url)

        for spec in args:
            inst = factory(
                options.instdir, options.zip_ok, options.multi, options.tmpdir,
                index
            )
            try:
                print "Downloading", spec
                downloaded = inst.download(spec)
                if downloaded is None:
                    raise RuntimeError(
                        "Could not find distribution for %r" % spec
                    )
                print "Installing", os.path.basename(downloaded)
                for dist in inst.install_eggs(downloaded):
                    print inst.installation_report(dist)
            finally:
                inst.close()

    except RuntimeError, v:
        print >>sys.stderr,"error:",v
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])










