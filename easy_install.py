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

from setuptools import Command
from setuptools.sandbox import run_setup
from distutils import log, dir_util
from distutils.sysconfig import get_python_lib
from distutils.errors import DistutilsArgError, DistutilsOptionError
from setuptools.archive_util import unpack_archive
from setuptools.package_index import PackageIndex
from pkg_resources import *


def samefile(p1,p2):
    if hasattr(os.path,'samefile') and (
        os.path.exists(p1) and os.path.exists(p2)
    ):
        return os.path.samefile(p1,p2)
    return (
        os.path.normpath(os.path.normcase(p1)) ==
        os.path.normpath(os.path.normcase(p2))
    )






class easy_install(Command):
    """Manage a download/build/install process"""

    description = "Find/get/install Python packages"
    command_consumes_arguments = True
    user_options = [
        ("zip-ok", "z", "install package as a zipfile"),
        ("multi-version", "m", "make apps have to require() a version"),
        ("install-dir=", "d", "install package to DIR"),
        ("script-dir=", "s", "install scripts to DIR"),
        ("exclude-scripts", "x", "Don't install scripts"),
        ("index-url=", "i", "base URL of Python Package Index"),
        ("find-links=", "f", "additional URL(s) to search for packages"),
        ("build-directory=", "b",
            "download/extract/build in DIR; keep the results"),
        ('optimize=', 'O',
         "also compile with optimization: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
    ]

    boolean_options = [ 'zip-ok', 'multi-version', 'exclude-scripts' ]
    create_index = PackageIndex

    def initialize_options(self):
        self.zip_ok = None
        self.multi_version = None
        self.install_dir = self.script_dir = self.exclude_scripts = None
        self.index_url = None
        self.find_links = None
        self.build_directory = None
        self.args = None
        self.optimize = None

        # Options not specifiable via command line
        self.package_index = None
        self.pth_file = None





    def finalize_options(self):
        # If a non-default installation directory was specified, default the
        # script directory to match it.
        if self.script_dir is None:
            self.script_dir = self.install_dir

        # Let install_dir get set by install_lib command, which in turn
        # gets its info from the install command, and takes into account
        # --prefix and --home and all that other crud.
        self.set_undefined_options('install_lib',
            ('install_dir','install_dir')
        )
        # Likewise, set default script_dir from 'install_scripts.install_dir'
        self.set_undefined_options('install_scripts',
            ('install_dir', 'script_dir')
        )

        site_packages = get_python_lib()
        instdir = self.install_dir

        if instdir is None or samefile(site_packages,instdir):
            instdir = site_packages
            if self.pth_file is None:
                self.pth_file = PthDistributions(
                    os.path.join(instdir,'easy-install.pth')
                )
            self.install_dir = instdir

        elif self.multi_version is None:
            self.multi_version = True

        elif not self.multi_version:
            # explicit false set from Python code; raise an error
            raise DistutilsArgError(
                "Can't do single-version installs outside site-packages"
            )

        self.index_url = self.index_url or "http://www.python.org/pypi"
        if self.package_index is None:
            self.package_index = self.create_index(self.index_url)

        if self.find_links is not None:
            if isinstance(self.find_links, basestring):
                self.find_links = self.find_links.split()
        else:
            self.find_links = []

        self.set_undefined_options('install_lib', ('optimize','optimize'))

        if not isinstance(self.optimize,int):
            try:
                self.optimize = int(self.optimize)
                if not (0 <= self.optimize <= 2): raise ValueError
            except ValueError:
                raise DistutilsOptionError("--optimize must be 0, 1, or 2")

        if not self.args:
            raise DistutilsArgError(
                "No urls, filenames, or requirements specified (see --help)")

        elif len(self.args)>1 and self.build_directory is not None:
            raise DistutilsArgError(
                "Build directory can only be set when using one URL"
            )


















    def alloc_tmp(self):
        if self.build_directory is None:
            return tempfile.mkdtemp(prefix="easy_install-")
        tmpdir = os.path.realpath(self.build_directory)
        if not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)
        return tmpdir


    def run(self):
        if self.verbose<>self.distribution.verbose:
            log.set_verbosity(self.verbose)
        try:
            for link in self.find_links:
                self.package_index.scan_url(link)
            for spec in self.args:
                self.easy_install(spec)
        finally:
            log.set_verbosity(self.distribution.verbose)


    def easy_install(self, spec):
        tmpdir = self.alloc_tmp()
        try:
            download = self.package_index.download(spec, tmpdir)
            if download is None:
                raise RuntimeError(
                    "Could not find distribution for %r" % spec
                )

            log.info("Processing %s", os.path.basename(download))
            for dist in self.install_eggs(download, self.zip_ok, tmpdir):
                self.package_index.add(dist)
                self.install_egg_scripts(dist)
                log.warn(self.installation_report(dist))

        finally:
            if self.build_directory is None:
                shutil.rmtree(tmpdir)


    def install_egg_scripts(self, dist):
        metadata = dist.metadata
        if self.exclude_scripts or not metadata.metadata_isdir('scripts'):
            return

        from distutils.command.build_scripts import first_line_re

        for script_name in metadata.metadata_listdir('scripts'):
            target = os.path.join(self.script_dir, script_name)

            log.info("Installing %s script to %s", script_name,self.script_dir)

            script_text = metadata.get_metadata('scripts/'+script_name)
            script_text = script_text.replace('\r','\n')
            first, rest = script_text.split('\n',1)

            match = first_line_re.match(first)
            options = ''
            if match:
                options = match.group(1) or ''
                if options:
                    options = ' '+options

            spec = '%s==%s' % (dist.name,dist.version)

            script_text = '\n'.join([
                "#!%s%s" % (os.path.normpath(sys.executable),options),
                "# EASY-INSTALL-SCRIPT: %r,%r" % (spec, script_name),
                "import pkg_resources",
                "pkg_resources.run_main(%r, %r)" % (spec, script_name)
            ])
            if not self.dry_run:
                f = open(target,"w")
                f.write(script_text)
                f.close()






    def install_eggs(self, dist_filename, zip_ok, tmpdir):
        # .egg dirs or files are already built, so just return them
        if dist_filename.lower().endswith('.egg'):
            return [self.install_egg(dist_filename, True, tmpdir)]

        # Anything else, try to extract and build
        if os.path.isfile(dist_filename):
            unpack_archive(dist_filename, tmpdir, self.unpack_progress)

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

        self.build_egg(tmpdir, setup_script)
        dist_dir = os.path.join(os.path.dirname(setup_script),'dist')

        eggs = []
        for egg in glob(os.path.join(dist_dir,'*.egg')):
            eggs.append(self.install_egg(egg, zip_ok, tmpdir))

        if not eggs and not self.dry_run:
            log.warn("No eggs found in %s (setup script problem?)", dist_dir)

        return eggs






    def install_egg(self, egg_path, zip_ok, tmpdir):
        destination = os.path.join(self.install_dir,os.path.basename(egg_path))
        destination = os.path.abspath(destination)
        if not self.dry_run:
            ensure_directory(destination)

        if not samefile(egg_path, destination):
            if os.path.isdir(destination):
                dir_util.remove_tree(destination, dry_run=self.dry_run)

            elif os.path.isfile(destination):
                self.execute(os.unlink,(destination,),"Removing "+destination)

            if zip_ok:
                if egg_path.startswith(tmpdir):
                    f,m = shutil.move, "Moving"
                else:
                    f,m = shutil.copy2, "Copying"
            elif os.path.isdir(egg_path):
                f,m = shutil.move, "Moving"
            else:
                self.mkpath(destination)
                f,m = self.unpack_and_compile, "Extracting"

            self.execute(f, (egg_path, destination),
                (m+" %s to %s") %
                (os.path.basename(egg_path),os.path.dirname(destination)))

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

        msg = "\nInstalled %(eggloc)s to %(instdir)s"
        if self.multi_version:
            msg += """

Because this distribution was installed --multi-version or --install-dir,
before you can import modules from this package in an application, you
will need to 'import pkg_resources' and then use a 'require()' call
similar to one of these examples, in order to select the desired version:

    pkg_resources.require("%(name)s")  # latest installed version
    pkg_resources.require("%(name)s==%(version)s")  # this exact version
    pkg_resources.require("%(name)s>=%(version)s")  # this version or higher
"""
        if not samefile(get_python_lib(),self.install_dir):
            msg += """

Note also that the installation directory must be on sys.path at runtime for
this to work.  (e.g. by being the application's script directory, by being on
PYTHONPATH, or by being added to sys.path by your code.)
"""
        eggloc = os.path.basename(dist.path)
        instdir = os.path.realpath(self.install_dir)
        name = dist.name
        version = dist.version
        return msg % locals()

    def update_pth(self,dist):
        if self.pth_file is not None:
            remove = self.pth_file.remove
            for d in self.pth_file.get(dist.key,()):    # drop old entries
                log.info("Removing %s from .pth file", d)
                remove(d)
            if not self.multi_version:
                log.info("Adding %s to .pth file", dist)
                self.pth_file.add(dist) # add new entry
            self.pth_file.save()


    def build_egg(self, tmpdir, setup_script):
        from setuptools.command import bdist_egg
        sys.modules.setdefault('distutils.command.bdist_egg', bdist_egg)

        args = ['bdist_egg']
        if self.verbose>2:
            v = 'v' * self.verbose - 1
            args.insert(0,'-'+v)
        elif self.verbose<2:
            args.insert(0,'-q')
        if self.dry_run:
            args.insert(0,'-n')

        log.info("Running %s %s", setup_script[len(tmpdir)+1:], ' '.join(args))
        try:
            try:
                run_setup(setup_script, args)
            except SystemExit, v:
                raise RuntimeError(
                    "Setup script exited with %s" % (v.args[0],)
                )
        finally:
            log.set_verbosity(self.verbose) # restore our log verbosity


















    def unpack_progress(self, src, dst):
        # Progress filter for unpacking
        log.debug("Unpacking %s to %s", src, dst)
        return True     # only unpack-and-compile skips files for dry run


    def unpack_and_compile(self, egg_path, destination):
        to_compile = []

        def pf(src,dst):
            if dst.endswith('.py'):
                to_compile.append(dst)
            self.unpack_progress(src,dst)
            return not self.dry_run

        unpack_archive(egg_path, destination, pf)

        from distutils.util import byte_compile
        try:
            # try to make the byte compile messages quieter
            log.set_verbosity(self.verbose - 1)

            byte_compile(to_compile, optimize=0, force=1, dry_run=self.dry_run) 
            if self.optimize:
                byte_compile(
                    to_compile, optimize=self.optimize, force=1,
                    dry_run=self.dry_run
                )
        finally:
            log.set_verbosity(self.verbose)     # restore original verbosity











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




def main(argv, cmds={'easy_install':easy_install}):
    from setuptools import setup
    try:
        setup(cmdclass = cmds, script_args = ['-q','easy_install', '-v']+argv)
    except RuntimeError, v:
        print >>sys.stderr,"error:",v
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])






























