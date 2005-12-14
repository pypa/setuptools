import setuptools, sys
from distutils.command.install import install as _install
from distutils.errors import DistutilsArgError

class install(_install):
    """Use easy_install to install the package, w/dependencies"""

    user_options = _install.user_options + [
        ('old-and-unmanageable', None, "Try not to use this!"),
        ('single-version-externally-managed', None,
            "used by system package builders to create 'flat' eggs"),
    ]

    boolean_options = _install.boolean_options + [
        'old-and-unmanageable', 'single-version-externally-managed',
    ]

    sub_commands = [
        cmd for cmd in _install.sub_commands if cmd[0] != 'install_scripts'
    ] + [
        ('install_egg_info', lambda self: True),
        ('install_scripts',  lambda self: True),
    ]

    def initialize_options(self):
        _install.initialize_options(self)
        self.old_and_unmanageable = None
        self.single_version_externally_managed = None
        self.no_compile = None  # make DISTUTILS_DEBUG work right!

    def finalize_options(self):
        _install.finalize_options(self)
        if self.single_version_externally_managed:
            if not self.root and not self.record:
                raise DistutilsArgError(
                    "You must specify --record or --root when building system"
                    " packages"
                )

    def handle_extra_path(self):
        # We always ignore extra_path, because we install as .egg or .egg-info
        self.path_file = None
        self.extra_dirs = ''

    def run(self):
        if (self.old_and_unmanageable or self.single_version_externally_managed
           or sys._getframe(1).f_globals.get('__name__','') != 'distutils.dist'
        ):
            # Either we were asked for the old behavior, or we're not being
            # run from the command line.  This is a bit kludgy, because a
            # command might use dist.run_command() to run 'install', but
            # bdist_dumb and bdist_wininst both call run() directly right now.
            return _install.run(self)

        from setuptools.command.easy_install import easy_install

        cmd = easy_install(
            self.distribution, args="x", ignore_conflicts_at_my_risk=1,
            root=self.root, record=self.record,
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













