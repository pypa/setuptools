from distutils.cmd import Command
import os

class depends(Command):
    """Download and install dependencies, if needed"""

    description = "download and install dependencies, if needed"

    user_options = [
        ('temp=', 't',
         "directory where dependencies will be downloaded and built"),
        ('ignore-extra-args', 'i',
         "ignore options that won't be passed to child setup scripts"),
    ]

    def initialize_options(self):
        self.temp = None
        self.install_purelib = self.install_platlib = None
        self.install_lib     = self.install_libbase = None
        self.install_scripts = self.install_data = self.install_headers = None
        self.compiler = self.debug = self.force = None

    def finalize_options(self):
        self.set_undefined_options('build',('build_temp', 'temp'))

    def run(self):
        self.announce("downloading and building here")
