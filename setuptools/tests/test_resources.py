from unittest import TestCase, makeSuite
from pkg_resources import *
import pkg_resources

class DistroTests(TestCase):
    def testEmptyiter(self):
        # empty path should produce no distributions
        self.assertEqual(list(iter_distributions(path=[])), [])

class ParseTests(TestCase):
    def testEmptyParse(self):
        self.assertEqual(list(parse_requirements('')), [])

    def testYielding(self):
        for inp,out in [
            ([], []), ('x',['x']), ([[]],[]), (' x\n y', ['x','y']),
            (['x\n\n','y'], ['x','y']),
        ]:
            self.assertEqual(list(pkg_resources.yield_lines(inp)),out)

    def testSimple(self):
        self.assertEqual(
            list(parse_requirements('Twis-Ted>=1.2')),
            [('Twis_Ted',[('>=','1.2')])]
        )
        self.assertEqual(
            list(parse_requirements('Twisted >=1.2, \ # more\n<2.0')),
            [('Twisted',[('>=','1.2'),('<','2.0')])]
        )
        self.assertRaises(ValueError,lambda:list(parse_requirements(">=2.3")))
        self.assertRaises(ValueError,lambda:list(parse_requirements("x\\")))
        self.assertRaises(ValueError,lambda:list(parse_requirements("x==2 q")))

