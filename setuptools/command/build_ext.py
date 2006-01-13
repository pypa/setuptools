from distutils.command.build_ext import build_ext as _du_build_ext
try:
    # Attempt to use Pyrex for building extensions, if available
    from Pyrex.Distutils.build_ext import build_ext as _build_ext
except ImportError:
    _build_ext = _du_build_ext

import os, sys
from distutils.file_util import copy_file
from setuptools.extension import Library
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler

have_rtld = False
libtype = 'shared'
if os.name != 'nt':
    try:
        from dl import RTLD_NOW
        have_rtld = True
    except ImportError:
        pass




















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
        ext = self.ext_map[fullname]
        if isinstance(ext,Library):
            fn, ext = os.path.splitext(filename)
            return self.shlib_compiler.library_filename(fn,libtype)
        elif have_rtld and ext.links_to_dynamic:
            d,fn = os.path.split(filename)
            return os.path.join(d,'dl-'+fn)
        else:
            return filename

    def initialize_options(self):
        _build_ext.initialize_options(self)
        self.shlib_compiler = None
        self.shlibs = []
        self.ext_map = {}

    def finalize_options(self):
        _build_ext.finalize_options(self)
        self.check_extensions_list(self.extensions)
        self.shlibs = [ext for ext in self.extensions or ()
                        if isinstance(ext,Library)]
        if self.shlibs:
            self.setup_shlib_compiler()
        for ext in self.extensions:
            fullname = ext._full_name = self.get_ext_fullname(ext.name)
            self.ext_map[fullname] = ext
            filename = ext._file_name = self.get_ext_filename(fullname)
            ltd = ext._links_to_dynamic = \
                self.shlibs and self.links_to_dynamic(ext) or False
            ext._needs_stub = ltd and have_rtld and not isinstance(ext,Library)
            libdir = os.path.dirname(os.path.join(self.build_lib,filename))
            if ltd and libdir not in ext.library_dirs:
                ext.library_dirs.append(libdir)
            if ltd and have_rtld and os.curdir not in ext.runtime_library_dirs:
                ext.runtime_library_dirs.append(os.curdir)




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

        # hack so distutils' build_extension() builds a library instead
        compiler.link_shared_object = link_shared_object.__get__(compiler)

    def get_export_symbols(self, ext):
        if isinstance(ext,Library):
            return ext.export_symbols
        return _build_ext.get_export_symbols(self,ext)
        






    def build_extension(self, ext):
        _compiler = self.compiler
        try:
            if isinstance(ext,Library):
                self.compiler = self.shlib_compiler
            _build_ext.build_extension(self,ext)
            if ext._needs_stub:
                self.write_stub(ext)
        finally:
            self.compiler = _compiler

    def write_stub(self, ext):
        log.info("writing stub loader for %s",ext._full_name)
        stub_file = os.path.join(self.build_lib, *ext._full_name.split('.'))
        stub_file += '.py'
        if not self.dry_run:
            f = open(stub_file,'w')
            f.write('\n'.join([
                "def __bootstrap__():",
                "   global __bootstrap__, __file__, __loader__",
                "   import sys, os, pkg_resources, imp, dl",
                "   __file__ = pkg_resources.resource_filename(__name__,%r)"
                   % os.path.basename(ext._file_name),
                "   del __bootstrap__",
                "   if '__loader__' in globals():",
                "       del __loader__",
                "   old_flags = sys.getdlopenflags()",
                "   old_dir = os.getcwd()",
                "   try:",
                "     os.chdir(os.path.dirname(__file__))",
                "     sys.setdlopenflags(dl.RTLD_NOW)",
                "     imp.load_dynamic(__name__,__file__)",
                "   finally:",
                "     sys.setdlopenflags(old_flags)",
                "     os.chdir(old_dir)",
                "__bootstrap__()",
                "" # terminal \n
            ]))
            f.close()
        self.get_finalized_command('build_py').byte_compile(stub_file)

    def links_to_dynamic(self, ext):
        """Return true if 'ext' links to a dynamic lib in the same package"""
        # XXX this should check to ensure the lib is actually being built
        # XXX as dynamic, and not just using a locally-found version or a
        # XXX static-compiled version
        libnames = dict.fromkeys([lib._full_name for lib in self.shlibs])
        pkg = '.'.join(ext._full_name.split('.')[:-1]+[''])
        for libname in ext.libraries:
            if pkg+libname in libnames: return True
        return False

    def get_outputs(self):
        outputs = _build_ext.get_outputs(self)
        optimize = self.get_finalized_command('build_py').optimize
        for ext in self.extensions:
            if ext._needs_stub:
                base = os.path.join(self.build_lib, *ext._full_name.split('.'))
                outputs.append(base+'.py')
                outputs.append(base+'.pyc')
                if optimize:
                    outputs.append(base+'.pyo')
        return outputs



















if have_rtld or os.name=='nt':
    # Build shared libraries
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
else:
    # Build static libraries everywhere else
    libtype = 'static'

    def link_shared_object(self, objects, output_libname, output_dir=None,
        libraries=None, library_dirs=None, runtime_library_dirs=None,
        export_symbols=None, debug=0, extra_preargs=None,
        extra_postargs=None, build_temp=None, target_lang=None
    ):
        # XXX we need to either disallow these attrs on Library instances,
        #     or warn/abort here if set, or something...
        #libraries=None, library_dirs=None, runtime_library_dirs=None,
        #export_symbols=None, extra_preargs=None, extra_postargs=None,
        #build_temp=None

        assert output_dir is None   # distutils build_ext doesn't pass this       
        output_dir,filename = os.path.split(output_libname)
        basename, ext = os.path.splitext(filename)
        if self.library_filename("x").startswith('lib'):
            # strip 'lib' prefix; this is kludgy if some platform uses
            # a different prefix
            basename = basename[3:] 

        self.create_static_lib(
            objects, basename, output_dir, debug, target_lang
        )


