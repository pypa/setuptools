from setuptools import Command, namespaces


class develop(namespaces.DevelopInstaller, Command):
    """Set up package for development"""

    def run(self):
        raise NotImplementedError

    def initialize_options(self):
        "stubbed"

    def finalize_options(self) -> None:
        raise NotImplementedError
