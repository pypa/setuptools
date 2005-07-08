import distutils, os
from setuptools import Command
from setuptools.command.setopt import edit_config, option_base

class saveopts(option_base):
    """Save command-line options to a file"""

    description = "save supplied options to setup.cfg or other config file"

    user_options = option_base.user_options + [
    ]

    boolean_options = option_base.boolean_options + [
    ]    

    def run(self):
        dist = self.distribution
        commands = dist.command_options.keys()
        settings = {}
        for cmd in commands:
            if cmd=='saveopts':
                continue
            for opt,(src,val) in dist.get_option_dict(cmd).items():
                if src=="command line":
                    settings.setdefault(cmd,{})[opt] = val
        edit_config(self.filename, settings, self.dry_run)

