"""Test .dist-info style distributions.
"""
import os
import shutil
import tempfile
import textwrap

import pytest

import pkg_resources

def DALS(s):
    "dedent and left-strip"
    return textwrap.dedent(s).lstrip()

class TestDistInfo:

    def test_distinfo(self):
        dists = {}
        for d in pkg_resources.find_distributions(self.tmpdir):
            dists[d.project_name] = d

        assert len(dists) == 2, dists

        unversioned = dists['UnversionedDistribution']
        versioned = dists['VersionedDistribution']

        assert versioned.version == '2.718' # from filename
        assert unversioned.version == '0.3' # from METADATA

    @pytest.mark.importorskip('ast')
    def test_conditional_dependencies(self):
        requires = [pkg_resources.Requirement.parse('splort==4'),
                    pkg_resources.Requirement.parse('quux>=1.1')]

        for d in pkg_resources.find_distributions(self.tmpdir):
            assert d.requires() == requires[:1]
            assert d.requires(extras=('baz',)) == requires
            assert d.extras == ['baz']

    def setup_method(self, method):
        self.tmpdir = tempfile.mkdtemp()
        versioned = os.path.join(self.tmpdir,
                                 'VersionedDistribution-2.718.dist-info')
        os.mkdir(versioned)
        with open(os.path.join(versioned, 'METADATA'), 'w+') as metadata_file:
            metadata_file.write(DALS(
                """
                Metadata-Version: 1.2
                Name: VersionedDistribution
                Requires-Dist: splort (4)
                Provides-Extra: baz
                Requires-Dist: quux (>=1.1); extra == 'baz'
                """))
        unversioned = os.path.join(self.tmpdir,
                                   'UnversionedDistribution.dist-info')
        os.mkdir(unversioned)
        with open(os.path.join(unversioned, 'METADATA'), 'w+') as metadata_file:
            metadata_file.write(DALS(
                """
                Metadata-Version: 1.2
                Name: UnversionedDistribution
                Version: 0.3
                Requires-Dist: splort (==4)
                Provides-Extra: baz
                Requires-Dist: quux (>=1.1); extra == 'baz'
                """))

    def teardown_method(self, method):
        shutil.rmtree(self.tmpdir)
