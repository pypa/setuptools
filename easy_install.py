#!python
"""\

Easy Install
------------

A tool for doing automatic download/extract/build of distutils-based Python
packages.  For detailed documentation, see the accompanying EasyInstall.txt
file, or visit the `EasyInstall home page`__.

__ http://peak.telecommunity.com/DevCenter/EasyInstall

"""

import sys, os.path, zipimport, shutil, tempfile

from setuptools.sandbox import run_setup
from distutils.sysconfig import get_python_lib

from setuptools.archive_util import unpack_archive
from setuptools.package_index import PackageIndex
from pkg_resources import *



















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

