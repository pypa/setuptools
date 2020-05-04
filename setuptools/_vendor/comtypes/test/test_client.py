import unittest as ut
import comtypes.client
from comtypes import COSERVERINFO
from ctypes import POINTER, byref

# create the typelib wrapper and import it
comtypes.client.GetModule("scrrun.dll")
from comtypes.gen import Scripting

import comtypes.test
comtypes.test.requires("ui")

class Test(ut.TestCase):
    def test_progid(self):
        # create from ProgID
        obj = comtypes.client.CreateObject("Scripting.Dictionary")
        self.assertTrue(isinstance(obj, POINTER(Scripting.IDictionary)))

    def test_clsid(self):
        # create from the CoClass' clsid
        obj = comtypes.client.CreateObject(Scripting.Dictionary)
        self.assertTrue(isinstance(obj, POINTER(Scripting.IDictionary)))

    def test_clsid_string(self):
        # create from string clsid
        comtypes.client.CreateObject(str(Scripting.Dictionary._reg_clsid_))
        comtypes.client.CreateObject(str(Scripting.Dictionary._reg_clsid_))

    def test_remote(self):
        ie = comtypes.client.CreateObject("InternetExplorer.Application",
                                          machine="localhost")
        self.assertEqual(ie.Visible, False)
        ie.Visible = 1
        # on a remote machine, this may not work.  Probably depends on
        # how the server is run.
        self.assertEqual(ie.Visible, True)
        self.assertEqual(0, ie.Quit()) # 0 == S_OK

    def test_server_info(self):
        serverinfo = COSERVERINFO()
        serverinfo.pwszName = 'localhost'
        pServerInfo = byref(serverinfo)

        self.assertRaises(ValueError, comtypes.client.CreateObject,
                "InternetExplorer.Application", machine='localhost',
                pServerInfo=pServerInfo)
        ie = comtypes.client.CreateObject("InternetExplorer.Application",
                                          pServerInfo=pServerInfo)
        self.assertEqual(ie.Visible, False)
        ie.Visible = 1
        # on a remote machine, this may not work.  Probably depends on
        # how the server is run.
        self.assertEqual(ie.Visible, True)
        self.assertEqual(0, ie.Quit()) # 0 == S_OK

def test_main():
    from test import test_support
    test_support.run_unittest(Test)

if __name__ == "__main__":
    ut.main()
