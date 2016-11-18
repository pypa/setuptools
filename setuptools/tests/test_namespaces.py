from __future__ import absolute_import, unicode_literals

import os
import sys
import subprocess

import pytest

from . import namespaces


class TestNamespaces:

    @pytest.mark.xfail(sys.version_info < (3, 3),
        reason="Requires PEP 420")
    @pytest.mark.skipif('os.environ.get("APPVEYOR")',
        reason="https://github.com/pypa/setuptools/issues/851")
    def test_mixed_site_and_non_site(self, tmpdir):
        """
        Installing two packages sharing the same namespace, one installed
        to a site dir and the other installed just to a path on PYTHONPATH
        should leave the namespace in tact and both packages reachable by
        import.
        """
        pkg_A = namespaces.build_namespace_package(tmpdir, 'myns.pkgA')
        pkg_B = namespaces.build_namespace_package(tmpdir, 'myns.pkgB')
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
        namespaces.make_site_dir(site_packages)
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
