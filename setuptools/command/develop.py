from distutils.util import convert_path
from distutils import log
from distutils.errors import DistutilsError, DistutilsOptionError
import os
import glob
import io

from setuptools.extern import six

from pkg_resources import Distribution, PathMetadata, normalize_path
from setuptools.command.easy_install import easy_install
import setuptools


class develop(easy_install):
    """Set up package for development"""

    description = "install package in 'development mode'"

    user_options = easy_install.user_options + [
        ("uninstall", "u", "Uninstall this source package"),
        ("egg-path=", None, "Set the path to be used in the .egg-link file"),
        ("use-pth-file", None,
            "Create a pip-compatible .pth file instead of an .egg-link file")
    ]

    boolean_options = easy_install.boolean_options + [
        'uninstall', 'use-pth-file']

    command_consumes_arguments = False  # override base

    def run(self):
        if self.uninstall:
            self.multi_version = True
            self.uninstall_link()
        else:
            self.install_for_development()
        self.warn_deprecated_options()

    def initialize_options(self):
        self.uninstall = None
        self.egg_path = None
        self.use_pth_file = False
        easy_install.initialize_options(self)
        self.setup_path = None
        self.always_copy_from = '.'  # always copy eggs installed in curdir

    def finalize_options(self):
        ei = self.get_finalized_command("egg_info")
        if ei.broken_egg_info:
            template = "Please rename %r to %r before using 'develop'"
            args = ei.egg_info, ei.broken_egg_info
            raise DistutilsError(template % args)
        self.args = [ei.egg_name]

        easy_install.finalize_options(self)
        self.expand_basedirs()
        self.expand_dirs()
        # pick up setup-dir .egg files only: no .egg-info
        self.package_index.scan(glob.glob('*.egg'))

        egg_link_fn = ei.egg_name + '.egg-link'
        self.egg_link = os.path.join(self.install_dir, egg_link_fn)
        self.egg_base = ei.egg_base
        if self.egg_path is None:
            self.egg_path = os.path.abspath(ei.egg_base)

        target = normalize_path(self.egg_base)
        egg_path = normalize_path(os.path.join(self.install_dir,
                                               self.egg_path))
        if egg_path != target:
            raise DistutilsOptionError(
                "--egg-path must be a relative path from the install"
                " directory to " + target
            )

        # Make a distribution for the package's source
        self.dist = Distribution(
            target,
            PathMetadata(target, os.path.abspath(ei.egg_info)),
            project_name=ei.egg_name
        )

        p = self.egg_base.replace(os.sep, '/')
        if p != os.curdir:
            p = '../' * (p.count('/') + 1)
        self.setup_path = p
        p = normalize_path(os.path.join(self.install_dir, self.egg_path, p))
        if p != normalize_path(os.curdir):
            raise DistutilsOptionError(
                "Can't get a consistent path to setup script from"
                " installation directory", p, normalize_path(os.curdir))

    def install_for_development(self):
        if six.PY3 and getattr(self.distribution, 'use_2to3', False):
            # If we run 2to3 we can not do this inplace:

            # Ensure metadata is up-to-date
            self.reinitialize_command('build_py', inplace=0)
            self.run_command('build_py')
            bpy_cmd = self.get_finalized_command("build_py")
            build_path = normalize_path(bpy_cmd.build_lib)

            # Build extensions
            self.reinitialize_command('egg_info', egg_base=build_path)
            self.run_command('egg_info')

            self.reinitialize_command('build_ext', inplace=0)
            self.run_command('build_ext')

            # Fixup egg-link and easy-install.pth
            ei_cmd = self.get_finalized_command("egg_info")
            self.egg_path = build_path
            self.dist.location = build_path
            # XXX
            self.dist._provider = PathMetadata(build_path, ei_cmd.egg_info)
        else:
            # Without 2to3 inplace works fine:
            self.run_command('egg_info')

            # Build extensions in-place
            self.reinitialize_command('build_ext', inplace=1)
            self.run_command('build_ext')

        self.install_site_py()  # ensure that target dir is site-safe
        if setuptools.bootstrap_install_from:
            self.easy_install(setuptools.bootstrap_install_from)
            setuptools.bootstrap_install_from = None

        if self.distribution.namespace_packages and self.use_pth_file:
            self._create_nspth()
        else:
            self._create_egg_link()

        # postprocess the installed distro, fixing up .pth, installing scripts,
        # and handling requirements
        self.process_distribution(None, self.dist, not self.no_deps)

    def _create_nspth(self):
        namespace_packages = self._get_all_ns_packages()

        # TODO Give the nspth it's own variable
        filename, ext = os.path.splitext(self.egg_link)
        filename += '-nspkg-develop.pth'
        self.outputs.append(filename)

        log.info("Installing %s (link to %s)", filename, self.egg_path)

        # TODO: support package_dir.
        lines = [
            self._gen_nspkg_line(package) for package in namespace_packages]

        if self.dry_run:
            return

        with open(filename, 'wt') as f:
            f.writelines(lines)

    def _create_egg_link(self):
        # create an .egg-link in the installation dir, pointing to our egg
        log.info("Creating %s (link to %s)", self.egg_link, self.egg_base)
        if not self.dry_run:
            with open(self.egg_link, "w") as f:
                f.write(self.egg_path + "\n" + self.setup_path)

    def uninstall_link(self):
        if os.path.exists(self.egg_link):
            log.info("Removing %s (link to %s)", self.egg_link, self.egg_base)
            egg_link_file = open(self.egg_link)
            contents = [line.rstrip() for line in egg_link_file]
            egg_link_file.close()
            if contents not in ([self.egg_path],
                                [self.egg_path, self.setup_path]):
                log.warn("Link points to %s: uninstall aborted", contents)
                return
            if not self.dry_run:
                os.unlink(self.egg_link)
        if not self.dry_run:
            self.update_pth(self.dist)  # remove any .pth link to us
        if self.distribution.scripts:
            # XXX should also check for entry point scripts!
            log.warn("Note: you must uninstall or replace scripts manually!")

    def install_egg_scripts(self, dist):
        if dist is not self.dist:
            # Installing a dependency, so fall back to normal behavior
            return easy_install.install_egg_scripts(self, dist)

        # create wrapper scripts in the script dir, pointing to dist.scripts

        # new-style...
        self.install_wrapper_scripts(dist)

        # ...and old-style
        for script_name in self.distribution.scripts or []:
            script_path = os.path.abspath(convert_path(script_name))
            script_name = os.path.basename(script_path)
            with io.open(script_path) as strm:
                script_text = strm.read()
            self.install_script(dist, script_name, script_text, script_path)

    def install_wrapper_scripts(self, dist):
        dist = VersionlessRequirement(dist)
        return easy_install.install_wrapper_scripts(self, dist)

    def _get_all_ns_packages(self):
        """Return sorted list of all package namespaces"""
        nsp = set()
        for pkg in self.distribution.namespace_packages or []:
            pkg = pkg.split('.')
            while pkg:
                nsp.add('.'.join(pkg))
                pkg.pop()
        return sorted(nsp)

    _nspkg_tmpl = (
        "import sys, types, os",
        "p = os.path.join(%(develop_path)r, *%(pth)r)",
        "ie = os.path.exists(os.path.join(p,'__init__.py'))",
        "m = ie and "
            "sys.modules.setdefault(%(pkg)r, types.ModuleType(%(pkg)r))",
        "mp = (m or []) and m.__dict__.setdefault('__path__',[])",
        "(p not in mp) and mp.append(p)",
    )
    "lines for the namespace installer"

    _nspkg_tmpl_multi = (
        'm and setattr(sys.modules[%(parent)r], %(child)r, m)',
    )
    "additional line(s) when a parent package is indicated"

    def _gen_nspkg_line(self, pkg):
        # ensure pkg is not a unicode string under Python 2.7
        pkg = str(pkg)
        develop_path = str(self.egg_path)
        pth = tuple(pkg.split('.'))
        tmpl_lines = self._nspkg_tmpl
        parent, sep, child = pkg.rpartition('.')
        if parent:
            tmpl_lines += self._nspkg_tmpl_multi
        return ';'.join(tmpl_lines) % locals() + '\n'


class VersionlessRequirement(object):
    """
    Adapt a pkg_resources.Distribution to simply return the project
    name as the 'requirement' so that scripts will work across
    multiple versions.

    >>> dist = Distribution(project_name='foo', version='1.0')
    >>> str(dist.as_requirement())
    'foo==1.0'
    >>> adapted_dist = VersionlessRequirement(dist)
    >>> str(adapted_dist.as_requirement())
    'foo'
    """

    def __init__(self, dist):
        self.__dist = dist

    def __getattr__(self, name):
        return getattr(self.__dist, name)

    def as_requirement(self):
        return self.project_name
