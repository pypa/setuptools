from distutils.cmd import Command
import os, sys


class depends(Command):

    """Download and install dependencies, if needed"""

    description = "download and install dependencies, if needed"

    user_options = [
        ('temp=', 't',
         "directory where dependencies will be downloaded and built"),
        ('ignore-extra-args', 'i',
         "ignore options that won't be passed to child setup scripts"),
    ]

    path_attrs = [
        # Note: these must be in *reverse* order, as they are pushed onto the
        # *front* of a copy of sys.path.
        ('install','install_libbase'),      # installation base if extra_path
        ('install_lib','install_dir'),      # where modules are installed
    ]


    def initialize_options(self):
        self.temp = None

    def finalize_options(self):
        self.set_undefined_options('build',('build_temp', 'temp'))
        self.set_search_path()

    def set_search_path(self):
        """Determine paths to check for installed dependencies"""
        path = sys.path[:]  # copy sys path
        for cmd,attr in self.path_attrs:
            dir = getattr(self.get_finalized_command(cmd),attr,None)
            if dir and dir not in path:
                path.insert(0,dir)  # prepend
        self.search_path = path

    def run(self):
        self.announce("checking for installed dependencies")
        needed = [
            dep for dep in self.distribution.requires if self.is_needed(dep)
        ]
        if not needed:
            self.announce("all dependencies are present and up-to-date")
            return

        # Alert the user to missing items
        fmt = "\t%s\t%s\n"
        items = [fmt % (dep.full_name(),dep.homepage) for dep in needed]
        items.insert(0,"Please install the following packages first:\n")
        items.append('')
        raise SystemExit('\n'.join(items))  # dump msg to stderr and exit


    def is_needed(self,dep):
        """Does the specified dependency need to be installed/updated?"""

        self.announce("searching for "+dep.full_name())
        version = dep.get_version(self.search_path)

        if version is None:
            self.announce(name+" not found!")
            return True

        if str(version)=="unknown":
            status = dep.name+" is installed"
        else:
            status = dep.name+" version "+str(version)+" found"

        if dep.version_ok(version):
            self.announce(status+" (OK)")
            return False
        else:
            self.announce(status+" (update needed)")
            return True



