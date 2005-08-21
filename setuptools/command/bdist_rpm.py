# This is just a kludge so that bdist_rpm doesn't guess wrong about the
# distribution name and version, if the egg_info command is going to alter them

from distutils.command.bdist_rpm import bdist_rpm as _bdist_rpm

class bdist_rpm(_bdist_rpm):

    def run(self):
        self.run_command('egg_info')    # ensure distro name is up-to-date
        _bdist_rpm.run(self)

