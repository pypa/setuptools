#!python
"""\
Easy Install
------------

A tool for doing automatic download/extract/build of distutils-based Python
packages.  For detailed documentation, see the accompanying EasyInstall.txt
file, or visit the `EasyInstall home page`__.

__ http://peak.telecommunity.com/DevCenter/EasyInstall
"""
import sys, os.path, zipimport, shutil, tempfile, zipfile, re, stat
from glob import glob
from setuptools import Command
from setuptools.sandbox import run_setup
from distutils import log, dir_util
from distutils.sysconfig import get_python_lib
from distutils.errors import DistutilsArgError, DistutilsOptionError, \
    DistutilsError
from setuptools.archive_util import unpack_archive
from setuptools.package_index import PackageIndex, parse_bdist_wininst
from setuptools.package_index import URL_SCHEME
from setuptools.command import bdist_egg, egg_info
from pkg_resources import *
sys_executable = os.path.normpath(sys.executable)

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
        ("delete-conflicting", "D", "delete old packages that get in the way"),
        ("ignore-conflicts-at-my-risk", None,
            "install even if old packages are in the way, even though it "
            "most likely means the new package won't work."),
        ("build-directory=", "b",
            "download/extract/build in DIR; keep the results"),
        ('optimize=', 'O',
         "also compile with optimization: -O1 for \"python -O\", "
         "-O2 for \"python -OO\", and -O0 to disable [default: -O0]"),
        ('record=', None,
         "filename in which to record list of installed files"),
        ('always-unzip', 'Z', "don't install as a zipfile, no matter what"),
        ('site-dirs=','S',"list of directories where .pth files work"),
        ('editable', 'e', "Install specified packages in editable form"),
        ('no-deps', 'N', "don't install dependencies"),
        ('allow-hosts=', 'H', "pattern(s) that hostnames must match"),
    ]
    boolean_options = [
        'zip-ok', 'multi-version', 'exclude-scripts', 'upgrade', 'always-copy',
        'delete-conflicting', 'ignore-conflicts-at-my-risk', 'editable',
        'no-deps',
    ]
    negative_opt = {'always-unzip': 'zip-ok'}
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
        self.editable = self.no_deps = self.allow_hosts = None
        self.root = None

        # Options not specifiable via command line
        self.package_index = None
        self.pth_file = None
        self.delete_conflicting = None
        self.ignore_conflicts_at_my_risk = None
        self.site_dirs = None
        self.installed_projects = {}

        # Always read easy_install options, even if we are subclassed, or have
        # an independent instance created.  This ensures that defaults will
        # always come from the standard configuration file(s)' "easy_install"
        # section, even if this is a "develop" or "install" command, or some
        # other embedding.
        self._dry_run = None
        self.verbose = self.distribution.verbose
        self.distribution._set_command_options(
            self, self.distribution.get_option_dict('easy_install')
        )

    def delete_blockers(self, blockers):
        for filename in blockers:
            if os.path.exists(filename) or os.path.islink(filename):
                log.info("Deleting %s", filename)
                if not self.dry_run:
                    if os.path.isdir(filename) and not os.path.islink(filename):
                        rmtree(filename)
                    else:
                        os.unlink(filename)

    def finalize_options(self):
        self._expand('install_dir','script_dir','build_directory','site_dirs')
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
        normpath = map(normalize_path, sys.path)
        self.all_site_dirs = get_site_dirs()
        if self.site_dirs is not None:
            site_dirs = [
                os.path.expanduser(s.strip()) for s in self.site_dirs.split(',')
            ]
            for d in site_dirs:                           
                if not os.path.isdir(d):
                    log.warn("%s (in --site-dirs) does not exist", d)
                elif normalize_path(d) not in normpath:
                    raise DistutilsOptionError(
                        d+" (in --site-dirs) is not on sys.path"
                    )
                else:
                    self.all_site_dirs.append(normalize_path(d))
        instdir = normalize_path(self.install_dir or self.all_site_dirs[-1])
        if instdir in self.all_site_dirs:
            if self.pth_file is None:
                self.pth_file = PthDistributions(
                    os.path.join(instdir,'easy-install.pth')
                )

        elif self.multi_version is None:
            self.multi_version = True

        elif not self.multi_version:
            # explicit false set from Python code; raise an error
            raise DistutilsArgError(
                "Can't do single-version installs outside 'site-package' dirs"
            )

        self.install_dir = instdir
        self.index_url = self.index_url or "http://www.python.org/pypi"
        self.shadow_path = self.all_site_dirs[:]
        for path_item in self.install_dir, normalize_path(self.script_dir):
            if path_item not in self.shadow_path:
                self.shadow_path.insert(0, path_item)

        if self.allow_hosts is not None:
            hosts = [s.strip() for s in self.allow_hosts.split(',')]
        else:
            hosts = ['*']

        if self.package_index is None:
            self.package_index = self.create_index(
                self.index_url, search_path = self.shadow_path, hosts=hosts
            )
        self.local_index = Environment(self.shadow_path)

        if self.find_links is not None:
            if isinstance(self.find_links, basestring):
                self.find_links = self.find_links.split()
        else:
            self.find_links = []
        self.package_index.add_find_links(self.find_links)
        self.set_undefined_options('install_lib', ('optimize','optimize'))
        if not isinstance(self.optimize,int):
            try:
                self.optimize = int(self.optimize)
                if not (0 <= self.optimize <= 2): raise ValueError
            except ValueError:
                raise DistutilsOptionError("--optimize must be 0, 1, or 2")

        if self.delete_conflicting and self.ignore_conflicts_at_my_risk:
            raise DistutilsOptionError(
                "Can't use both --delete-conflicting and "
                "--ignore-conflicts-at-my-risk at the same time"
            )
        if self.editable and not self.build_directory:
            raise DistutilsArgError(
                "Must specify a build directory (-b) when using --editable"
            )

        if not self.args:
            raise DistutilsArgError(
                "No urls, filenames, or requirements specified (see --help)")

        self.outputs = []


    def run(self):
        if self.verbose<>self.distribution.verbose:
            log.set_verbosity(self.verbose)
        try:
            for spec in self.args:
                self.easy_install(spec, not self.no_deps)
            if self.record:
                outputs = self.outputs
                if self.root:               # strip any package prefix
                    root_len = len(self.root)
                    for counter in xrange(len(outputs)):
                        outputs[counter] = outputs[counter][root_len:]
                from distutils import file_util
                self.execute(
                    file_util.write_file, (self.record, outputs),
                    "writing list of installed files to '%s'" %
                    self.record
                )
        finally:
            log.set_verbosity(self.distribution.verbose)




    def install_egg_scripts(self, dist):
        """Write all the scripts for `dist`, unless scripts are excluded"""

        self.install_wrapper_scripts(dist)
        if self.exclude_scripts or not dist.metadata_isdir('scripts'):
            return

        for script_name in dist.metadata_listdir('scripts'):
            self.install_script(
                dist, script_name,
                dist.get_metadata('scripts/'+script_name).replace('\r','\n')
            )

    def add_output(self, path):
        if os.path.isdir(path):
            for base, dirs, files in os.walk(path):
                for filename in files:
                    self.outputs.append(os.path.join(base,filename))
        else:
            self.outputs.append(path)

    def not_editable(self, spec):
        if self.editable:
            raise DistutilsArgError(
                "Invalid argument %r: you can't use filenames or URLs "
                "with --editable (except via the --find-links option)."
                % (spec,)
            )

    def check_editable(self,spec):
        if not self.editable:
            return

        if os.path.exists(os.path.join(self.build_directory, spec.key)):
            raise DistutilsArgError(
                "%r already exists in %s; can't do a checkout there" %
                (spec.key, self.build_directory)
            )



    def easy_install(self, spec, deps=False):
        tmpdir = tempfile.mkdtemp(prefix="easy_install-")
        download = None

        try:
            if not isinstance(spec,Requirement):
                if URL_SCHEME(spec):
                    # It's a url, download it to tmpdir and process
                    self.not_editable(spec)
                    download = self.package_index.download(spec, tmpdir)
                    return self.install_item(None, download, tmpdir, deps, True)

                elif os.path.exists(spec):
                    # Existing file or directory, just process it directly
                    self.not_editable(spec)
                    return self.install_item(None, spec, tmpdir, deps, True)
                else:
                    spec = parse_requirement_arg(spec)

            self.check_editable(spec)
            dist = self.package_index.fetch_distribution(
                spec, tmpdir, self.upgrade, self.editable, not self.always_copy
            )

            if dist is None:
                msg = "Could not find suitable distribution for %r" % spec
                if self.always_copy:
                    msg+=" (--always-copy skips system and development eggs)"
                raise DistutilsError(msg)
            elif dist.precedence==DEVELOP_DIST:
                # .egg-info dists don't need installing, just process deps
                self.process_distribution(spec, dist, deps, "Using")                
                return dist
            else:
                return self.install_item(spec, dist.location, tmpdir, deps)

        finally:
            if os.path.exists(tmpdir):
                rmtree(tmpdir)


    def install_item(self, spec, download, tmpdir, deps, install_needed=False):

        # Installation is also needed if file in tmpdir or is not an egg
        install_needed = install_needed or os.path.dirname(download) == tmpdir
        install_needed = install_needed or not download.endswith('.egg')

        log.info("Processing %s", os.path.basename(download))

        if install_needed or self.always_copy:
            dists = self.install_eggs(spec, download, tmpdir)
            for dist in dists:
                self.process_distribution(spec, dist, deps)
        else:
            dists = [self.check_conflicts(self.egg_distribution(download))]
            self.process_distribution(spec, dists[0], deps, "Using")

        if spec is not None:
            for dist in dists:
                if dist in spec:
                    return dist





















    def process_distribution(self, requirement, dist, deps=True, *info):
        self.update_pth(dist)
        self.package_index.add(dist)
        self.local_index.add(dist)
        self.install_egg_scripts(dist)
        self.installed_projects[dist.key] = dist
        log.warn(self.installation_report(dist, *info))
        if not deps and not self.always_copy:
            return
        elif requirement is not None and dist.key != requirement.key:
            log.warn("Skipping dependencies for %s", dist)
            return  # XXX this is not the distribution we were looking for
        elif requirement is None or dist not in requirement:
            # if we wound up with a different version, resolve what we've got
            distreq = dist.as_requirement()
            requirement = requirement or distreq
            requirement = Requirement(
                distreq.project_name, distreq.specs, requirement.extras
            )

        log.info("Processing dependencies for %s", requirement)
        try:
            distros = WorkingSet([]).resolve(
                [requirement], self.local_index, self.easy_install
            )
        except DistributionNotFound, e:
            raise DistutilsError(
                "Could not find required distribution %s" % e.args
            )
        except VersionConflict, e:
            raise DistutilsError(
                "Installed distribution %s conflicts with requirement %s"
                % e.args
            )

        if self.always_copy:
            # Force all the relevant distros to be copied or activated
            for dist in distros:
                if dist.key not in self.installed_projects:
                    self.easy_install(dist.as_requirement())

    def should_unzip(self, dist):
        if self.zip_ok is not None:
            return not self.zip_ok
        if dist.has_metadata('not-zip-safe'):
            return True
        if not dist.has_metadata('zip-safe'):
            return True
        return False

    def maybe_move(self, spec, dist_filename, setup_base):
        dst = os.path.join(self.build_directory, spec.key)
        if os.path.exists(dst):
            log.warn(
               "%r already exists in %s; build directory %s will not be kept",
               spec.key, self.build_directory, setup_base
            )
            return setup_base
        if os.path.isdir(dist_filename):
            setup_base = dist_filename
        else:
            if os.path.dirname(dist_filename)==setup_base:
                os.unlink(dist_filename)   # get it out of the tmp dir
            contents = os.listdir(setup_base)
            if len(contents)==1:
                dist_filename = os.path.join(setup_base,contents[0])
                if os.path.isdir(dist_filename):
                    # if the only thing there is a directory, move it instead
                    setup_base = dist_filename
        ensure_directory(dst); shutil.move(setup_base, dst)
        return dst

    def install_wrapper_scripts(self, dist):
        if not self.exclude_scripts:
            for args in get_script_args(dist):
                self.write_script(*args)






    def install_script(self, dist, script_name, script_text, dev_path=None):
        """Generate a legacy script wrapper and install it"""
        spec = str(dist.as_requirement())

        if dev_path:
            script_text = get_script_header(script_text) + (
                "# EASY-INSTALL-DEV-SCRIPT: %(spec)r,%(script_name)r\n"
                "__requires__ = %(spec)r\n"
                "from pkg_resources import require; require(%(spec)r)\n"
                "del require\n"
                "__file__ = %(dev_path)r\n"
                "execfile(__file__)\n"
            ) % locals()
        else:
            script_text = get_script_header(script_text) + (
                "# EASY-INSTALL-SCRIPT: %(spec)r,%(script_name)r\n"
                "__requires__ = %(spec)r\n"
                "import pkg_resources\n"
                "pkg_resources.run_script(%(spec)r, %(script_name)r)\n"
            ) % locals()

        self.write_script(script_name, script_text)

    def write_script(self, script_name, contents, mode="t", blockers=()):
        """Write an executable file to the scripts directory"""
        self.delete_blockers(   # clean up old .py/.pyw w/o a script
            [os.path.join(self.script_dir,x) for x in blockers])
        log.info("Installing %s script to %s", script_name, self.script_dir)
        target = os.path.join(self.script_dir, script_name)
        self.add_output(target)

        if not self.dry_run:
            ensure_directory(target)
            f = open(target,"w"+mode)
            f.write(contents)
            f.close()
            try:
                os.chmod(target,0755)
            except (AttributeError, os.error):
                pass

    def install_eggs(self, spec, dist_filename, tmpdir):
        # .egg dirs or files are already built, so just return them
        if dist_filename.lower().endswith('.egg'):
            return [self.install_egg(dist_filename, tmpdir)]
        elif dist_filename.lower().endswith('.exe'):
            return [self.install_exe(dist_filename, tmpdir)]

        # Anything else, try to extract and build
        setup_base = tmpdir
        if os.path.isfile(dist_filename) and not dist_filename.endswith('.py'):
            unpack_archive(dist_filename, tmpdir, self.unpack_progress)
        elif os.path.isdir(dist_filename):
            setup_base = os.path.abspath(dist_filename)

        if (setup_base.startswith(tmpdir)   # something we downloaded
            and self.build_directory and spec is not None
        ):
            setup_base = self.maybe_move(spec, dist_filename, setup_base)

        # Find the setup.py file
        setup_script = os.path.join(setup_base, 'setup.py')

        if not os.path.exists(setup_script):
            setups = glob(os.path.join(setup_base, '*', 'setup.py'))
            if not setups:
                raise DistutilsError(
                    "Couldn't find a setup script in %s" % dist_filename
                )
            if len(setups)>1:
                raise DistutilsError(
                    "Multiple setup scripts in %s" % dist_filename
                )
            setup_script = setups[0]

        # Now run it, and return the result
        if self.editable:
            log.warn(self.report_editable(spec, setup_script))
            return []
        else:
            return self.build_and_install(setup_script, setup_base)

    def egg_distribution(self, egg_path):
        if os.path.isdir(egg_path):
            metadata = PathMetadata(egg_path,os.path.join(egg_path,'EGG-INFO'))
        else:
            metadata = EggMetadata(zipimport.zipimporter(egg_path))
        return Distribution.from_filename(egg_path,metadata=metadata)

    def install_egg(self, egg_path, tmpdir):
        destination = os.path.join(self.install_dir,os.path.basename(egg_path))
        destination = os.path.abspath(destination)
        if not self.dry_run:
            ensure_directory(destination)

        dist = self.egg_distribution(egg_path)
        self.check_conflicts(dist)
        if not samefile(egg_path, destination):
            if os.path.isdir(destination) and not os.path.islink(destination):
                dir_util.remove_tree(destination, dry_run=self.dry_run)
            elif os.path.exists(destination):
                self.execute(os.unlink,(destination,),"Removing "+destination)

            if os.path.isdir(egg_path):
                if egg_path.startswith(tmpdir):
                    f,m = shutil.move, "Moving"
                else:
                    f,m = shutil.copytree, "Copying"
            elif self.should_unzip(dist):
                self.mkpath(destination)
                f,m = self.unpack_and_compile, "Extracting"
            elif egg_path.startswith(tmpdir):
                f,m = shutil.move, "Moving"
            else:
                f,m = shutil.copy2, "Copying"

            self.execute(f, (egg_path, destination),
                (m+" %s to %s") %
                (os.path.basename(egg_path),os.path.dirname(destination)))

        self.add_output(destination)
        return self.egg_distribution(destination)

    def install_exe(self, dist_filename, tmpdir):
        # See if it's valid, get data
        cfg = extract_wininst_cfg(dist_filename)
        if cfg is None:
            raise DistutilsError(
                "%s is not a valid distutils Windows .exe" % dist_filename
            )
        # Create a dummy distribution object until we build the real distro
        dist = Distribution(None,
            project_name=cfg.get('metadata','name'),
            version=cfg.get('metadata','version'), platform="win32"
        )

        # Convert the .exe to an unpacked egg
        egg_path = dist.location = os.path.join(tmpdir, dist.egg_name()+'.egg')
        egg_tmp  = egg_path+'.tmp'
        egg_info = os.path.join(egg_tmp, 'EGG-INFO') 
        pkg_inf = os.path.join(egg_info, 'PKG-INFO')
        ensure_directory(pkg_inf)   # make sure EGG-INFO dir exists
        dist._provider = PathMetadata(egg_tmp, egg_info)    # XXX
        self.exe_to_egg(dist_filename, egg_tmp)

        # Write EGG-INFO/PKG-INFO
        if not os.path.exists(pkg_inf):
            f = open(pkg_inf,'w')
            f.write('Metadata-Version: 1.0\n')
            for k,v in cfg.items('metadata'):
                if k<>'target_version':
                    f.write('%s: %s\n' % (k.replace('_','-').title(), v))
            f.close()
        script_dir = os.path.join(egg_info,'scripts')
        self.delete_blockers(   # delete entry-point scripts to avoid duping
            [os.path.join(script_dir,args[0]) for args in get_script_args(dist)]
        )       
        # Build .egg file from tmpdir
        bdist_egg.make_zipfile(
            egg_path, egg_tmp, verbose=self.verbose, dry_run=self.dry_run
        )
        # install the .egg
        return self.install_egg(egg_path, tmpdir)

    def exe_to_egg(self, dist_filename, egg_tmp):
        """Extract a bdist_wininst to the directories an egg would use"""
        # Check for .pth file and set up prefix translations
        prefixes = get_exe_prefixes(dist_filename)
        to_compile = []
        native_libs = []
        top_level = {}

        def process(src,dst):
            for old,new in prefixes:
                if src.startswith(old):
                    src = new+src[len(old):]
                    parts = src.split('/')
                    dst = os.path.join(egg_tmp, *parts)
                    dl = dst.lower()
                    if dl.endswith('.pyd') or dl.endswith('.dll'):
                        top_level[os.path.splitext(parts[0])[0]] = 1
                        native_libs.append(src)
                    elif dl.endswith('.py') and old!='SCRIPTS/':
                        top_level[os.path.splitext(parts[0])[0]] = 1
                        to_compile.append(dst)
                    return dst
            if not src.endswith('.pth'):
                log.warn("WARNING: can't process %s", src)
            return None

        # extract, tracking .pyd/.dll->native_libs and .py -> to_compile
        unpack_archive(dist_filename, egg_tmp, process)
        stubs = []
        for res in native_libs:
            if res.lower().endswith('.pyd'):    # create stubs for .pyd's
                parts = res.split('/')
                resource, parts[-1] = parts[-1], parts[-1][:-1]
                pyfile = os.path.join(egg_tmp, *parts)
                to_compile.append(pyfile); stubs.append(pyfile)
                bdist_egg.write_stub(resource, pyfile)

        self.byte_compile(to_compile)   # compile .py's
        bdist_egg.write_safety_flag(os.path.join(egg_tmp,'EGG-INFO'),
            bdist_egg.analyze_egg(egg_tmp, stubs))  # write zip-safety flag

        for name in 'top_level','native_libs':
            if locals()[name]:
                txt = os.path.join(egg_tmp, 'EGG-INFO', name+'.txt')
                if not os.path.exists(txt):
                    open(txt,'w').write('\n'.join(locals()[name])+'\n')

    def check_conflicts(self, dist):
        """Verify that there are no conflicting "old-style" packages"""

        from imp import find_module, get_suffixes
        from glob import glob

        blockers = []
        names = dict.fromkeys(dist._get_metadata('top_level.txt')) # XXX private attr

        exts = {'.pyc':1, '.pyo':1}     # get_suffixes() might leave one out
        for ext,mode,typ in get_suffixes():
            exts[ext] = 1

        for path,files in expand_paths([self.install_dir]+self.all_site_dirs):
            for filename in files:
                base,ext = os.path.splitext(filename)
                if base in names:
                    if not ext:
                        # no extension, check for package
                        try:
                            f, filename, descr = find_module(base, [path])
                        except ImportError:
                            continue
                        else:
                            if f: f.close()
                            if filename not in blockers:
                                blockers.append(filename)
                    elif ext in exts:
                        blockers.append(os.path.join(path,filename))

        if blockers:
            self.found_conflicts(dist, blockers)

        return dist

    def found_conflicts(self, dist, blockers):
        if self.delete_conflicting:
            log.warn("Attempting to delete conflicting packages:")
            return self.delete_blockers(blockers)

        msg = """\
-------------------------------------------------------------------------
CONFLICT WARNING:

The following modules or packages have the same names as modules or
packages being installed, and will be *before* the installed packages in
Python's search path.  You MUST remove all of the relevant files and
directories before you will be able to use the package(s) you are
installing:

   %s

""" % '\n   '.join(blockers)

        if self.ignore_conflicts_at_my_risk:
            msg += """\
(Note: you can run EasyInstall on '%s' with the
--delete-conflicting option to attempt deletion of the above files
and/or directories.)
""" % dist.project_name
        else:
            msg += """\
Note: you can attempt this installation again with EasyInstall, and use
either the --delete-conflicting (-D) option or the
--ignore-conflicts-at-my-risk option, to either delete the above files
and directories, or to ignore the conflicts, respectively.  Note that if
you ignore the conflicts, the installed package(s) may not work.
"""
        msg += """\
-------------------------------------------------------------------------
"""
        sys.stderr.write(msg)
        sys.stderr.flush()
        if not self.ignore_conflicts_at_my_risk:
            raise DistutilsError("Installation aborted due to conflicts")

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
        if self.install_dir not in map(normalize_path,sys.path):
            msg += """

Note also that the installation directory must be on sys.path at runtime for
this to work.  (e.g. by being the application's script directory, by being on
PYTHONPATH, or by being added to sys.path by your code.)
"""
        eggloc = dist.location
        name = dist.project_name
        version = dist.version
        return msg % locals()

    def report_editable(self, spec, setup_script):
        dirname = os.path.dirname(setup_script)
        python = sys.executable
        return """\nExtracted editable version of %(spec)s to %(dirname)s

If it uses setuptools in its setup script, you can activate it in
"development" mode by going to that directory and running::

    %(python)s setup.py develop

See the setuptools documentation for the "develop" command for more info.
""" % locals()

    def run_setup(self, setup_script, setup_base, args):
        sys.modules.setdefault('distutils.command.bdist_egg', bdist_egg)
        sys.modules.setdefault('distutils.command.egg_info', egg_info)

        args = list(args)
        if self.verbose>2:
            v = 'v' * (self.verbose - 1)
            args.insert(0,'-'+v)
        elif self.verbose<2:
            args.insert(0,'-q')
        if self.dry_run:
            args.insert(0,'-n')
        log.info(
            "Running %s %s", setup_script[len(setup_base)+1:], ' '.join(args)
        )
        try:
            run_setup(setup_script, args)
        except SystemExit, v:
            raise DistutilsError("Setup script exited with %s" % (v.args[0],))

    def build_and_install(self, setup_script, setup_base):
        args = ['bdist_egg', '--dist-dir']
        dist_dir = tempfile.mkdtemp(
            prefix='egg-dist-tmp-', dir=os.path.dirname(setup_script)
        )
        try:
            args.append(dist_dir)
            self.run_setup(setup_script, setup_base, args)
            all_eggs = Environment([dist_dir])
            eggs = []
            for key in all_eggs:
                for dist in all_eggs[key]:
                    eggs.append(self.install_egg(dist.location, setup_base))
            if not eggs and not self.dry_run:
                log.warn("No eggs found in %s (setup script problem?)",
                    dist_dir)
            return eggs
        finally:
            rmtree(dist_dir)
            log.set_verbosity(self.verbose) # restore our log verbosity

    def update_pth(self,dist):
        if self.pth_file is None:
            return

        for d in self.pth_file[dist.key]:    # drop old entries
            if self.multi_version or d.location != dist.location:
                log.info("Removing %s from easy-install.pth file", d)
                self.pth_file.remove(d)
                if d.location in self.shadow_path:
                    self.shadow_path.remove(d.location)

        if not self.multi_version:
            if dist.location in self.pth_file.paths:
                log.info(
                    "%s is already the active version in easy-install.pth",
                    dist
                )
            else:
                log.info("Adding %s to easy-install.pth file", dist)
                self.pth_file.add(dist) # add new entry
                if dist.location not in self.shadow_path:
                    self.shadow_path.append(dist.location)

        if not self.dry_run:

            self.pth_file.save()

            if dist.key=='setuptools':
                # Ensure that setuptools itself never becomes unavailable!
                # XXX should this check for latest version?
                filename = os.path.join(self.install_dir,'setuptools.pth')
                if os.path.islink(filename): os.unlink(filename)
                f = open(filename, 'wt')
                f.write(dist.location+'\n')
                f.close()

    def unpack_progress(self, src, dst):
        # Progress filter for unpacking
        log.debug("Unpacking %s to %s", src, dst)
        return dst     # only unpack-and-compile skips files for dry run

    def unpack_and_compile(self, egg_path, destination):
        to_compile = []

        def pf(src,dst):
            if dst.endswith('.py') and not src.startswith('EGG-INFO/'):
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

    def _expand(self, *attrs):
        config_vars = self.get_finalized_command('install').config_vars
        from distutils.util import subst_vars
        for attr in attrs:
            val = getattr(self, attr)
            if val is not None:
                if os.name == 'posix':
                    val = os.path.expanduser(val)
                val = subst_vars(val, config_vars)
                setattr(self, attr, val)



def get_site_dirs():
    # return a list of 'site' dirs, based on 'site' module's code to do this
    sitedirs = []
    prefixes = [sys.prefix]
    if sys.exec_prefix != sys.prefix:
        prefixes.append(sys.exec_prefix)
    for prefix in prefixes:
        if prefix:
            if sys.platform in ('os2emx', 'riscos'):
                sitedirs.append(os.path.join(prefix, "Lib", "site-packages"))
            elif os.sep == '/':
                sitedirs.extend([os.path.join(prefix,
                                         "lib",
                                         "python" + sys.version[:3],
                                         "site-packages"),
                            os.path.join(prefix, "lib", "site-python")])
            else:
                sitedirs.extend(
                    [prefix, os.path.join(prefix, "lib", "site-packages")]
                )
            if sys.platform == 'darwin':
                # for framework builds *only* we add the standard Apple
                # locations. Currently only per-user, but /Library and
                # /Network/Library could be added too
                if 'Python.framework' in prefix:
                    home = os.environ.get('HOME')
                    if home:
                        sitedirs.append(
                            os.path.join(home,
                                         'Library',
                                         'Python',
                                         sys.version[:3],
                                         'site-packages'))
    for plat_specific in (0,1):
        site_lib = get_python_lib(plat_specific)
        if site_lib not in sitedirs: sitedirs.append(site_lib)        

    sitedirs = filter(os.path.isdir, sitedirs)
    sitedirs = map(normalize_path, sitedirs)
    return sitedirs     # ensure at least one

def expand_paths(inputs):
    """Yield sys.path directories that might contain "old-style" packages"""

    seen = {}

    for dirname in inputs:
        dirname = normalize_path(dirname)
        if dirname in seen:
            continue

        seen[dirname] = 1
        if not os.path.isdir(dirname):
            continue

        files = os.listdir(dirname)
        yield dirname, files

        for name in files:
            if not name.endswith('.pth'):
                # We only care about the .pth files
                continue
            if name in ('easy-install.pth','setuptools.pth'):
                # Ignore .pth files that we control
                continue

            # Read the .pth file
            f = open(os.path.join(dirname,name))
            lines = list(yield_lines(f))
            f.close()

            # Yield existing non-dupe, non-import directory lines from it
            for line in lines:
                if not line.startswith("import"):
                    line = normalize_path(line.rstrip())
                    if line not in seen:
                        seen[line] = 1
                        if not os.path.isdir(line):
                            continue
                        yield line, os.listdir(line)


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
        if tag not in (0x1234567A, 0x1234567B):
            return None     # not a valid tag

        f.seek(prepended-(12+cfglen+bmlen))
        cfg = ConfigParser.RawConfigParser({'version':'','target_version':''})
        try:
            cfg.readfp(StringIO.StringIO(f.read(cfglen).split(chr(0),1)[0]))
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
            parts = name.split('/')
            if len(parts)==3 and parts[2]=='PKG-INFO':
                if parts[1].endswith('.egg-info'):
                    prefixes.insert(0,('/'.join(parts[:2]), 'EGG-INFO/'))
                    break
            if len(parts)<>2 or not name.endswith('.pth'):
                continue
            if parts[0] in ('PURELIB','PLATLIB'):
                pth = z.read(name).strip()
                prefixes[0] = ('PURELIB/%s/' % pth), ''
                prefixes[1] = ('PLATLIB/%s/' % pth), ''
                break
    finally:
        z.close()

    return prefixes


def parse_requirement_arg(spec):
    try:
        return Requirement.parse(spec)
    except ValueError:
        raise DistutilsError(
            "Not a URL, existing file, or requirement spec: %r" % (spec,)
        )




class PthDistributions(Environment):
    """A .pth file with Distribution paths in it"""

    dirty = False

    def __init__(self, filename):
        self.filename = filename; self._load()
        Environment.__init__(self, [], None, None)
        for path in yield_lines(self.paths):
            map(self.add, find_distributions(path, True))

    def _load(self):
        self.paths = []
        seen = {}
        if os.path.isfile(self.filename):
            for line in open(self.filename,'rt'):
                path = line.rstrip()
                self.paths.append(path)
                if not path.strip() or path.strip().startswith('#'):
                    continue
                # skip non-existent paths, in case somebody deleted a package
                # manually, and duplicate paths as well
                path = self.paths[-1] = normalize_path(path)
                if not os.path.exists(path) or path in seen:
                    self.paths.pop()    # skip it
                    self.dirty = True   # we cleaned up, so we're dirty now :)
                    continue
                seen[path] = 1

        while self.paths and not self.paths[-1].strip(): self.paths.pop()

    def save(self):
        """Write changed .pth file back to disk"""
        if self.dirty:
            log.debug("Saving %s", self.filename)
            data = '\n'.join(self.paths+[''])
            if os.path.islink(self.filename):
                os.unlink(self.filename)
            f = open(self.filename,'wt'); f.write(data); f.close()
            self.dirty = False

    def add(self,dist):
        """Add `dist` to the distribution map"""
        if dist.location not in self.paths:
            self.paths.append(dist.location); self.dirty = True
        Environment.add(self,dist)

    def remove(self,dist):
        """Remove `dist` from the distribution map"""
        while dist.location in self.paths:
            self.paths.remove(dist.location); self.dirty = True
        Environment.remove(self,dist)


def get_script_header(script_text, executable=sys_executable):
    """Create a #! line, getting options (if any) from script_text"""
    from distutils.command.build_scripts import first_line_re
    first, rest = (script_text+'\n').split('\n',1)
    match = first_line_re.match(first)
    options = ''
    if match:
        script_text = rest
        options = match.group(1) or ''
        if options:
            options = ' '+options
    return "#!%(executable)s%(options)s\n" % locals()

def main(argv=None, **kw):
    from setuptools import setup
    if argv is None:
        argv = sys.argv[1:]
    setup(script_args = ['-q','easy_install', '-v']+argv, **kw)


def auto_chmod(func, arg, exc):
    if func is os.remove and os.name=='nt':
        os.chmod(arg, stat.S_IWRITE)
        return func(arg)
    exc = sys.exc_info()
    raise exc[0], (exc[1][0], exc[1][1] + (" %s %s" % (func,arg)))


def get_script_args(dist, executable=sys_executable):
    """Yield write_script() argument tuples for a distribution's entrypoints"""
    spec = str(dist.as_requirement())
    header = get_script_header("", executable)
    for group in 'console_scripts', 'gui_scripts':
        for name,ep in dist.get_entry_map(group).items():
            script_text = (
                "# EASY-INSTALL-ENTRY-SCRIPT: %(spec)r,%(group)r,%(name)r\n"
                "__requires__ = %(spec)r\n"
                "import sys\n"
                "from pkg_resources import load_entry_point\n"
                "\n"
                "sys.exit(\n"
                "   load_entry_point(%(spec)r, %(group)r, %(name)r)()\n"
                ")\n"
            ) % locals()
            if sys.platform=='win32':
                # On Windows, add a .py extension and an .exe launcher
                if group=='gui_scripts':
                    ext, launcher = '-script.pyw', 'gui.exe'
                    old = ['.pyw']
                    new_header = re.sub('(?i)python.exe','pythonw.exe',header)
                else:
                    ext, launcher = '-script.py', 'cli.exe'
                    old = ['.py','.pyc','.pyo']
                    new_header = re.sub('(?i)pythonw.exe','pythonw.exe',header)

                if os.path.exists(new_header[2:-1]):
                    hdr = new_header
                else:
                    hdr = header
                yield (name+ext, hdr+script_text, 't', [name+x for x in old])
                yield (
                    name+'.exe', resource_string('setuptools', launcher),
                    'b' # write in binary mode
                )
            else:
                # On other platforms, we assume the right thing to do is to
                # just write the stub with no extension.
                yield (name, header+script_text)

def rmtree(path, ignore_errors=False, onerror=auto_chmod):
    """Recursively delete a directory tree.

    This code is taken from the Python 2.4 version of 'shutil', because
    the 2.3 version doesn't really work right.
    """
    if ignore_errors:
        def onerror(*args):
            pass
    elif onerror is None:
        def onerror(*args):
            raise
    names = []
    try:
        names = os.listdir(path)
    except os.error, err:
        onerror(os.listdir, path, sys.exc_info())
    for name in names:
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            rmtree(fullname, ignore_errors, onerror)
        else:
            try:
                os.remove(fullname)
            except os.error, err:
                onerror(os.remove, fullname, sys.exc_info())
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path, sys.exc_info())







