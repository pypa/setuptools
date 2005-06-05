"""setuptools.command.bdist_egg

Build .egg distributions"""

# This module should be kept compatible with Python 2.3
import os
from distutils.core import Command
from distutils.util import get_platform
from distutils.dir_util import create_tree, remove_tree, ensure_relative,mkpath
from distutils.sysconfig import get_python_version, get_python_lib
from distutils.errors import *
from distutils import log
from pkg_resources import parse_requirements, get_platform, safe_name, safe_version

class bdist_egg(Command):
    description = "create an \"egg\" distribution"
    user_options = [
        ('egg-base=', 'e', "directory containing .egg-info directories"
                           " (default: top of the source tree)"),
        ('bdist-dir=', 'd',
            "temporary directory for creating the distribution"),
        ('tag-svn-revision', None,
            "Add subversion revision ID to version number"),
        ('tag-date', None, "Add date stamp (e.g. 20050528) to version number"),
        ('tag-build=', None, "Specify explicit tag to add to version number"),
        ('plat-name=', 'p',
                     "platform name to embed in generated filenames "
                     "(default: %s)" % get_platform()),
        ('keep-temp', 'k',
                     "keep the pseudo-installation tree around after " +
                     "creating the distribution archive"),
        ('dist-dir=', 'd',
                     "directory to put final built distributions in"),
        ('skip-build', None,
                     "skip rebuilding everything (for testing/debugging)"),
    ]

    boolean_options = [
        'keep-temp', 'skip-build', 'relative','tag-date','tag-svn-revision'
    ]

    def initialize_options (self):
        self.egg_name = None
        self.egg_version = None
        self.egg_base = None
        self.egg_info = None
        self.bdist_dir = None
        self.plat_name = None
        self.keep_temp = 0
        self.dist_dir = None
        self.skip_build = 0
        self.tag_build = None
        self.tag_svn_revision = 0
        self.tag_date = 0

    def finalize_options (self):
        self.egg_name = safe_name(self.distribution.get_name())
        self.egg_version = self.tagged_version()
        try:
            list(
                parse_requirements('%s==%s' % (self.egg_name,self.egg_version))
            )
        except ValueError:
            raise DistutilsOptionError(
                "Invalid distribution name or version syntax: %s-%s" %
                (self.egg_name,self.egg_version)
            )
        if self.egg_base is None:
            dirs = self.distribution.package_dir
            self.egg_base = (dirs or {}).get('','.')

        self.ensure_dirname('egg_base')
        self.egg_info = os.path.join(
            self.egg_base, self.egg_name+'.egg-info'
        )
        if self.bdist_dir is None:
            bdist_base = self.get_finalized_command('bdist').bdist_base
            self.bdist_dir = os.path.join(bdist_base, 'egg')
        if self.plat_name is None:
            self.plat_name = get_platform()
        self.set_undefined_options('bdist',('dist_dir', 'dist_dir'))

    def write_stub(self, resource, pyfile):
        f = open(pyfile,'w')
        f.write('\n'.join([
            "def __bootstrap__():",
            "   global __bootstrap__, __loader__, __file__",
            "   import sys, pkg_resources, imp",
            "   __file__ = pkg_resources.resource_filename(__name__,%r)"
                % resource,
            "   del __bootstrap__, __loader__",
            "   imp.load_dynamic(__name__,__file__)",
            "__bootstrap__()",
            "" # terminal \n
        ]))
        f.close()

    def do_install_data(self):
        self.get_finalized_command('install').install_lib = self.bdist_dir
        site_packages = os.path.normcase(os.path.realpath(get_python_lib()))
        old, self.distribution.data_files = self.distribution.data_files,[]
        for item in old:
            if isinstance(item,tuple) and len(item)==2:
                if os.path.isabs(item[0]):
                    realpath = os.path.realpath(item[0])
                    normalized = os.path.normcase(realpath)
                    if normalized==site_packages or normalized.startswith(
                        site_packages+os.sep
                    ):
                        item = realpath[len(site_packages)+1:], item[1]
                    # XXX else: raise ???
            self.distribution.data_files.append(item)
        try:
            install = self.reinitialize_command('install_data')
            # kludge for setups that use a 3-tuple inst_data
            install.install_dir = install.install_base = \
                install.install_data = install.install_lib = self.bdist_dir
            install.force = 0; install.root = None
            log.info("installing package data to %s" % self.bdist_dir)
            self.run_command('install_data')
        finally:
            self.distribution.data_files = old

    def run(self):
        if not self.skip_build:
            self.run_command('build')

        # We run install_lib before install_data, because some data hacks
        # pull their data path from the install_lib command.
        install = self.reinitialize_command('install_lib', reinit_subcommands=1)
        install.install_dir = self.bdist_dir
        install.skip_build = self.skip_build
        install.warn_dir = 0

        ext_outputs = \
            install._mutate_outputs(self.distribution.has_ext_modules(),
                                    'build_ext', 'build_lib',
                                    '')
        log.info("installing library code to %s" % self.bdist_dir)
        self.run_command('install_lib')

        to_compile = []
        for ext_name in ext_outputs:
            filename,ext = os.path.splitext(ext_name)
            pyfile = os.path.join(self.bdist_dir, filename + '.py')
            log.info("creating stub loader for %s" % ext_name)
            if not self.dry_run:
                self.write_stub(os.path.basename(ext_name), pyfile)
            to_compile.append(pyfile)

        if to_compile:
            install.byte_compile(to_compile)

        if self.distribution.data_files:
            self.do_install_data()

        # And make an archive relative to the root of the
        # pseudo-installation tree.
        archive_basename = "%s-%s-py%s" % ( self.egg_name.replace('-','_'),
            self.egg_version.replace('-','_'), get_python_version())
        if ext_outputs:
            archive_basename += "-" + self.plat_name
            ext_outputs = [out.replace(os.sep,'/') for out in ext_outputs]

        # OS/2 objects to any ":" characters in a filename (such as when
        # a timestamp is used in a version) so change them to underscores.
        if os.name == "os2":
            archive_basename = archive_basename.replace(":", "_")

        pseudoinstall_root = os.path.join(self.dist_dir, archive_basename)
        archive_root = self.bdist_dir

        # Make the EGG-INFO directory
        egg_info = os.path.join(archive_root,'EGG-INFO')
        self.mkpath(egg_info)
        self.mkpath(self.egg_info)
        log.info("writing %s" % os.path.join(self.egg_info,'PKG-INFO'))
        if not self.dry_run:
            metadata = self.distribution.metadata
            metadata.version, oldver = self.egg_version, metadata.version
            metadata.name, oldname   = self.egg_name, metadata.name
            try:
                metadata.write_pkg_info(self.egg_info)
            finally:
                metadata.name, metadata.version = oldname, oldver

        native_libs = os.path.join(self.egg_info,"native_libs.txt")
        if ext_outputs:
            log.info("writing %s" % native_libs)
            if not self.dry_run:
                libs_file = open(native_libs, 'wt')
                libs_file.write('\n'.join(ext_outputs))
                libs_file.write('\n')
                libs_file.close()
        elif os.path.isfile(native_libs):
            log.info("removing %s" % native_libs)
            if not self.dry_run:
                os.unlink(native_libs)

        if self.egg_info:
            for filename in os.listdir(self.egg_info):
                path = os.path.join(self.egg_info,filename)
                if os.path.isfile(path):
                    self.copy_file(path,os.path.join(egg_info,filename))

        # Make the archive
        make_zipfile(pseudoinstall_root+'.egg',
                          archive_root, verbose=self.verbose,
                          dry_run=self.dry_run)

        if not self.keep_temp:
            remove_tree(self.bdist_dir, dry_run=self.dry_run)

    def tagged_version(self):
        version = self.distribution.get_version()
        if self.tag_build:
            version+='-'+self.tag_build

        if self.tag_svn_revision and os.path.exists('.svn'):
            version += '-%s' % self.get_svn_revision()

        if self.tag_date:
            import time
            version += time.strftime("-%Y%m%d")

        return safe_version(version)

    def get_svn_revision(self):
        stdin, stdout = os.popen4("svn info"); stdin.close()
        result = stdout.read(); stdout.close()
        import re
        match = re.search(r'Last Changed Rev: (\d+)', result)
        if not match:
            raise RuntimeError("svn info error: %s" % result.strip())
        return match.group(1)











def make_zipfile (zip_filename, base_dir, verbose=0, dry_run=0):
    """Create a zip file from all the files under 'base_dir'.  The output
    zip file will be named 'base_dir' + ".zip".  Uses either the "zipfile"
    Python module (if available) or the InfoZIP "zip" utility (if installed
    and found on the default search path).  If neither tool is available,
    raises DistutilsExecError.  Returns the name of the output zip file.
    """
    import zipfile
    mkpath(os.path.dirname(zip_filename), dry_run=dry_run)

    # If zipfile module is not available, try spawning an external
    # 'zip' command.
    log.info("creating '%s' and adding '%s' to it",
             zip_filename, base_dir)

    def visit (z, dirname, names):
        for name in names:
            path = os.path.normpath(os.path.join(dirname, name))
            if os.path.isfile(path):
                p = path[len(base_dir)+1:]
                z.write(path, p)
                log.info("adding '%s'" % p)

    if not dry_run:
        z = zipfile.ZipFile(zip_filename, "w",
                            compression=zipfile.ZIP_DEFLATED)
        os.path.walk(base_dir, visit, z)
        z.close()

    return zip_filename











