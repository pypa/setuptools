"""setuptools.command.egg_info

Create a distribution's .egg-info directory and contents"""

# This module should be kept compatible with Python 2.3
import os, re
from setuptools import Command
from distutils.errors import *
from distutils import log
from pkg_resources import parse_requirements, safe_name, \
    safe_version, yield_lines, EntryPoint, iter_entry_points

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

        # Set package version for the benefit of dumber commands
        # (e.g. sdist, bdist_wininst, etc.) 
        #
        self.distribution.metadata.version = self.egg_version
















    def write_or_delete_file(self, what, filename, data):
        """Write `data` to `filename` or delete if empty

        If `data` is non-empty, this routine is the same as ``write_file()``.
        If `data` is empty but not ``None``, this is the same as calling
        ``delete_file(filename)`.  If `data` is ``None``, then this is a no-op
        unless `filename` exists, in which case a warning is issued about the
        orphaned file.
        """
        if data:
            self.write_file(what, filename, data)
        elif os.path.exists(filename):
            if data is None:
                log.warn(
                    "%s not set in setup(), but %s exists", what, filename
                )
                return
            else:
                self.delete_file(filename)

    def write_file(self, what, filename, data):
        """Write `data` to `filename` (if not a dry run) after announcing it

        `what` is used in a log message to identify what is being written
        to the file.
        """
        log.info("writing %s to %s", what, filename)
        if not self.dry_run:
            f = open(filename, 'wb')
            f.write(data)
            f.close()

    def delete_file(self, filename):
        """Delete `filename` (if not a dry run) after announcing it"""
        log.info("deleting %s", filename)
        if not self.dry_run:
            os.unlink(filename)




    def run(self):
        # Make the .egg-info directory, then write PKG-INFO and requires.txt
        self.mkpath(self.egg_info)
        installer = self.distribution.fetch_build_egg
        for ep in iter_entry_points('egg_info.writers'):
            writer = ep.load(installer=installer)
            writer(self, ep.name, os.path.join(self.egg_info,ep.name))

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
        revision = 0
        urlre = re.compile('url="([^"]+)"')
        revre = re.compile('committed-rev="(\d+)"')
        for base,dirs,files in os.walk(os.curdir):
            if '.svn' not in dirs:
                dirs[:] = []
                continue    # no sense walking uncontrolled subdirs
            dirs.remove('.svn')
            f = open(os.path.join(base,'.svn','entries'))
            data = f.read()
            f.close()
            dirurl = urlre.search(data).group(1)    # get repository URL
            if base==os.curdir:
                base_url = dirurl+'/'   # save the root url
            elif not dirurl.startswith(base_url):
                dirs[:] = []
                continue    # not part of the same svn tree, skip it
            for match in revre.finditer(data):
                revision = max(revision, int(match.group(1)))
        return str(revision or get_pkg_info_revision())

def write_pkg_info(cmd, basename, filename):
    log.info("writing %s", filename)
    if not cmd.dry_run:
        metadata = cmd.distribution.metadata
        metadata.version, oldver = cmd.egg_version, metadata.version
        metadata.name, oldname   = cmd.egg_name, metadata.name
        try:
            # write unescaped data to PKG-INFO, so older pkg_resources
            # can still parse it
            metadata.write_pkg_info(cmd.egg_info)
        finally:
            metadata.name, metadata.version = oldname, oldver

def warn_depends_obsolete(cmd, basename, filename):
    if os.path.exists(filename):
        log.warn(
            "WARNING: 'depends.txt' is not used by setuptools 0.6!\n"
            "Use the install_requires/extras_require setup() args instead."
        )


def write_requirements(cmd, basename, filename):
    dist = cmd.distribution
    data = ['\n'.join(yield_lines(dist.install_requires or ()))]
    for extra,reqs in (dist.extras_require or {}).items():
        data.append('\n\n[%s]\n%s' % (extra, '\n'.join(yield_lines(reqs))))
    cmd.write_or_delete_file("requirements", filename, ''.join(data))

def write_toplevel_names(cmd, basename, filename):
    pkgs = dict.fromkeys(
        [k.split('.',1)[0]
            for k in cmd.distribution.iter_distribution_names()
        ]
    )
    cmd.write_file("top-level names", filename, '\n'.join(pkgs)+'\n')






def write_arg(cmd, basename, filename):
    argname = os.path.splitext(basename)[0]
    value = getattr(cmd.distribution, argname, None)
    if value is not None:
        value = '\n'.join(value)+'\n'
    cmd.write_or_delete_file(argname, filename, value)

def write_entries(cmd, basename, filename):
    ep = cmd.distribution.entry_points

    if isinstance(ep,basestring) or ep is None:
        data = ep
    elif ep is not None:
        data = []
        for section, contents in ep.items():
            if not isinstance(contents,basestring):
                contents = EntryPoint.parse_group(section, contents)
                contents = '\n'.join(map(str,contents.values()))
            data.append('[%s]\n%s\n\n' % (section,contents))
        data = ''.join(data)

    cmd.write_or_delete_file('entry points', filename, data)

def get_pkg_info_revision():
    # See if we can get a -r### off of PKG-INFO, in case this is an sdist of
    # a subversion revision
    #
    if os.path.exists('PKG-INFO'):
        f = open('PKG-INFO','rU')
        for line in f:
            match = re.match(r"Version:.*-r(\d+)\s*$", line)
            if match:
                return int(match.group(1))
    return 0







