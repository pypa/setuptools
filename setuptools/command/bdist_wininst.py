from distutils.command.bdist_wininst import bdist_wininst as _bdist_wininst
import os

class bdist_wininst(_bdist_wininst):

    def create_exe(self, arcname, fullname, bitmap=None):

        _bdist_wininst.create_exe(self, arcname, fullname, bitmap)

        if self.target_version:
            installer_name = os.path.join(self.dist_dir,
                                          "%s.win32-py%s.exe" %
                                           (fullname, self.target_version))
            pyversion = self.target_version
        else:
            installer_name = os.path.join(self.dist_dir,
                                          "%s.win32.exe" % fullname)
            pyversion = 'any'

        getattr(self.distribution,'dist_files',[]).append(
            ('bdist_wininst', pyversion, installer_name)
        )
