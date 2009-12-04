"""develop tests
"""
import sys
import os
import shutil
import unittest
import tempfile

from setuptools.sandbox import DirectorySandbox

class TestSandbox(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_devnull(self):
        sandbox = DirectorySandbox(self.dir)

        def _write():
            f = open(os.devnull, 'w')
            f.write('xxx')
            f.close()

        sandbox.run(_write)

