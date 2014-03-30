from distutils.command.bdist_rpm import bdist_rpm as _bdist_rpm

class bdist_rpm(_bdist_rpm):
    """
    Override the default bdist_rpm behavior to do the following:

    1. Run egg_info to ensure the name and version are properly calculated.
    2. Always run 'install' using --single-version-externally-managed to
       disable eggs in RPM distributions.
    3. Replace dash with underscore in the version numbers for better RPM
       compatibility.
    """

    def run(self):
        # ensure distro name is up-to-date
        self.run_command('egg_info')

        _bdist_rpm.run(self)

    def _make_spec_file(self):
        version = self.distribution.get_version()
        rpmversion = version.replace('-','_')
        spec = _bdist_rpm._make_spec_file(self)
        line23 = '%define version ' + version
        line24 = '%define version ' + rpmversion
        spec = [
            line.replace(
                "Source0: %{name}-%{version}.tar",
                "Source0: %{name}-%{unmangled_version}.tar"
            ).replace(
                "setup.py install ",
                "setup.py install --single-version-externally-managed "
            ).replace(
                "%setup",
                "%setup -n %{name}-%{unmangled_version}"
            ).replace(line23, line24)
            for line in spec
        ]
        insert_loc = spec.index(line24) + 1
        unmangled_version = "%define unmangled_version " + version
        spec.insert(insert_loc, unmangled_version)
        return spec
