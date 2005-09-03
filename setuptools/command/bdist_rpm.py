# This is just a kludge so that bdist_rpm doesn't guess wrong about the
# distribution name and version, if the egg_info command is going to alter
# them, and another kludge to allow you to build old-style non-egg RPMs

from distutils.command.bdist_rpm import bdist_rpm as _bdist_rpm

class bdist_rpm(_bdist_rpm):

    user_options = _bdist_rpm.user_options + [
        ('no-egg', None, "Don't install as an egg (may break the package!)")
    ]

    boolean_options = _bdist_rpm.boolean_options + ['no-egg']

    def initialize_options(self):
        _bdist_rpm.initialize_options(self)
        self.no_egg = None

    def run(self):
        self.run_command('egg_info')    # ensure distro name is up-to-date
        _bdist_rpm.run(self)

    def _make_spec_file(self):
        spec = _bdist_rpm._make_spec_file(self)
        if not self.no_egg:
            return spec

        # Hack the spec file so that we install old-style
        return [
            line.replace(
                "setup.py install ","setup.py install --old-and-unmanageable "
            ) for line in spec
        ]
