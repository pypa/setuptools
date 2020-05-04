import unittest as ut
from ctypes import POINTER
from comtypes.client import CoGetObject
from comtypes.test import requires

requires("time")

# WMI has dual interfaces.
# Some methods/properties have "[out] POINTER(VARIANT)" parameters.
# This test checks that these parameters are returned as strings:
# that's what VARIANT.__ctypes_from_outparam__ does.
class Test(ut.TestCase):
    def test_wmi(self):
        wmi = CoGetObject("winmgmts:")
        disks = wmi.InstancesOf("Win32_LogicalDisk")

        # There are different typelibs installed for WMI on win2k and winXP.
        # WbemScripting refers to their guid:
        #   Win2k:
        #     import comtypes.gen._565783C6_CB41_11D1_8B02_00600806D9B6_0_1_1 as mod
        #   WinXP:
        #     import comtypes.gen._565783C6_CB41_11D1_8B02_00600806D9B6_0_1_2 as mod
        # So, the one that's referenced onm WbemScripting will be used, whether the actual
        # typelib is available or not.  XXX
        from comtypes.gen import WbemScripting
        WbemScripting.wbemPrivilegeCreateToken

        for item in disks:
            # obj[index] is forwarded to obj.Item(index)
            # .Value is a property with "[out] POINTER(VARIANT)" parameter.
            a = item.Properties_["Caption"].Value
            b = item.Properties_.Item("Caption").Value
            c = item.Properties_("Caption").Value
            self.assertEqual(a, b)
            self.assertEqual(a, c)
            self.assertTrue(isinstance(a, str))
            self.assertTrue(isinstance(b, str))
            self.assertTrue(isinstance(c, str))
            result = {}
            for prop in item.Properties_:
                self.assertTrue(isinstance(prop.Name, str))
                prop.Value
                result[prop.Name] = prop.Value
##                print "\t", (prop.Name, prop.Value)
            self.assertEqual(len(item.Properties_), item.Properties_.Count)
            self.assertEqual(len(item.Properties_), len(result))
            self.assertTrue(isinstance(item.Properties_["Description"].Value, str))
        # len(obj) is forwared to obj.Count
        self.assertEqual(len(disks), disks.Count)

if __name__ == "__main__":
    ut.main()
