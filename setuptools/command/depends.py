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

    # Command options that can be safely passed to dependencies' setup scripts
    safe_opts = {
        'install': [
            'prefix','exec-prefix','home','install-base','install-platbase',
            'root','optimize','force','verbose','quiet'
        ],
        'build': ['compiler','debug','force','verbose','quiet'],
    }

    # Options with string arguments that are *not* directories or files, and
    # so should *not* have absolute-path fixups applied.
    non_fs_opts = {'build':['compiler'] }


    def initialize_options(self):
        self.temp = None; self.ignore_extra_args = None

    def finalize_options(self):
        self.set_undefined_options('build',('build_temp', 'temp'))
        self.set_search_path()
        self.set_subcommand_args()

    def set_subcommand_args(self):
        safe = {'install':[]}   # ensure we at least perform an install
        unsafe = {}
        copts = self.distribution.get_cmdline_options()

        if 'depends' in copts:
            del copts['depends']

        for cmd,opts in copts.items():
            safe_opts = self.safe_opts.get(cmd,())
            non_fs_opts = self.non_fs_opts.get(cmd,())

            for opt,val in opts.items():
                if opt in safe_opts:
                    cmdline = safe.setdefault(cmd,[])
                    if val is not None and opt not in non_fs_opts:
                        val = os.path.abspath(val)
                else:
                    cmdline = unsafe.setdefault(cmd,[])

                cmdline.append('--'+opt)
                if val is not None:
                    cmdline.append(val)

        self.safe_options = safe
        self.unsafe_options = unsafe

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

        argv = [sys.executable,'setup.py']
        for cmd,line in self.safe_options.items():
            argv.append(cmd); argv.extend(line)

        self.announce(
            "dependencies will be installed using:\n    "+' '.join(argv)+'\n'
        )

        # Alert for unsupported commands/options, unless '-i' was used
        if self.unsafe_options:
            self.warn_unsafe_options_used()
            if not self.ignore_extra_args:
                raise SystemExit(
                    "Unsupported options for building dependencies; please"
                    " add 'depends -i'\nto your command line if you want to"
                    " force the build to proceed.\nOtherwise, you will need"
                    " to omit the unsupported options,\nor install the"
                    " dependencies manually."
                )


        # Alert the user to missing items
        fmt = "\t%s\t%s\n"
        items = [fmt % (dep.full_name(),dep.homepage) for dep in needed]
        items.insert(0,"Please install the following packages *first*:\n")
        items.append('')
        raise SystemExit('\n'.join(items))  # dump msg to stderr and exit



    def warn_unsafe_options_used(self):
        lines = []; write = lines.append
        write("the following command options are not supported for building")
        write("dependencies, and will be IGNORED:")
        for cmd,line in self.unsafe_options.items():
            write('\t%s %s' % (cmd,' '.join(line)))
        write('')
        self.warn('\n'.join(lines))


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










