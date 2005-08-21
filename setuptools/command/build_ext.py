# Attempt to use Pyrex for building extensions, if available

try:
    from Pyrex.Distutils.build_ext import build_ext as _build_ext
except ImportError:
    from distutils.command.build_ext import build_ext as _build_ext

import os
from distutils.file_util import copy_file

class build_ext(_build_ext):
    
    def run(self):
        """Build extensions in build directory, then copy if --inplace"""
        old_inplace, self.inplace = self.inplace, 0
        _build_ext.run(self)
        self.inplace = old_inplace
        if old_inplace:
            self.copy_extensions_to_source()

    def copy_extensions_to_source(self):
        build_py = self.get_finalized_command('build_py')
        for ext in self.extensions:
            fullname = ext.name
            modpath = fullname.split('.')
            package = '.'.join(modpath[:-1])
            base = modpath[-1]
            package_dir = build_py.get_package_dir(package)
            dest_filename = os.path.join(package_dir,
                                        self.get_ext_filename(base))
            src_filename = os.path.join(self.build_lib,
                                        self.get_ext_filename(fullname))

            # Always copy, even if source is older than destination, to ensure
            # that the right extensions for the current Python/platform are
            # used.
            copy_file(
                src_filename, dest_filename, verbose=self.verbose,
                dry_run=self.dry_run
            )

