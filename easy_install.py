#!python
"""\

Easy Install
------------

A tool for doing automatic download/extract/build of distutils-based Python
packages.  For detailed documentation, see the accompanying EasyInstall.txt
file, or visit the `EasyInstall home page`__.

__ http://peak.telecommunity.com/DevCenter/EasyInstall
"""

import sys, os.path, zipimport, shutil, tempfile, zipfile

from setuptools import Command
from setuptools.sandbox import run_setup
from distutils import log, dir_util
from distutils.sysconfig import get_python_lib
from distutils.errors import DistutilsArgError, DistutilsOptionError
from setuptools.archive_util import unpack_archive
from setuptools.package_index import PackageIndex, parse_bdist_wininst
from setuptools.package_index import URL_SCHEME
from setuptools.command import bdist_egg
from pkg_resources import *

__all__ = [
    'samefile', 'easy_install', 'PthDistributions', 'extract_wininst_cfg',
    'main', 'get_exe_prefixes',
]

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
        ("upgrade", "U", "force upgrade (searches PyPI for latest versions)"),
        ("install-dir=", "d", "install package to DIR"),
        ("script-dir=", "s", "install scripts to DIR"),
        ("exclude-scripts", "x", "Don't install scripts"),
        ("always-copy", "a", "Copy all needed packages to install dir"),
        ("index-url=", "i", "base URL of Python Package Index"),
        ("find-links=", "f", "additional URL(s) to search for packages"),
        ("build-directory=", "b",
            "download/extract/build in DIR; keep the results"),
        ('optimize=', 'O',
         "also compile with optimization: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ('record=', None,
         "filename in which to record list of installed files"),
    ]
    boolean_options = [
        'zip-ok', 'multi-version', 'exclude-scripts', 'upgrade', 'always-copy'
    ]
    create_index = PackageIndex

    def initialize_options(self):
        self.zip_ok = None
        self.install_dir = self.script_dir = self.exclude_scripts = None
        self.index_url = None
        self.find_links = None
        self.build_directory = None
        self.args = None
        self.optimize = self.record = None
        self.upgrade = self.always_copy = self.multi_version = None
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
        # default --record from the install command
        self.set_undefined_options('install', ('record', 'record'))

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

        self.shadow_path = sys.path[:]

        for path_item in self.install_dir, self.script_dir:
            if path_item not in self.shadow_path:
                self.shadow_path.insert(0, self.install_dir)
        
        if self.package_index is None:
            self.package_index = self.create_index(
                self.index_url, search_path = self.shadow_path
            )

        self.local_index = AvailableDistributions(self.shadow_path)

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

        self.outputs = []



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
            if self.record:
                from distutils import file_util
                self.execute(
                    file_util.write_file, (self.record, self.outputs),
                    "writing list of installed files to '%s'" %
                    self.record
                )
        finally:
            log.set_verbosity(self.distribution.verbose)


    def add_output(self, path):
        if os.path.isdir(path):
            for base, dirs, files in walk(path):
                for filename in files:
                    self.outputs.append(os.path.join(base,filename))
        else:
            self.outputs.append(path)






    def easy_install(self, spec):
        tmpdir = self.alloc_tmp()
        download = None

        try:           
            if not isinstance(spec,Requirement):
                if URL_SCHEME(spec):
                    # It's a url, download it to tmpdir and process
                    download = self.package_index.download(spec, tmpdir)
                    return self.install_item(None, download, tmpdir, True)                   

                elif os.path.exists(spec):
                    # Existing file or directory, just process it directly
                    return self.install_item(None, spec, tmpdir, True)
                else:
                    try:
                        spec = Requirement.parse(spec)
                    except ValueError:
                        raise RuntimeError(
                            "Not a URL, existing file, or requirement spec: %r"
                            % (spec,)
                        )

            if isinstance(spec, Requirement):
                download = self.package_index.fetch(spec, tmpdir, self.upgrade)
            else:
                spec = None

            if download is None:
                raise RuntimeError(
                    "Could not find distribution for %r" % spec
                )

            return self.install_item(spec, download, tmpdir)

        finally:
            if self.build_directory is None:
                shutil.rmtree(tmpdir)



    def install_item(self, spec, download, tmpdir, install_needed=False):
        # Installation is also needed if file in tmpdir or is not an egg
        install_needed = install_needed or os.path.dirname(download) == tmpdir
        install_needed = install_needed or not download.endswith('.egg')
        log.info("Processing %s", os.path.basename(download))
        if install_needed or self.always_copy:
            dists = self.install_eggs(download, self.zip_ok, tmpdir)
            for dist in dists:
                self.process_distribution(spec, dist)
        else:
            dists = [self.egg_distribution(download)]
            self.process_distribution(spec, dists[0], "Using")
        if spec is not None:
            for dist in dists:
                if dist in spec:
                    return dist

    def process_distribution(self, requirement, dist, *info):
        self.update_pth(dist)
        self.package_index.add(dist)
        self.local_index.add(dist)
        self.install_egg_scripts(dist)
        log.warn(self.installation_report(dist, *info))
        if requirement is None:
            requirement = Requirement.parse('%s==%s'%(dist.name,dist.version))
        if dist in requirement:
            log.info("Processing dependencies for %s", requirement)
            try:
                self.local_index.resolve(
                    [requirement], self.shadow_path, self.easy_install
                )
            except DistributionNotFound, e:
                raise RuntimeError(
                    "Could not find required distribution %s" % e.args
                )
            except VersionConflict, e:
                raise RuntimeError(
                    "Installed distribution %s conflicts with requirement %s"
                    % e.args
                )

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
                try:
                    os.chmod(target,0755)
                except (AttributeError, os.error):
                    pass


    def install_eggs(self, dist_filename, zip_ok, tmpdir):
        # .egg dirs or files are already built, so just return them
        if dist_filename.lower().endswith('.egg'):
            return [self.install_egg(dist_filename, True, tmpdir)]

        if dist_filename.lower().endswith('.exe'):
            return [self.install_exe(dist_filename, tmpdir)]

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



    def egg_distribution(self, egg_path):
        if os.path.isdir(egg_path):
            metadata = PathMetadata(egg_path,os.path.join(egg_path,'EGG-INFO'))
        else:
            metadata = EggMetadata(zipimport.zipimporter(egg_path))
        return Distribution.from_filename(egg_path,metadata=metadata)
        
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

            if os.path.isdir(egg_path):
                if egg_path.startswith(tmpdir):
                    f,m = shutil.move, "Moving"
                else:
                    f,m = shutil.copytree, "Copying"
            elif zip_ok:
                if egg_path.startswith(tmpdir):
                    f,m = shutil.move, "Moving"
                else:
                    f,m = shutil.copy2, "Copying"
            else:
                self.mkpath(destination)
                f,m = self.unpack_and_compile, "Extracting"

            self.execute(f, (egg_path, destination),
                (m+" %s to %s") %
                (os.path.basename(egg_path),os.path.dirname(destination)))

        self.add_output(destination)
        return self.egg_distribution(destination)

    def install_exe(self, dist_filename, tmpdir):
        # See if it's valid, get data
        cfg = extract_wininst_cfg(dist_filename)
        if cfg is None:
            raise RuntimeError(
                "%s is not a valid distutils Windows .exe" % dist_filename
            )

        # Create a dummy distribution object until we build the real distro
        dist = Distribution(None,
            name=cfg.get('metadata','name'),
            version=cfg.get('metadata','version'),
            platform="win32"
        )

        # Convert the .exe to an unpacked egg
        egg_path = dist.path = os.path.join(tmpdir, dist.egg_name()+'.egg')
        egg_tmp  = egg_path+'.tmp'
        self.exe_to_egg(dist_filename, egg_tmp)

        # Write EGG-INFO/PKG-INFO
        pkg_inf = os.path.join(egg_tmp, 'EGG-INFO', 'PKG-INFO')
        f = open(pkg_inf,'w')
        f.write('Metadata-Version: 1.0\n')
        for k,v in cfg.items('metadata'):
            if k<>'target_version':
                f.write('%s: %s\n' % (k.replace('_','-').title(), v))
        f.close()

        # Build .egg file from tmpdir
        bdist_egg.make_zipfile(
            egg_path, egg_tmp,
            verbose=self.verbose, dry_run=self.dry_run
        )

        # install the .egg        
        return self.install_egg(egg_path, self.zip_ok, tmpdir)




    def exe_to_egg(self, dist_filename, egg_tmp):
        """Extract a bdist_wininst to the directories an egg would use"""

        # Check for .pth file and set up prefix translations
        prefixes = get_exe_prefixes(dist_filename)
        to_compile = []
        native_libs = []

        def process(src,dst):
            for old,new in prefixes:
                if src.startswith(old):
                    src = new+src[len(old):]
                    dst = os.path.join(egg_tmp, *src.split('/'))
                    dl = dst.lower()
                    if dl.endswith('.pyd') or dl.endswith('.dll'):
                        native_libs.append(src)
                    elif dl.endswith('.py') and old!='SCRIPTS/':
                        to_compile.append(dst)
                    return dst
            if not src.endswith('.pth'):
                log.warn("WARNING: can't process %s", src)
            return None

        # extract, tracking .pyd/.dll->native_libs and .py -> to_compile
        unpack_archive(dist_filename, egg_tmp, process)
       
        for res in native_libs:
            if res.lower().endswith('.pyd'):    # create stubs for .pyd's
                parts = res.split('/')
                resource, parts[-1] = parts[-1], parts[-1][:-1]
                pyfile = os.path.join(egg_tmp, *parts)
                to_compile.append(pyfile)
                bdist_egg.write_stub(resource, pyfile)
        
        self.byte_compile(to_compile)   # compile .py's
        
        if native_libs:     # write EGG-INFO/native_libs.txt
            nl_txt = os.path.join(egg_tmp, 'EGG-INFO', 'native_libs.txt')
            ensure_directory(nl_txt)
            open(nl_txt,'w').write('\n'.join(native_libs)+'\n')

    def installation_report(self, dist, what="Installed"):
        """Helpful installation message for display to package users"""

        msg = "\n%(what)s %(eggloc)s"
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
        eggloc = dist.path
        name = dist.name
        version = dist.version
        return msg % locals()














    def build_egg(self, tmpdir, setup_script):
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



















    def update_pth(self,dist):
        if self.pth_file is None:
            return

        for d in self.pth_file.get(dist.key,()):    # drop old entries
            if self.multi_version or d.path != dist.path:
                log.info("Removing %s from easy-install.pth file", d)
                self.pth_file.remove(d)
                if d.path in self.shadow_path:
                    self.shadow_path.remove(d.path)

        if not self.multi_version:
            if dist.path in self.pth_file.paths:
                log.info(
                    "%s is already the active version in easy-install.pth",
                    dist
                )
            else:
                log.info("Adding %s to easy-install.pth file", dist)
                self.pth_file.add(dist) # add new entry
                if dist.path not in self.shadow_path:
                    self.shadow_path.append(dist.path)

        self.pth_file.save()

        if dist.name=='setuptools':
            # Ensure that setuptools itself never becomes unavailable!
            f = open(os.path.join(self.install_dir,'setuptools.pth'), 'w')
            f.write(dist.path+'\n')
            f.close()


    def unpack_progress(self, src, dst):
        # Progress filter for unpacking
        log.debug("Unpacking %s to %s", src, dst)
        return dst     # only unpack-and-compile skips files for dry run





    def unpack_and_compile(self, egg_path, destination):
        to_compile = []

        def pf(src,dst):
            if dst.endswith('.py'):
                to_compile.append(dst)
            self.unpack_progress(src,dst)
            return not self.dry_run and dst or None

        unpack_archive(egg_path, destination, pf)
        self.byte_compile(to_compile)


    def byte_compile(self, to_compile):
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














def extract_wininst_cfg(dist_filename):
    """Extract configuration data from a bdist_wininst .exe

    Returns a ConfigParser.RawConfigParser, or None
    """
    f = open(dist_filename,'rb')
    try:
        endrec = zipfile._EndRecData(f)
        if endrec is None:
            return None

        prepended = (endrec[9] - endrec[5]) - endrec[6]
        if prepended < 12:  # no wininst data here
            return None               
        f.seek(prepended-12)

        import struct, StringIO, ConfigParser
        tag, cfglen, bmlen = struct.unpack("<iii",f.read(12))
        if tag<>0x1234567A:
            return None     # not a valid tag

        f.seek(prepended-(12+cfglen+bmlen))
        cfg = ConfigParser.RawConfigParser({'version':'','target_version':''})
        try:
            cfg.readfp(StringIO.StringIO(f.read(cfglen)))
        except ConfigParser.Error:
            return None
        if not cfg.has_section('metadata') or not cfg.has_section('Setup'):
            return None
        return cfg              

    finally:
        f.close()








def get_exe_prefixes(exe_filename):
    """Get exe->egg path translations for a given .exe file"""

    prefixes = [
        ('PURELIB/', ''),
        ('PLATLIB/', ''),
        ('SCRIPTS/', 'EGG-INFO/scripts/')
    ]
    z = zipfile.ZipFile(exe_filename)
    try:
        for info in z.infolist():
            name = info.filename
            if not name.endswith('.pth'):
                continue
            parts = name.split('/')
            if len(parts)<>2:
                continue
            if parts[0] in ('PURELIB','PLATLIB'):
                pth = z.read(name).strip()
                prefixes[0] = ('PURELIB/%s/' % pth), ''
                prefixes[1] = ('PLATLIB/%s/' % pth), ''
                break
    finally:
        z.close()

    return prefixes















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






























