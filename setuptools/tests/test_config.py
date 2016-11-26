import contextlib
import pytest
from distutils.errors import DistutilsOptionError
from setuptools.dist import Distribution
from setuptools.config import ConfigHandler


class ErrConfigHandler(ConfigHandler):
    """Erroneous handler. Fails to implement required methods."""


def fake_env(tmpdir, setup_cfg, setup_py=None):

    if setup_py is None:
        setup_py = (
            'from setuptools import setup\n'
            'setup()\n'
        )

    tmpdir.join('setup.py').write(setup_py)
    tmpdir.join('setup.cfg').write(setup_cfg)

    package_name = 'fake_package'
    dir_package = tmpdir.mkdir(package_name)
    dir_package.join('__init__.py').write(
        'VERSION = (1, 2, 3)\n'
        '\n'
        'VERSION_MAJOR = 1'
        '\n'
        'def get_version():\n'
        '    return [3, 4, 5, "dev"]\n'
        '\n'
    )


@contextlib.contextmanager
def get_dist(tmpdir, kwargs_initial=None, parse=True):
    kwargs_initial = kwargs_initial or {}

    with tmpdir.as_cwd():
        dist = Distribution(kwargs_initial)
        dist.script_name = 'setup.py'
        parse and dist.parse_config_files()

        yield dist


def test_parsers_implemented():

    with pytest.raises(NotImplementedError):
        handler = ErrConfigHandler(None, {})
        handler.parsers


class TestMetadata:

    def test_basic(self, tmpdir):

        fake_env(
            tmpdir,
            '[metadata]\n'
            'version = 10.1.1\n'
            'description = Some description\n'
            'long_description = file: README\n'
            'name = fake_name\n'
            'keywords = one, two\n'
            'provides = package, package.sub\n'
            'license = otherlic\n'
        )

        tmpdir.join('README').write('readme contents\nline2')

        meta_initial = {
            # This will be used so `otherlic` won't replace it.
            'license': 'BSD 3-Clause License',
        }

        with get_dist(tmpdir, meta_initial) as dist:
            metadata = dist.metadata

            assert metadata.version == '10.1.1'
            assert metadata.description == 'Some description'
            assert metadata.long_description == 'readme contents\nline2'
            assert metadata.provides == ['package', 'package.sub']
            assert metadata.license == 'BSD 3-Clause License'
            assert metadata.name == 'fake_name'
            assert metadata.keywords == ['one', 'two']

    def test_version(self, tmpdir):

        fake_env(
            tmpdir,
            '[metadata]\n'
            'version = attr: fake_package.VERSION\n'
        )
        with get_dist(tmpdir) as dist:
            assert dist.metadata.version == '1.2.3'

        tmpdir.join('setup.cfg').write(
            '[metadata]\n'
            'version = attr: fake_package.get_version\n'
        )
        with get_dist(tmpdir) as dist:
            assert dist.metadata.version == '3.4.5.dev'

        tmpdir.join('setup.cfg').write(
            '[metadata]\n'
            'version = attr: fake_package.VERSION_MAJOR\n'
        )
        with get_dist(tmpdir) as dist:
            assert dist.metadata.version == '1'

        subpack = tmpdir.join('fake_package').mkdir('subpackage')
        subpack.join('__init__.py').write('')
        subpack.join('submodule.py').write('VERSION = (2016, 11, 26)')

        tmpdir.join('setup.cfg').write(
            '[metadata]\n'
            'version = attr: fake_package.subpackage.submodule.VERSION\n'
        )
        with get_dist(tmpdir) as dist:
            assert dist.metadata.version == '2016.11.26'

    def test_unknown_meta_item(self, tmpdir):

        fake_env(
            tmpdir,
            '[metadata]\n'
            'name = fake_name\n'
            'unknown = some\n'
        )
        with get_dist(tmpdir, parse=False) as dist:
            with pytest.raises(DistutilsOptionError):
                dist.parse_config_files()

    def test_usupported_section(self, tmpdir):

        fake_env(
            tmpdir,
            '[metadata:some]\n'
            'key = val\n'
        )
        with get_dist(tmpdir, parse=False) as dist:
            with pytest.raises(DistutilsOptionError):
                dist.parse_config_files()

    def test_classifiers(self, tmpdir):
        expected = set([
            'Framework :: Django',
            'Programming Language :: Python :: 3.5',
        ])

        # From file.
        fake_env(
            tmpdir,
            '[metadata]\n'
            'classifiers = file: classifiers\n'
        )

        tmpdir.join('classifiers').write(
            'Framework :: Django\n'
            'Programming Language :: Python :: 3.5\n'
        )

        with get_dist(tmpdir) as dist:
            assert set(dist.metadata.classifiers) == expected

        # From section.
        tmpdir.join('setup.cfg').write(
            '[metadata:classifiers]\n'
            'Framework :: Django\n'
            'Programming Language :: Python :: 3.5\n'
        )

        with get_dist(tmpdir) as dist:
            assert set(dist.metadata.classifiers) == expected


class TestOptions:

    def test_basic(self, tmpdir):

        fake_env(
            tmpdir,
            '[options]\n'
            'zip_safe = True\n'
            'use_2to3 = 1\n'
            'include_package_data = yes\n'
            'package_dir = b=c, =src\n'
            'packages = pack_a, pack_b.subpack\n'
            'namespace_packages = pack1, pack2\n'
            'use_2to3_fixers = your.fixers, or.here\n'
            'use_2to3_exclude_fixers = one.here, two.there\n'
            'convert_2to3_doctests = src/tests/one.txt, src/two.txt\n'
            'scripts = bin/one.py, bin/two.py\n'
            'eager_resources = bin/one.py, bin/two.py\n'
            'install_requires = docutils>=0.3; pack ==1.1, ==1.3; hey\n'
            'tests_require = mock==0.7.2; pytest\n'
            'setup_requires = docutils>=0.3; spack ==1.1, ==1.3; there\n'
            'dependency_links = http://some.com/here/1, '
                'http://some.com/there/2\n'
        )
        with get_dist(tmpdir) as dist:
            assert dist.zip_safe
            assert dist.use_2to3
            assert dist.include_package_data
            assert dist.package_dir == {'': 'src', 'b': 'c'}
            assert set(dist.packages) == set(['pack_a', 'pack_b.subpack'])
            assert set(dist.namespace_packages) == set(['pack1', 'pack2'])
            assert set(dist.use_2to3_fixers) == set(['your.fixers', 'or.here'])
            assert set(dist.use_2to3_exclude_fixers) == set([
                'one.here', 'two.there'])
            assert set(dist.convert_2to3_doctests) == set([
                'src/tests/one.txt', 'src/two.txt'])
            assert set(dist.scripts) == set(['bin/one.py', 'bin/two.py'])
            assert set(dist.dependency_links) == set([
                'http://some.com/here/1',
                'http://some.com/there/2'
            ])
            assert set(dist.install_requires) == set([
                'docutils>=0.3',
                'pack ==1.1, ==1.3',
                'hey'
            ])
            assert set(dist.setup_requires) == set([
                'docutils>=0.3',
                'spack ==1.1, ==1.3',
                'there'
            ])
            assert set(dist.tests_require) == set([
                'mock==0.7.2',
                'pytest'
            ])

    def test_package_dir_fail(self, tmpdir):
        fake_env(
            tmpdir,
            '[options]\n'
            'package_dir = a b\n'
        )
        with get_dist(tmpdir, parse=False) as dist:
            with pytest.raises(DistutilsOptionError):
                dist.parse_config_files()

    def test_package_data(self, tmpdir):
        fake_env(
            tmpdir,
            '[options:package_data]\n'
            '* = *.txt, *.rst\n'
            'hello = *.msg\n'
            '\n'
            '[options:exclude_package_data]\n'
            '* = fake1.txt, fake2.txt\n'
            'hello = *.dat\n'
        )

        with get_dist(tmpdir) as dist:
            assert dist.package_data == {
                '': ['*.txt', '*.rst'],
                'hello': ['*.msg'],
            }
            assert dist.exclude_package_data == {
                '': ['fake1.txt', 'fake2.txt'],
                'hello': ['*.dat'],
            }

    def test_packages(self, tmpdir):
        fake_env(
            tmpdir,
            '[options]\n'
            'packages = find:\n'
        )

        with get_dist(tmpdir) as dist:
            assert dist.packages == ['fake_package']

    def test_extras_require(self, tmpdir):
        fake_env(
            tmpdir,
            '[options:extras_require]\n'
            'pdf = ReportLab>=1.2; RXP\n'
            'rest = docutils>=0.3; pack ==1.1, ==1.3\n'
        )

        with get_dist(tmpdir) as dist:
            assert dist.extras_require == {
                'pdf': ['ReportLab>=1.2', 'RXP'],
                'rest': ['docutils>=0.3', 'pack ==1.1, ==1.3']
            }

    def test_entry_points(self, tmpdir):
        fake_env(
            tmpdir,
            '[options:entry_points]\n'
            'group1 = point1 = pack.module:func, '
                '.point2 = pack.module2:func_rest [rest]\n'
            'group2 = point3 = pack.module:func2\n'
        )

        with get_dist(tmpdir) as dist:
            assert dist.entry_points == {
                'group1': [
                    'point1 = pack.module:func',
                    '.point2 = pack.module2:func_rest [rest]',
                ],
                'group2': ['point3 = pack.module:func2']
            }

        expected = (
            '[blogtool.parsers]\n'
            '.rst = some.nested.module:SomeClass.some_classmethod[reST]\n'
        )

        tmpdir.join('entry_points').write(expected)

        # From file.
        tmpdir.join('setup.cfg').write(
            '[options]\n'
            'entry_points = file: entry_points\n'
        )

        with get_dist(tmpdir) as dist:
            assert dist.entry_points == expected

    def test_dependency_links(self, tmpdir):
        expected = set([
            'http://some.com/here/1',
            'http://some.com/there/2'
        ])
        # From section.
        fake_env(
            tmpdir,
            '[options:dependency_links]\n'
            '1 = http://some.com/here/1\n'
            '2 = http://some.com/there/2\n'
        )

        with get_dist(tmpdir) as dist:
            assert set(dist.dependency_links) == expected
