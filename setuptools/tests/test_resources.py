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









    def testVersionOrdering(self):
        def c(s1,s2):
            p1, p2 = parse_version(s1),parse_version(s2)
            self.failUnless(p1<p2, (s1,s2,p1,p2))

        c('2.1','2.1.1')
        c('2a1','2b0')        
        c('2a1','2.1')        
        c('2.3a1', '2.3')
        c('2.1-1', '2.1-2')
        c('2.1-1', '2.1.1')
        c('2.1', '2.1pl4')
        c('2.1a0-20040501', '2.1')
        c('1.1', '02.1')
        c('A56','B27')
        c('3.2', '3.2.pl0')
        c('3.2-1', '3.2pl1')
        c('3.2pl1', '3.2pl1-1')
        c('0.4', '4.0')
        c('0.0.4', '0.4.0')
        c('0pl1', '0.4pl1')


    def testVersionEquality(self):
        def c(s1,s2):
            p1, p2 = parse_version(s1),parse_version(s2)
            self.assertEqual(p1,p2, (s1,s2,p1,p2))
        
        c('0.4', '0.4.0')
        c('0.4.0.0', '0.4.0')
        c('0.4.0-0', '0.4-0')
        c('0pl1', '0.0pl1')
        c('0pre1', '0.0c1')
        c('0.0.0preview1', '0c1')
        c('0.0c1', '0rc1')

        













