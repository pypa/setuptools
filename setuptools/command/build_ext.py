from distutils.command.build_ext import build_ext as _du_build_ext
try:
    # Attempt to use Pyrex for building extensions, if available
    from Pyrex.Distutils.build_ext import build_ext as _build_ext
except ImportError:
    _build_ext = _du_build_ext

import os, sys
from distutils.file_util import copy_file
from setuptools.extension import SharedLibrary
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler

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
        for ext in self.extensions or ():
            fullname = self.get_ext_fullname(ext.name)
            filename = self.get_ext_filename(fullname)
            modpath = fullname.split('.')
            package = '.'.join(modpath[:-1])
            package_dir = build_py.get_package_dir(package)
            dest_filename = os.path.join(package_dir,os.path.basename(filename))
            src_filename = os.path.join(self.build_lib,filename)

            # Always copy, even if source is older than destination, to ensure
            # that the right extensions for the current Python/platform are
            # used.
            copy_file(
                src_filename, dest_filename, verbose=self.verbose,
                dry_run=self.dry_run
            )

    if _build_ext is not _du_build_ext:
        # Workaround for problems using some Pyrex versions w/SWIG and/or 2.4
        def swig_sources(self, sources, *otherargs):
            # first do any Pyrex processing
            sources = _build_ext.swig_sources(self, sources) or sources
            # Then do any actual SWIG stuff on the remainder
            return _du_build_ext.swig_sources(self, sources, *otherargs)

    def get_ext_filename(self, fullname):
        filename = _build_ext.get_ext_filename(self,fullname)
        for ext in self.shlibs:
            if self.get_ext_fullname(ext.name)==fullname:
                fn, ext = os.path.splitext(filename)
                fn = self.shlib_compiler.library_filename(fn,'shared')
                print "shlib",fn
                return fn
        return filename

    def initialize_options(self):
        _build_ext.initialize_options(self)
        self.shlib_compiler = None
        self.shlibs = []

    def finalize_options(self):
        _build_ext.finalize_options(self)
        self.shlibs = [ext for ext in self.extensions or ()
                        if isinstance(ext,SharedLibrary)]
        if self.shlibs:
            self.setup_shlib_compiler()
            self.library_dirs.append(self.build_lib)

    def build_extension(self, ext):
        _compiler = self.compiler
        try:
            if isinstance(ext,SharedLibrary):
                self.compiler = self.shlib_compiler
            _build_ext.build_extension(self,ext)
        finally:
            self.compiler = _compiler


    def setup_shlib_compiler(self):
        compiler = self.shlib_compiler = new_compiler(
            compiler=self.compiler, dry_run=self.dry_run, force=self.force
        ) 
        customize_compiler(compiler)
        if sys.platform == "darwin":
            # XXX need to fix up compiler_so:ccshared + linker_so:ldshared too
            compiler.shared_lib_extension = ".dylib"

        if self.include_dirs is not None:
            compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name,value) tuples
            for (name,value) in self.define:
                compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                compiler.undefine_macro(macro)
        if self.libraries is not None:
            compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            compiler.set_link_objects(self.link_objects)

        # hack so distutils' build_extension() builds a shared lib instead
        #
        def link_shared_object(self, objects, output_libname, output_dir=None,
            libraries=None, library_dirs=None, runtime_library_dirs=None,
            export_symbols=None, debug=0, extra_preargs=None,
            extra_postargs=None, build_temp=None, target_lang=None
        ):  self.link(
                self.SHARED_LIBRARY, objects, output_libname,
                output_dir, libraries, library_dirs, runtime_library_dirs,
                export_symbols, debug, extra_preargs, extra_postargs,
                build_temp, target_lang
            )
        compiler.link_shared_object = link_shared_object.__get__(compiler)

    def get_export_symbols(self, ext):
        if isinstance(ext,SharedLibrary):
            return ext.export_symbols
        return _build_ext.get_export_symbols(self,ext)
        




































