import os
import unittest
from comtypes import GUID

class Test(unittest.TestCase):
    def test(self):
        self.assertEqual(GUID(), GUID())
        self.assertEqual(GUID("{00000000-0000-0000-C000-000000000046}"),
                             GUID("{00000000-0000-0000-C000-000000000046}"))

        self.assertEqual(str(GUID("{0002DF01-0000-0000-C000-000000000046}")),
                             "{0002DF01-0000-0000-C000-000000000046}")
        self.assertEqual(repr(GUID("{0002DF01-0000-0000-C000-000000000046}")),
                             'GUID("{0002DF01-0000-0000-C000-000000000046}")')

        self.assertRaises(WindowsError, GUID, "abc")
        self.assertRaises(WindowsError, GUID.from_progid, "abc")

        self.assertRaises(WindowsError, lambda guid: guid.as_progid(),
                          GUID("{00000000-0000-0000-C000-000000000046}"))


        if os.name == "nt":
            self.assertEqual(GUID.from_progid("InternetExplorer.Application"),
                                 GUID("{0002DF01-0000-0000-C000-000000000046}"))
            self.assertEqual(GUID("{0002DF01-0000-0000-C000-000000000046}").as_progid(),
                                 'InternetExplorer.Application.1')
        elif os.name == "ce":
            self.assertEqual(GUID.from_progid("JScript"),
                                 GUID("{f414c260-6ac0-11cf-b6d1-00aa00bbbb58}"))
            self.assertEqual(GUID("{f414c260-6ac0-11cf-b6d1-00aa00bbbb58}").as_progid(),
                                 'JScript')


        self.assertNotEqual(GUID.create_new(), GUID.create_new())

if __name__ == "__main__":
    unittest.main()
