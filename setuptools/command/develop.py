from setuptools.command.easy_install import easy_install
from distutils.util import convert_path, subst_vars
from pkg_resources import Distribution, PathMetadata, normalize_path
from distutils import log
from distutils.errors import *
import sys, os, setuptools, glob
from distutils.sysconfig import get_config_vars
from distutils.command.install import INSTALL_SCHEMES, SCHEME_KEYS

if sys.version < "2.6":
    USER_BASE = None
    USER_SITE = None
    HAS_USER_SITE = False
else:
    from site import USER_BASE
    from site import USER_SITE
    HAS_USER_SITE = True

class develop(easy_install):
    """Set up package for development"""

    description = "install package in 'development mode'"

    user_options = easy_install.user_options + [
        ("uninstall", "u", "Uninstall this source package"),
        ("egg-path=", None, "Set the path to be used in the .egg-link file"),
    ]

    boolean_options = easy_install.boolean_options + ['uninstall']

    if HAS_USER_SITE:
        user_options.append(('user', None,
                             "install in user site-package '%s'" % USER_SITE))
        boolean_options.append('user')

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
        easy_install.initialize_options(self)
        self.setup_path = None
        self.always_copy_from = '.'   # always copy eggs installed in curdir
        self.user = 0
        self.install_purelib = None     # for pure module distributions
        self.install_platlib = None     # non-pure (dists w/ extensions)
        self.install_headers = None     # for C/C++ headers
        self.install_lib = None         # set to either purelib or platlib
        self.install_scripts = None
        self.install_data = None
        self.install_base = None
        self.install_platbase = None
        self.install_userbase = USER_BASE
        self.install_usersite = USER_SITE

    def select_scheme(self, name):
        """Sets the install directories by applying the install schemes."""
        # it's the caller's problem if they supply a bad name!
        scheme = INSTALL_SCHEMES[name]
        for key in SCHEME_KEYS:
            attrname = 'install_' + key
            if getattr(self, attrname) is None:
                setattr(self, attrname, scheme[key])

    def create_home_path(self):
        """Create directories under ~."""
        if not self.user:
            return
        home = convert_path(os.path.expanduser("~"))
        for name, path in self.config_vars.iteritems():
            if path.startswith(home) and not os.path.isdir(path):
                self.debug_print("os.makedirs('%s', 0700)" % path)
                os.makedirs(path, 0700)

    def _expand_attrs(self, attrs):
        for attr in attrs:
            val = getattr(self, attr)
            if val is not None:
                if os.name == 'posix' or os.name == 'nt':
                    val = os.path.expanduser(val)
                val = subst_vars(val, self.config_vars)
                setattr(self, attr, val)

    def expand_basedirs(self):
        """Calls `os.path.expanduser` on install_base, install_platbase and
        root."""
        self._expand_attrs(['install_base', 'install_platbase', 'root'])

    def expand_dirs(self):
        """Calls `os.path.expanduser` on install dirs."""
        self._expand_attrs(['install_purelib', 'install_platlib',
                            'install_lib', 'install_headers',
                            'install_scripts', 'install_data',])

    def finalize_options(self):
        ei = self.get_finalized_command("egg_info")
        if ei.broken_egg_info:
            raise DistutilsError(
            "Please rename %r to %r before using 'develop'"
            % (ei.egg_info, ei.broken_egg_info)
            )
        self.args = [ei.egg_name]


        py_version = sys.version.split()[0]
        prefix, exec_prefix = get_config_vars('prefix', 'exec_prefix')
        self.config_vars = {'dist_name': self.distribution.get_name(),
                            'dist_version': self.distribution.get_version(),
                            'dist_fullname': self.distribution.get_fullname(),
                            'py_version': py_version,
                            'py_version_short': py_version[0:3],
                            'py_version_nodot': py_version[0] + py_version[2],
                            'sys_prefix': prefix,
                            'prefix': prefix,
                            'sys_exec_prefix': exec_prefix,
                            'exec_prefix': exec_prefix,
                           }

        if HAS_USER_SITE:
            self.config_vars['userbase'] = self.install_userbase
            self.config_vars['usersite'] = self.install_usersite

        # fix the install_dir if "--user" was used
        if self.user:
            self.create_home_path()
            if self.install_userbase is None:
                raise DistutilsPlatformError(
                    "User base directory is not specified")
            self.install_base = self.install_platbase = self.install_userbase
            if os.name == 'posix':
                self.select_scheme("unix_user")
            else:
                self.select_scheme(os.name + "_user")

        self.expand_basedirs()
        self.expand_dirs()

        if self.user and self.install_purelib:
            self.install_dir = self.install_purelib
            self.script_dir = self.install_scripts

        easy_install.finalize_options(self)
        # pick up setup-dir .egg files only: no .egg-info
        self.package_index.scan(glob.glob('*.egg'))

        self.egg_link = os.path.join(self.install_dir, ei.egg_name+'.egg-link')
        self.egg_base = ei.egg_base
        if self.egg_path is None:
            self.egg_path = os.path.abspath(ei.egg_base)

        target = normalize_path(self.egg_base)
        if normalize_path(os.path.join(self.install_dir, self.egg_path)) != target:
            raise DistutilsOptionError(
                "--egg-path must be a relative path from the install"
                " directory to "+target
        )

        # Make a distribution for the package's source
        self.dist = Distribution(
            target,
            PathMetadata(target, os.path.abspath(ei.egg_info)),
            project_name = ei.egg_name
        )

        p = self.egg_base.replace(os.sep,'/')
        if p!= os.curdir:
            p = '../' * (p.count('/')+1)
        self.setup_path = p
        p = normalize_path(os.path.join(self.install_dir, self.egg_path, p))
        if  p != normalize_path(os.curdir):
            raise DistutilsOptionError(
                "Can't get a consistent path to setup script from"
                " installation directory", p, normalize_path(os.curdir))

    def install_for_development(self):
        # Ensure metadata is up-to-date
        self.run_command('egg_info')
        # Build extensions in-place
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')
        self.install_site_py()  # ensure that target dir is site-safe
        if setuptools.bootstrap_install_from:
            self.easy_install(setuptools.bootstrap_install_from)
            setuptools.bootstrap_install_from = None

        # create an .egg-link in the installation dir, pointing to our egg
        log.info("Creating %s (link to %s)", self.egg_link, self.egg_base)
        if not self.dry_run:
            f = open(self.egg_link,"w")
            f.write(self.egg_path + "\n" + self.setup_path)
            f.close()
        # postprocess the installed distro, fixing up .pth, installing scripts,
        # and handling requirements
        self.process_distribution(None, self.dist, not self.no_deps)


    def uninstall_link(self):
        if os.path.exists(self.egg_link):
            log.info("Removing %s (link to %s)", self.egg_link, self.egg_base)
            contents = [line.rstrip() for line in open(self.egg_link)]
            if contents not in ([self.egg_path], [self.egg_path, self.setup_path]):
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
            return easy_install.install_egg_scripts(self,dist)

        # create wrapper scripts in the script dir, pointing to dist.scripts

        # new-style...
        self.install_wrapper_scripts(dist)

        # ...and old-style
        for script_name in self.distribution.scripts or []:
            script_path = os.path.abspath(convert_path(script_name))
            script_name = os.path.basename(script_path)
            f = open(script_path,'rU')
            script_text = f.read()
            f.close()
            self.install_script(dist, script_name, script_text, script_path)

