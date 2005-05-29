#!python
"""\
Easy Install
============

Easy Install is a python module (easy_install) that lets you automatically
download, build, install, and manage Python packages.

.. contents:: **Table of Contents**


Downloading and Installing a Package
------------------------------------

For basic use of ``easy_install``, you need only supply the filename or URL of
a source distribution or .egg file (`Python Egg`__).

__ http://peak.telecommunity.com/DevCenter/PythonEggs

**Example 1**. Download a source distribution, automatically building and
installing it::

    easy_install http://example.com/path/to/MyPackage-1.2.3.tgz

**Example 2**. Install an already-downloaded .egg file::

    easy_install /my_downloads/OtherPackage-3.2.1-py2.3.egg

Easy Install recognizes distutils *source* (not binary) distribution files with
extensions of .tgz, .tar, .tar.gz, .tar.bz2, or .zip. And of course it handles
already-built .egg distributions.

By default, packages are installed to the running Python installation's
``site-packages`` directory, unless you provide the ``-d`` or ``--install-dir``
option to specify an alternative directory.

Packages installed to ``site-packages`` are added to an ``easy-install.pth``
file, so that Python will be able to import the package by default. If you do
not want this to happen, you should use the ``-m`` or ``--multi`` option, which
allows multiple versions of the same package to be selected at runtime.

Note that installing to a directory other than ``site-packages`` already
implies the ``-m`` option, so if you cannot install to ``site-packages``,
please see the `Options`_ section below (under ``--multi``) to find out how to
select packages at runtime.


Upgrading a Package
-------------------

You don't need to do anything special to upgrade a package: just install the
new version. If you're using ``-m`` or ``--multi`` (or installing outside of
``site-packages``), the runtime system automatically selects the newest
available version of a package. If you're installing to ``site-packages`` and
not using ``-m``, installing a package automatically replaces its older version
in the ``easy-install.pth`` file, so that Python will import the latest version
by default.

``easy_install`` never actually deletes packages (unless you're installing a
package with the same name and version number as an existing package), so if
you want to get rid of older versions of a package, please see `Uninstalling
Packages`_, below.


Changing the Active Version (``site-packages`` installs only)
-------------------------------------------------------------

If you've upgraded a package, but need to revert to a previously-installed
version, you can do so like this::

    easy_install PackageName==1.2.3

Where ``1.2.3`` is replaced by the exact version number you wish to switch to.
Note that the named package and version must already have been installed to
``site-packages``.

If you'd like to switch to the latest version of ``PackageName``, you can do so
like this::

    easy_install PackageName

This will activate the latest installed version.


Uninstalling Packages
---------------------

If you have replaced a package with another version, then you can just delete
the package(s) you don't need by deleting the PackageName-versioninfo.egg file
or directory (found in the installation directory).

If you want to delete the currently installed version of a package (or all
versions of a package), you should first run::

    easy_install -m PackageName

This will ensure that Python doesn't continue to search for a package you're
planning to remove. After you've done this, you can safely delete the .egg
files or directories.


Options
-------

``--zip, -z``
    Enable installing the package as a zip file. This can significantly
    increase Python's overall import performance if you're installing to
    ``site-packages`` and not using the ``--multi`` option, because Python
    process zipfile entries on ``sys.path`` much faster than it does
    directories. So, if you don't use this option, and you install a lot of
    packages, some of them may be slower to import.

    But, this option is disabled by default, unless you're installing from an
    already-built binary zipfile (``.egg`` file). This is to avoid problems
    when using packages that dosn't support running from a zip file. Such
    packages usually access data files in their package directories using the
    Python ``__file__`` or ``__path__`` attribute, instead of the
    ``pkg_resources`` API. So, if you find that a package doesn't work properly
    when used with this option, you may want to suggest to the author that they
    switch to using the ``pkg_resources`` resource API, which will allow their
    package to work whether it's installed as a zipfile or not.

    (Note: this option only affects the installation of newly-built packages
    that are not already installed in the target directory; if you want to
    convert an existing installed version from zipped to unzipped or vice
    versa, you'll need to delete the existing version first.)

``--multi-version, -m``
    "Multi-version" mode. Specifying this option prevents ``easy_install`` from
    adding an ``easy-install.pth`` entry for the package being installed, and
    if an entry for any version the package already exists, it will be removed
    upon successful installation. In multi-version mode, no specific version of
    the package is available for importing, unless you use
    ``pkg_resources.require()`` to put it on ``sys.path``. This can be as
    simple as::

        from pkg_resources import require
        require("SomePackage", "OtherPackage", "MyPackage")

    which will put the latest installed version of the specified packages on
    ``sys.path`` for you. (For more advanced uses, like selecting specific
    versions and enabling optional dependencies, see the ``pkg_resources`` API
    doc.) Note that if you install to a directory other than ``site-packages``,
    this option is automatically in effect, because ``.pth`` files can only be
    used in ``site-packages`` (at least in Python 2.3 and 2.4). So, if you use
    the ``--install-dir`` or ``-i`` options, you must also use ``require()`` to
    enable packages at runtime

``--install-dir=DIR, -d DIR``
    Set the installation directory. It is up to you to ensure that this
    directory is on ``sys.path`` at runtime, and to use
    ``pkg_resources.require()`` to enable the installed package(s) that you
    need.
"""

import sys, os.path, pkg_resources, re, zipimport
from pkg_resources import *







class Installer:
    """Manage a download/build/install process"""

    pth_file = None

    def __init__(self, instdir=None, zip_ok=False, multi=None, tmpdir=None):
        from distutils.sysconfig import get_python_lib
        site_packages = get_python_lib()

        if tmpdir is None:
            from tempfile import mkdtemp
            tmpdir = mkdtemp(prefix="easy_install-")

        self.tmpdir = tmpdir

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
        self.zip_ok = zip_ok
        self.multi = multi

    def close(self):
        if os.path.isdir(self.tmpdir):
            from shutil import rmtree
            rmtree(self.tmpdir,True)

    def __del__(self):
        self.close()

    def samefile(self,p1,p2):
        try:
            os.path.samefile
        except AttributeError:
            return (
                os.path.normpath(os.path.normcase(p1)) ==
                os.path.normpath(os.path.normcase(p2))
            )
        else:
            return os.path.samefile(p1,p2)

    def download(self, spec):
        """Locate and/or download or `spec`, returning a local filename"""
        if isinstance(spec,Requirement):
            pass
        else:
            scheme = URL_SCHEME(spec)
            if scheme:
                # It's a url, download it to self.tmpdir
                return self._download_url(scheme, spec)

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
        dist = AvailableDistributions().best_match(spec,[])
        if dist is not None and dist.path.endswith('.egg'):
            return dist.path

        # TODO: search here for a distro to download

        raise DistributionNotFound(spec)

    def install_eggs(self, dist_filename):
        # .egg dirs or files are already built, so just return them
        if dist_filename.lower().endswith('.egg'):
            return self.install_egg(dist_filename,True)

        # Anything else, try to extract and build
        import zipfile, tarfile
        if zipfile.is_zipfile(dist_filename):
            self._extract_zip(dist_filename, self.tmpdir)
        else:
            import tarfile
            try:
                tar = tarfile.open(dist_filename)
            except tarfile.TarError:
                raise RuntimeError(
                    "Not a valid tar or zip archive: %s" % dist_filename
                )
            else:
                self._extract_tar(tar)

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
        for egg in glob(
            os.path.join(os.path.dirname(setup_script),'dist','*.egg')
        ):
            self.install_egg(egg, self.zip_ok)

    def _extract_zip(self,zipname,extract_dir):
        import zipfile
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
                execfile(setup_script,
                    {'__file__':setup_script, '__name__':'__main__'}
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
        import shutil
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

        if self.pth_file is not None:
            if os.path.isdir(destination):
                dist = Distribution.from_filename(
                    destination, metadata=PathMetadata(
                        destination, os.path.join(destination,'EGG-INFO')
                    )
                )
            else:
                metadata = EggMetadata(zipimport.zipimporter(destination))
                dist = Distribution.from_filename(destination,metadata=metadata)

            # remove old
            map(self.pth_file.remove, self.pth_file.get(dist.key,()))
            if not self.multi:
                self.pth_file.add(dist) # add new
            self.pth_file.save()

    def _download_url(self, scheme, url):
        # Determine download filename
        from urlparse import urlparse
        name = filter(None,urlparse(url)[2].split('/'))[-1]
        while '..' in name:
            name = name.replace('..','.').replace('\\','_')

        # Download the file
        from urllib import FancyURLopener, URLopener
        class opener(FancyURLopener):
            http_error_default = URLopener.http_error_default
        try:
            filename,headers = opener().retrieve(
                url,os.path.join(self.tmpdir,name)
            )
        except IOError,v:
            if v.args and v.args[0]=='http error':
                raise RuntimeError(
                    "Download error: %s %s" % v.args[1:3]
                )
            else:
                raise
        # and return its filename
        return filename

















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

def main(argv):
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

    (options, args) = parser.parse_args()

    try:
        if not args:
            raise RuntimeError("No urls, filenames, or requirements specified")

        for spec in args:
            inst = Installer(options.instdir, options.zip_ok, options.multi)
            try:
                print "Downloading", spec
                downloaded = inst.download(spec)
                print "Installing", os.path.basename(downloaded)
                inst.install_eggs(downloaded)
            finally:
                inst.close()
    except RuntimeError, v:
        parser.error(str(v))

if __name__ == '__main__':
    main(sys.argv[1:])




