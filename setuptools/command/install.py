from distutils.command.install import install as _install

class install(_install):
    """Build dependencies before installation"""

    def has_dependencies(self):
        return self.distribution.has_dependencies()

    sub_commands = [('depends', has_dependencies)] + _install.sub_commands
