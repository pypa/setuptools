"""setuptools.command.egg_info

Create a distribution's .egg-info directory and contents"""

# This module should be kept compatible with Python 2.3
import os
from setuptools import Command
from distutils.errors import *
from distutils import log
from pkg_resources import parse_requirements, safe_name, \
    safe_version, yield_lines


class egg_info(Command):

    description = "create a distribution's .egg-info directory"

    user_options = [
        ('egg-base=', 'e', "directory containing .egg-info directories"
                           " (default: top of the source tree)"),
        ('tag-svn-revision', 'r',
            "Add subversion revision ID to version number"),
        ('tag-date', 'd', "Add date stamp (e.g. 20050528) to version number"),
        ('tag-build=', 'b', "Specify explicit tag to add to version number"),
    ]

    boolean_options = ['tag-date','tag-svn-revision']


    def initialize_options (self):
        self.egg_name = None
        self.egg_version = None
        self.egg_base = None
        self.egg_info = None
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
            self.egg_base = (dirs or {}).get('',os.curdir)

        self.ensure_dirname('egg_base')
        self.egg_info = os.path.join(self.egg_base, self.egg_name+'.egg-info')

        # Set package version and name for the benefit of dumber commands
        # (e.g. sdist, bdist_wininst, etc.)  We escape '-' so filenames will
        # be more machine-parseable.
        #
        metadata = self.distribution.metadata
        metadata.version = self.egg_version.replace('-','_')
        metadata.name    = self.egg_name.replace('-','_')













    def run(self):
        # Make the .egg-info directory, then write PKG-INFO and requires.txt
        self.mkpath(self.egg_info)

        log.info("writing %s" % os.path.join(self.egg_info,'PKG-INFO'))       
        if not self.dry_run:
            metadata = self.distribution.metadata
            metadata.version, oldver = self.egg_version, metadata.version
            metadata.name, oldname   = self.egg_name, metadata.name
            try:
                # write unescaped data to PKG-INFO, so older pkg_resources
                # can still parse it
                metadata.write_pkg_info(self.egg_info)
            finally:
                metadata.name, metadata.version = oldname, oldver

        self.write_requirements()
        self.write_toplevel_names()
        if os.path.exists(os.path.join(self.egg_info,'depends.txt')):
            log.warn(
                "WARNING: 'depends.txt' will not be used by setuptools 0.6!\n"
                "Use the install_requires/extras_require setup() args instead."
            )


    def write_requirements(self):
        dist = self.distribution
        if not getattr(dist,'install_requires',None) and \
           not getattr(dist,'extras_require',None): return

        requires = os.path.join(self.egg_info,"requires.txt")
        log.info("writing %s", requires)

        if not self.dry_run:
            f = open(requires, 'wt')
            f.write('\n'.join(yield_lines(dist.install_requires)))
            for extra,reqs in dist.extras_require.items():
                f.write('\n\n[%s]\n%s' % (extra, '\n'.join(yield_lines(reqs))))
            f.close()


    def tagged_version(self):
        version = self.distribution.get_version()
        if self.tag_build:
            version+=self.tag_build
        if self.tag_svn_revision and os.path.exists('.svn'):
            version += '-r%s' % self.get_svn_revision()
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
            raise DistutilsError("svn info error: %s" % result.strip())
        return match.group(1)


    def write_toplevel_names(self):
        pkgs = dict.fromkeys(self.distribution.packages or ())
        pkgs.update(dict.fromkeys(self.distribution.py_modules or ()))
        for ext in self.distribution.ext_modules or ():
            if isinstance(ext,tuple):
                name,buildinfo = ext
            else:
                name = ext.name
            pkgs[name]=1
        pkgs = dict.fromkeys([k.split('.',1)[0] for k in pkgs])
        toplevel = os.path.join(self.egg_info,"top_level.txt")
        log.info("writing list of top-level names to %s" % toplevel)
        if not self.dry_run:
            f = open(toplevel, 'wt')
            f.write('\n'.join(pkgs))
            f.write('\n')
            f.close()


