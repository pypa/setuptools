"""setuptools.command.bdist_egg

Build .egg distributions"""

# This module should be kept compatible with Python 2.3

import os
from distutils.core import Command
from distutils.util import get_platform
from distutils.dir_util import create_tree, remove_tree, ensure_relative,mkpath
from distutils.sysconfig import get_python_version
from distutils.errors import *
from distutils import log

class bdist_egg(Command):

    description = "create an \"egg\" distribution"

    user_options = [('egg-info=', 'e',
                     "directory containing EGG-INFO for the distribution "
                     "(default: EGG-INFO.in)"),
                    ('bdist-dir=', 'd',
                     "temporary directory for creating the distribution"),
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
                    ('relative', None,
                     "build the archive using relative paths"
                     "(default: false)"),
                   ]

    boolean_options = ['keep-temp', 'skip-build', 'relative']


    def initialize_options (self):
        self.egg_info = None
        self.bdist_dir = None
        self.plat_name = None
        self.keep_temp = 0
        self.dist_dir = None
        self.skip_build = 0
        self.relative = 0
        
    # initialize_options()


    def finalize_options (self):

        if self.egg_info is None and os.path.isdir('EGG-INFO.in'):
            self.egg_info = 'EGG-INFO.in'

        elif self.egg_info:
            self.ensure_dirname('egg_info')

        if self.bdist_dir is None:
            bdist_base = self.get_finalized_command('bdist').bdist_base
            self.bdist_dir = os.path.join(bdist_base, 'egg')

        self.set_undefined_options('bdist',
                                   ('dist_dir', 'dist_dir'),
                                   ('plat_name', 'plat_name'))

    # finalize_options()

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

        
    def run (self):

        if not self.skip_build:
            self.run_command('build')

        install = self.reinitialize_command('install_lib', reinit_subcommands=1)
        install.install_dir = self.bdist_dir
        install.skip_build = self.skip_build
        install.warn_dir = 0

        ext_outputs = \
            install._mutate_outputs(self.distribution.has_ext_modules(),
                                    'build_ext', 'build_lib',
                                    '')
        log.info("installing to %s" % self.bdist_dir)
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
            
        # And make an archive relative to the root of the
        # pseudo-installation tree.
        archive_basename = "%s-py%s" % (self.distribution.get_fullname(),
                                      get_python_version())

        if ext_outputs:
            archive_basename += "-" + self.plat_name

        # OS/2 objects to any ":" characters in a filename (such as when
        # a timestamp is used in a version) so change them to hyphens.
        if os.name == "os2":
            archive_basename = archive_basename.replace(":", "-")

        pseudoinstall_root = os.path.join(self.dist_dir, archive_basename)
        archive_root = self.bdist_dir

        # Make the EGG-INFO directory
        log.info("creating EGG-INFO directory")
        egg_info = os.path.join(archive_root,'EGG-INFO')
        self.mkpath(egg_info)

        if self.egg_info:
            for filename in os.listdir(self.egg_info):
                path = os.path.join(self.egg_info,filename)
                if os.path.isfile(path):
                    self.copy_file(path,os.path.join(egg_info,filename))

        log.info("writing EGG-INFO/PKG-INFO")
        if not self.dry_run:
            self.distribution.metadata.write_pkg_info(egg_info)

        if ext_outputs:
            log.info("writing EGG-INFO/native_libs.txt")
            if not self.dry_run:
                libs_file = open(
                    os.path.join(egg_info,"native_libs.txt"),'wt')
                libs_file.write('\n'.join(ext_outputs))
                libs_file.write('\n')
                libs_file.close()

        # Make the archive
        make_zipfile(pseudoinstall_root+'.egg',
                          archive_root, verbose=self.verbose,
                          dry_run=self.dry_run)

        if not self.keep_temp:
            remove_tree(self.bdist_dir, dry_run=self.dry_run)

    # run()

# class bdist_egg



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

# make_zipfile ()

