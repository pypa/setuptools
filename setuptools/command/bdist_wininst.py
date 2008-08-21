from distutils.command.bdist_wininst import bdist_wininst as _bdist_wininst
import os, sys

class bdist_wininst(_bdist_wininst):

    def create_exe(self, arcname, fullname, bitmap=None):
        _bdist_wininst.create_exe(self, arcname, fullname, bitmap)
        dist_files = getattr(self.distribution, 'dist_files', [])

        if self.target_version:
            installer_name = os.path.join(self.dist_dir,
                                          "%s.win32-py%s.exe" %
                                           (fullname, self.target_version))
            pyversion = self.target_version

            # fix 2.5 bdist_wininst ignoring --target-version spec
            bad = ('bdist_wininst','any',installer_name)
            if bad in dist_files:
                dist_files.remove(bad)
        else:
            installer_name = os.path.join(self.dist_dir,
                                          "%s.win32.exe" % fullname)
            pyversion = 'any'
        good = ('bdist_wininst', pyversion, installer_name)
        if good not in dist_files:
            dist_files.append(good)

    def reinitialize_command (self, command, reinit_subcommands=0):
        cmd = self.distribution.reinitialize_command(
            command, reinit_subcommands)
        if command in ('install', 'install_lib'):
            cmd.install_lib = None  # work around distutils bug
        return cmd

    def run(self):
        self._is_running = True
        try:
            _bdist_wininst.run(self)
        finally:
            self._is_running = False

