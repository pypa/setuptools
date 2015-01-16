from distutils import log
import distutils.command.install_scripts as orig
import os

from pkg_resources import Distribution, PathMetadata, ensure_directory


class install_scripts(orig.install_scripts):
    """Do normal script install, plus any egg_info wrapper scripts"""

    def initialize_options(self):
        orig.install_scripts.initialize_options(self)
        self.no_ep = False

    def run(self):
        import setuptools.command.easy_install as ei

        self.run_command("egg_info")
        if self.distribution.scripts:
            orig.install_scripts.run(self)  # run first to set up self.outfiles
        else:
            self.outfiles = []
        if self.no_ep:
            # don't install entry point scripts into .egg file!
            return

        ei_cmd = self.get_finalized_command("egg_info")
        dist = Distribution(
            ei_cmd.egg_base, PathMetadata(ei_cmd.egg_base, ei_cmd.egg_info),
            ei_cmd.egg_name, ei_cmd.egg_version,
        )
        bs_cmd = self.get_finalized_command('build_scripts')
        cmd = ei.CommandSpec.from_param(getattr(bs_cmd, 'executable', None))
        is_wininst = getattr(
            self.get_finalized_command("bdist_wininst"), '_is_running', False
        )
        writer = ei.ScriptWriter
        if is_wininst:
            cmd = ei.CommandSpec.from_string("python.exe")
            writer = ei.WindowsScriptWriter
        for args in writer.best().get_args(dist, cmd.as_header()):
            self.write_script(*args)

    def write_script(self, script_name, contents, mode="t", *ignored):
        """Write an executable file to the scripts directory"""
        from setuptools.command.easy_install import chmod, current_umask

        log.info("Installing %s script to %s", script_name, self.install_dir)
        target = os.path.join(self.install_dir, script_name)
        self.outfiles.append(target)

        mask = current_umask()
        if not self.dry_run:
            ensure_directory(target)
            f = open(target, "w" + mode)
            f.write(contents)
            f.close()
            chmod(target, 0o777 - mask)
