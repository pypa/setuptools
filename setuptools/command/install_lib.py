import distutils.command.install_lib as orig
import os, imp
from itertools import product

class install_lib(orig.install_lib):
    """Don't add compiled flags to filenames of non-Python files"""

    def run(self):
        self.build()
        outfiles = self.install()
        if outfiles is not None:
            # always compile, in case we have any extension stubs to deal with
            self.byte_compile(outfiles)

    def get_exclusions(self):
        """
        Return a collections.Sized collections.Container of paths to be
        excluded for single_version_externally_managed installations.
        """
        exclude = set()
        pkg_path = lambda pkg: os.path.join(self.install_dir, *pkg.split('.'))
        all_packages = (
            pkg
            for ns_pkg in self._get_SVEM_NSPs()
            for pkg in self._all_packages(ns_pkg)
        )
        for pkg, f in product(all_packages, self._gen_exclude_names()):
            exclude.add(os.path.join(pkg_path(pkg), f))
        return exclude

    @staticmethod
    def _all_packages(pkg_name):
        """
        >>> list(install_lib._all_packages('foo.bar.baz'))
        ['foo.bar.baz', 'foo.bar', 'foo']
        """
        while pkg_name:
            yield pkg_name
            pkg_name, sep, child = pkg_name.partition('.')

    def _get_SVEM_NSPs(self):
        """
        Get namespace packages (list) but only for
        single_version_externally_managed installations and empty otherwise.
        """
        # TODO: is it necessary to short-circuit here? i.e. what's the cost
        # if get_finalized_command is called even when namespace_packages is
        # False?
        if not self.distribution.namespace_packages:
            return []

        install_cmd = self.get_finalized_command('install')
        svem = install_cmd.single_version_externally_managed

        return self.distribution.namespace_packages if svem else []

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
