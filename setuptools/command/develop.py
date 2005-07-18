from setuptools.command.easy_install import easy_install
from distutils.util import convert_path
from pkg_resources import Distribution, PathMetadata, normalize_path
from distutils import log
import sys, os

class develop(easy_install):
    """Set up package for development"""

    description = "install package in 'development mode'"

    user_options = [
        ("install-dir=", "d", "link package from DIR"),
        ("script-dir=", "s", "create script wrappers in DIR"),
        ("multi-version", "m", "make apps have to require() a version"),
        ("exclude-scripts", "x", "Don't install scripts"),
        ("always-copy", "a", "Copy all needed dependencies to install dir"),
        ("uninstall", "u", "Uninstall this source package"),
    ]

    boolean_options = [
        'multi-version', 'exclude-scripts', 'always-copy', 'uninstall'
    ]

    command_consumes_arguments = False  # override base

    negative_opt = {}

    def run(self):
        if self.uninstall:
            self.multi_version = True
            self.uninstall_link()
        else:
            self.install_for_development()

    def initialize_options(self):
        self.uninstall = None
        easy_install.initialize_options(self)



    def finalize_options(self):
        ei = self.get_finalized_command("egg_info")
        self.args = [ei.egg_name]
        easy_install.finalize_options(self)
        self.egg_link = os.path.join(self.install_dir, ei.egg_name+'.egg-link')
        self.egg_base = ei.egg_base
        self.egg_path = os.path.abspath(ei.egg_base)

        # Make a distribution for the package's source
        self.dist = Distribution(
            normalize_path(self.egg_path),
            PathMetadata(self.egg_path, os.path.abspath(ei.egg_info)),
            project_name = ei.egg_name
        )

    def install_for_development(self):
        # Ensure metadata is up-to-date
        self.run_command('egg_info')
        ei = self.get_finalized_command("egg_info")

        # Build extensions in-place
        self.reinitialize_command('build_ext', inplace=1)
        self.run_command('build_ext')


        # create an .egg-link in the installation dir, pointing to our egg
        log.info("Creating %s (link to %s)", self.egg_link, self.egg_base)
        if not self.dry_run:
            f = open(self.egg_link,"w")
            f.write(self.egg_path)
            f.close()

        # postprocess the installed distro, fixing up .pth, installing scripts,
        # and handling requirements
        self.process_distribution(None, self.dist)






    def uninstall_link(self):
        if os.path.exists(self.egg_link):
            log.info("Removing %s (link to %s)", self.egg_link, self.egg_base)
            contents = [line.rstrip() for line in file(self.egg_link)]
            if contents != [self.egg_path]:
                log.warn("Link points to %s: uninstall aborted", contents)
                return
            if not self.dry_run:
                os.unlink(self.egg_link)
        if not self.dry_run:
            self.update_pth(self.dist)  # remove any .pth link to us
        if self.distribution.scripts:
            log.warn("Note: you must uninstall or replace scripts manually!")


    def install_egg_scripts(self, dist):
        if dist is not self.dist:
            # Installing a dependency, so fall back to normal behavior
            return easy_install.install_egg_scripts(self,dist)

        # create wrapper scripts in the script dir, pointing to dist.scripts
        for script_name in self.distribution.scripts or []:
            script_path = os.path.abspath(convert_path(script_name))
            script_name = os.path.basename(script_path)
            f = open(script_path,'rU')
            script_text = f.read()
            f.close()
            self.install_script(dist, script_name, script_text, script_path)













