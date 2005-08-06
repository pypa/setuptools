import setuptools
from distutils.command.install import install as _install

class install(_install):
    """Build dependencies before installation"""

    def handle_extra_path(self):
        # We always ignore extra_path, because we always install eggs
        # (you can always use install_* commands directly if needed)
        self.path_file = None
        self.extra_dirs = ''

    def run(self):
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


