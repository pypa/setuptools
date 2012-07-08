"""Test .dist-info style distributions.
"""
import os, shutil, tempfile, unittest
import pkg_resources
from pkg_resources import Requirement

class TestDistInfo(unittest.TestCase):

    def test_distinfo(self):
        dists = {}
        for d in pkg_resources.find_distributions(self.tmpdir):
            dists[d.project_name] = d
            
        unversioned = dists['UnversionedDistribution']
        versioned = dists['VersionedDistribution']
        
        assert versioned.version == '2.718' # from filename        
        assert unversioned.version == '0.3' # from METADATA
        
        requires = [Requirement.parse('splort==4'), 
                    Requirement.parse('quux>=1.1')]
        
        for d in (unversioned, versioned):
            self.assertEquals(d.requires(), requires[:1])
            self.assertEquals(d.requires(extras=('baz',)), requires)
            self.assertEquals(d.extras, ['baz'])

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        versioned = os.path.join(self.tmpdir, 
                                 'VersionedDistribution-2.718.dist-info')
        os.mkdir(versioned)
        open(os.path.join(versioned, 'METADATA'), 'w+').write(
"""Metadata-Version: 1.2
Name: VersionedDistribution
Requires-Dist: splort (4)
Provides-Extra: baz
Requires-Dist: quux (>=1.1); extra == 'baz'
""")

        unversioned = os.path.join(self.tmpdir, 
                                   'UnversionedDistribution.dist-info')
        os.mkdir(unversioned)
        open(os.path.join(unversioned, 'METADATA'), 'w+').write(
"""Metadata-Version: 1.2
Name: UnversionedDistribution
Version: 0.3
Requires-Dist: splort (==4)
Provides-Extra: baz
Requires-Dist: quux (>=1.1); extra == 'baz'
""")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

