"""Test .dist-info style distributions.
"""
import os
import shutil
import tempfile

from setuptools.extern.six.moves import map

import pytest

import pkg_resources
from .textwrap import DALS


class TestDistInfo:

    metadata_template = DALS("""
        Metadata-Version: 1.2
        Name: {name}
        {version}
        Requires-Dist: splort (==4)
        Provides-Extra: baz
        Requires-Dist: quux (>=1.1); extra == 'baz'
        """)

    @pytest.fixture
    def metadata(self, tmpdir):
        dist_info_name = 'VersionedDistribution-2.718.dist-info'
        versioned = tmpdir / dist_info_name
        versioned.mkdir()
        filename = versioned / 'METADATA'
        content = self.metadata_template.format(
            name='VersionedDistribution',
            version='',
        ).replace('\n\n', '\n')
        filename.write_text(content, encoding='utf-8')

        dist_info_name = 'UnversionedDistribution.dist-info'
        unversioned = tmpdir / dist_info_name
        unversioned.mkdir()
        filename = unversioned / 'METADATA'
        content = self.metadata_template.format(
            name='UnversionedDistribution',
            version='Version: 0.3',
        )
        filename.write_text(content, encoding='utf-8')

        return str(tmpdir)

    def test_distinfo(self, metadata):
        dists = dict(
            (d.project_name, d)
            for d in pkg_resources.find_distributions(metadata)
        )

        assert len(dists) == 2, dists

        unversioned = dists['UnversionedDistribution']
        versioned = dists['VersionedDistribution']

        assert versioned.version == '2.718'  # from filename
        assert unversioned.version == '0.3'  # from METADATA

    def test_conditional_dependencies(self, metadata):
        specs = 'splort==4', 'quux>=1.1'
        requires = list(map(pkg_resources.Requirement.parse, specs))

        for d in pkg_resources.find_distributions(metadata):
            assert d.requires() == requires[:1]
            assert d.requires(extras=('baz',)) == [
                requires[0],
                pkg_resources.Requirement.parse('quux>=1.1;extra=="baz"'),
            ]
            assert d.extras == ['baz']
