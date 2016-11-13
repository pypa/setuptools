from __future__ import absolute_import, unicode_literals

import textwrap


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
