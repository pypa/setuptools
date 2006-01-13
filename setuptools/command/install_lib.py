from distutils.command.install_lib import install_lib as _install_lib

class install_lib(_install_lib):
    """Don't add compiled flags to filenames of non-Python files"""

    def _bytecode_filenames (self, py_filenames):
        bytecode_files = []
        for py_file in py_filenames:
            if not py_file.endswith('.py'):
                continue
            if self.compile:
                bytecode_files.append(py_file + "c")
            if self.optimize > 0:
                bytecode_files.append(py_file + "o")

        return bytecode_files


    def run(self):
        self.build()
        outfiles = self.install()
        if outfiles is not None:
            # always compile, in case we have any extension stubs to deal with
            self.byte_compile(outfiles) 

