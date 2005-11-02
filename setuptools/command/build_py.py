import os.path, sys
from distutils.command.build_py import build_py as _build_py
from distutils.util import convert_path
from glob import glob


class build_py(_build_py):
    """Enhanced 'build_py' command that includes data files with packages

    The data files are specified via a 'package_data' argument to 'setup()'.
    See 'setuptools.dist.Distribution' for more details.

    Also, this version of the 'build_py' command allows you to specify both
    'py_modules' and 'packages' in the same setup operation.
    """

    def finalize_options(self):
        _build_py.finalize_options(self)
        self.package_data = self.distribution.package_data
        self.data_files = self.get_data_files()

    def run(self):
        """Build modules, packages, and copy data files to build directory"""
        if not self.py_modules and not self.packages:
            return

        if self.py_modules:
            self.build_modules()

        if self.packages:
            self.build_packages()
            self.build_package_data()

        # Only compile actual .py files, using our base class' idea of what our
        # output files are.
        self.byte_compile(_build_py.get_outputs(self, include_bytecode=0))





    def get_data_files(self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples"""
        data = []
        for package in self.packages or ():
            # Locate package source directory
            src_dir = self.get_package_dir(package)

            # Compute package build directory
            build_dir = os.path.join(*([self.build_lib] + package.split('.')))

            # Length of path to strip from found files
            plen = len(src_dir)+1

            # Strip directory from globbed filenames
            filenames = [
                file[plen:] for file in self.find_data_files(package, src_dir)
                ]
            data.append( (package, src_dir, build_dir, filenames) )
        return data

    def find_data_files(self, package, src_dir):
        """Return filenames for package's data files in 'src_dir'"""
        globs = (self.package_data.get('', [])
                 + self.package_data.get(package, []))
        files = []
        for pattern in globs:
            # Each pattern has to be converted to a platform-specific path
            files.extend(glob(os.path.join(src_dir, convert_path(pattern))))
        return files

    def build_package_data(self):
        """Copy data files into build directory"""
        lastdir = None
        for package, src_dir, build_dir, filenames in self.data_files:
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                self.copy_file(os.path.join(src_dir, filename), target)



    def get_outputs(self, include_bytecode=1):
        """Return complete list of files copied to the build directory

        This includes both '.py' files and data files, as well as '.pyc' and
        '.pyo' files if 'include_bytecode' is true.  (This method is needed for
        the 'install_lib' command to do its job properly, and to generate a
        correct installation manifest.)
        """
        return _build_py.get_outputs(self, include_bytecode) + [
            os.path.join(build_dir, filename)
            for package, src_dir, build_dir,filenames in self.data_files
            for filename in filenames
            ]


if sys.version>="2.4":
    # Python 2.4 already has the above code
    build_py = _build_py























