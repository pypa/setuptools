import setuptools, sys
from distutils.command.install import install as _install

class install(_install):
    """Use easy_install to install the package, w/dependencies"""

    def handle_extra_path(self):
        # We always ignore extra_path, because we always install eggs
        # (you can always use install_* commands directly if needed)
        self.path_file = None
        self.extra_dirs = ''

    def run(self):
        calling_module = sys._getframe(1).f_globals.get('__name__','')
        if calling_module != 'distutils.dist':
            # We're not being run from the command line, so use old-style
            # behavior.  This is a bit kludgy, because a command might use
            # dist.run_command() to run 'install', but bdist_dumb and
            # bdist_wininst both call run directly at the moment.
            # When this is part of the distutils, the old install behavior
            # should probably be requested with a flag, or a different method.
            return _install.run(self)

        from setuptools.command.easy_install import easy_install
        cmd = easy_install(
            self.distribution, args="x", ignore_conflicts_at_my_risk=1
        )
        cmd.ensure_finalized()  # finalize before bdist_egg munges install cmd

        self.run_command('bdist_egg')
        args = [self.distribution.get_command_obj('bdist_egg').egg_output]

        if setuptools.bootstrap_install_from:
            # Bootstrap self-installation of setuptools
            args.insert(0, setuptools.bootstrap_install_from)

        cmd.args = args
        cmd.run()
        setuptools.bootstrap_install_from = None

