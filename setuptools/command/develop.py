from setuptools import namespaces
from setuptools.command.easy_install import easy_install


class develop(namespaces.DevelopInstaller, easy_install):
    """Set up package for development"""

    description = "install package in 'development mode'"

    user_options = easy_install.user_options + [
        ("uninstall", "u", "Uninstall this source package"),
        ("egg-path=", None, "Set the path to be used in the .egg-link file"),
    ]

    boolean_options = easy_install.boolean_options + ['uninstall']

    command_consumes_arguments = False  # override base

    def run(self):
        raise NotImplementedError

    def initialize_options(self):
        self.uninstall = None
        self.egg_path = None
        easy_install.initialize_options(self)
        self.setup_path = None
        self.always_copy_from = '.'  # always copy eggs installed in curdir

    def finalize_options(self) -> None:
        raise NotImplementedError
