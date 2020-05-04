import unittest
from comtypes.client import CreateObject
from comtypes.test.find_memleak import find_memleak

class Test(unittest.TestCase):
    "Test COM records"
    def test(self):
        # The ATL COM dll
        avmc = CreateObject("AvmcIfc.Avmc.1")

        # This returns an array (a list) of DeviceInfo records.
        devs = avmc.FindAllAvmc()
        
        self.assertEqual(devs[0].Flags, 12)
        self.assertEqual(devs[0].ID, 13)
        self.assertEqual(devs[0].LocId, 14)
        self.assertEqual(devs[0].Description, "Avmc")
        self.assertEqual(devs[0].SerialNumber, "1234")

        self.assertEqual(devs[1].Flags, 22)
        self.assertEqual(devs[1].ID, 23)
        self.assertEqual(devs[1].LocId, 24)
        self.assertEqual(devs[1].Description, "Avmc2")
        self.assertEqual(devs[1].SerialNumber, "5678")

##        # Leaks... where?
##        def doit():
##            avmc.FindAllAvmc()
##        self.check_leaks(doit)

    def check_leaks(self, func, limit=0):
        bytes = find_memleak(func)
        self.assertFalse(bytes > limit, "Leaks %d bytes" % bytes)

if __name__ == "__main__":
    unittest.main()
