import os
from distutils import log
import itertools

from setuptools.extern.six.moves import map


flatten = itertools.chain.from_iterable


class Installer:

    nspkg_ext = '-nspkg.pth'

    def install_namespaces(self):
        nsp = self._get_all_ns_packages()
        if not nsp:
            return
        filename, ext = os.path.splitext(self._get_target())
        filename += self.nspkg_ext
        self.outputs.append(filename)
        log.info("Installing %s", filename)
        lines = map(self._gen_nspkg_line, nsp)

        if self.dry_run:
            # always generate the lines, even in dry run
            list(lines)
            return

        with open(filename, 'wt') as f:
            f.writelines(lines)

    def _get_target(self):
        return self.target

    @staticmethod
    def init(root, pkg):
        import sys, types
        pep420 = sys.version_info > (3, 3)
        pth = tuple(pkg.split('.'))
        p = os.path.join(root, *pth)
        ie = os.path.exists(os.path.join(p, '__init__.py'))
        m = not ie and not pep420 and sys.modules.setdefault(pkg,
            types.ModuleType(pkg))
        mp = (m or []) and m.__dict__.setdefault('__path__', [])
        (p not in mp) and mp.append(p)
        parent, sep, child = pkg.rpartition('.')
        m and parent and setattr(sys.modules[parent], child, m)
    _nspkg_tmpl = (
        "import setuptools.namespaces",
        "setuptools.namespaces.Installer.init(%(root)r, %(pkg)r)",
    )
    "lines for the namespace installer"

    def _get_root(self):
        return "sys._getframe(1).f_locals['sitedir']"

    def _gen_nspkg_line(self, pkg):
        # ensure pkg is not a unicode string under Python 2.7
        pkg = str(pkg)
        root = self._get_root()
        return ';'.join(self._nspkg_tmpl) % locals() + '\n'

    def _get_all_ns_packages(self):
        """Return sorted list of all package namespaces"""
        pkgs = self.distribution.namespace_packages or []
        return sorted(flatten(map(self._pkg_names, pkgs)))

    @staticmethod
    def _pkg_names(pkg):
        """
        Given a namespace package, yield the components of that
        package.

        >>> names = Installer._pkg_names('a.b.c')
        >>> set(names) == set(['a', 'a.b', 'a.b.c'])
        True
        """
        parts = pkg.split('.')
        while parts:
            yield '.'.join(parts)
            parts.pop()


class DevelopInstaller(Installer):
    def _get_root(self):
        return repr(str(self.egg_path))

    def _get_target(self):
        return self.egg_link
