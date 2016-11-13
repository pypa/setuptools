from __future__ import absolute_import

import os
import textwrap
import sys
import subprocess


class TestNamespaces:
    @staticmethod
    def build_namespace_package(tmpdir, name):
        src_dir = tmpdir / name
        src_dir.mkdir()
        setup_py = src_dir / 'setup.py'
        namespace, sep, rest = name.partition('.')
        script = textwrap.dedent("""
            import setuptools
            setuptools.setup(
                name={name!r},
                version="1.0",
                namespace_packages=[{namespace!r}],
                packages=[{namespace!r}],
            )
            """).format(**locals())
        setup_py.write_text(script, encoding='utf-8')
        ns_pkg_dir = src_dir / namespace
        ns_pkg_dir.mkdir()
        pkg_init = ns_pkg_dir / '__init__.py'
        tmpl = '__import__("pkg_resources").declare_namespace({namespace!r})'
        decl = tmpl.format(**locals())
        pkg_init.write_text(decl, encoding='utf-8')
        pkg_mod = ns_pkg_dir / (rest + '.py')
        some_functionality = 'name = {rest!r}'.format(**locals())
        pkg_mod.write_text(some_functionality, encoding='utf-8')
        return src_dir

    @staticmethod
    def make_site_dir(target):
        """
        Add a sitecustomize.py module in target to cause
        target to be added to site dirs such that .pth files
        are processed there.
        """
        sc = target / 'sitecustomize.py'
        target_str = str(target)
        tmpl = '__import__("site").addsitedir({target_str!r})'
        sc.write_text(tmpl.format(**locals()), encoding='utf-8')

    def test_mixed_site_and_non_site(self, tmpdir):
        """
        Installing two packages sharing the same namespace, one installed
        to a site dir and the other installed just to a path on PYTHONPATH
        should leave the namespace in tact and both packages reachable by
        import.
        """
        pkg_A = self.build_namespace_package(tmpdir, 'myns.pkgA')
        pkg_B = self.build_namespace_package(tmpdir, 'myns.pkgB')
        site_packages = tmpdir / 'site-packages'
        path_packages = tmpdir / 'path-packages'
        targets = site_packages, path_packages
        python_path = os.pathsep.join(map(str, targets))
        # use pip to install to the target directory
        install_cmd = [
            'pip',
            'install',
            str(pkg_A),
            '-t', str(site_packages),
        ]
        subprocess.check_call(install_cmd)
        self.make_site_dir(site_packages)
        install_cmd = [
            'pip',
            'install',
            str(pkg_B),
            '-t', str(path_packages),
        ]
        subprocess.check_call(install_cmd)
        try_import = [
            sys.executable,
            '-c', 'import myns.pkgA; import myns.pkgB',
        ]
        env = dict(PYTHONPATH=python_path)
        subprocess.check_call(try_import, env=env)
