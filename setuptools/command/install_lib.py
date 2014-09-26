import distutils.command.install_lib as orig
import os, imp

class install_lib(orig.install_lib):
    """Don't add compiled flags to filenames of non-Python files"""

    def run(self):
        self.build()
        outfiles = self.install()
        if outfiles is not None:
            # always compile, in case we have any extension stubs to deal with
            self.byte_compile(outfiles)

    def get_exclusions(self):
        exclude = set()
        nsp = self.distribution.namespace_packages
        svem = (nsp and self.get_finalized_command('install')
                .single_version_externally_managed)
        if svem:
            for pkg in nsp:
                parts = pkg.split('.')
                while parts:
                    pkgdir = os.path.join(self.install_dir, *parts)
                    for f in self._gen_exclude_names():
                        exclude.add(os.path.join(pkgdir, f))
                    parts.pop()
        return dict.fromkeys(exclude, 1)

    @staticmethod
    def _gen_exclude_names():
        """
        Generate file paths to be excluded for namespace packages (bytecode
        cache files).
        """
        # always exclude the package module itself
        yield '__init__.py'

        yield '__init__.pyc'
        yield '__init__.pyo'

        if not hasattr(imp, 'get_tag'):
            return

        base = os.path.join('__pycache__', '__init__.' + imp.get_tag())
        yield base + '.pyc'
        yield base + '.pyo'

    def copy_tree(
            self, infile, outfile,
            preserve_mode=1, preserve_times=1, preserve_symlinks=0, level=1
    ):
        assert preserve_mode and preserve_times and not preserve_symlinks
        exclude = self.get_exclusions()

        if not exclude:
            return orig.install_lib.copy_tree(self, infile, outfile)

        # Exclude namespace package __init__.py* files from the output

        from setuptools.archive_util import unpack_directory
        from distutils import log

        outfiles = []

        def pf(src, dst):
            if dst in exclude:
                log.warn("Skipping installation of %s (namespace package)",
                         dst)
                return False

            log.info("copying %s -> %s", src, os.path.dirname(dst))
            outfiles.append(dst)
            return dst

        unpack_directory(infile, outfile, pf)
        return outfiles

    def get_outputs(self):
        outputs = orig.install_lib.get_outputs(self)
        exclude = self.get_exclusions()
        if exclude:
            return [f for f in outputs if f not in exclude]
        return outputs
