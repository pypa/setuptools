import distutils, os
from setuptools import Command
from distutils.util import convert_path
from distutils import log
from distutils.errors import *
from setuptools.command.setopt import edit_config, option_base

class alias(option_base):
    """Abstract base class for commands that mess with config files"""
    
    description = "set an option in setup.cfg or another config file"

    user_options = [
        ('alias=',  'a',  'the name of the new pseudo-command'),
        ('command=', 'c', 'command(s) and options to invoke when used'),
        ('remove',   'r', 'remove (unset) the alias'), 
    ] + option_base.user_options

    boolean_options = option_base.boolean_options + ['remove']

    def initialize_options(self):
        option_base.initialize_options(self)
        self.alias = None
        self.command = None
        self.remove = None

    def finalize_options(self):
        option_base.finalize_options(self)
        if self.alias is None:
            raise DistutilsOptionError("Must specify name (--alias/-a)")
        if self.command is None and not self.remove:
            raise DistutilsOptionError("Must specify --command or --remove")

    def run(self):
        edit_config(
            self.filename, {'aliases': {self.alias:self.command}},
            self.dry_run
        )

