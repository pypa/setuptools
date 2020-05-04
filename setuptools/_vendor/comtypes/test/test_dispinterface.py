import unittest

from comtypes.server.register import register#, unregister
from comtypes.test import is_resource_enabled

################################################################
import comtypes.test.TestDispServer
register(comtypes.test.TestDispServer.TestDispServer)

class Test(unittest.TestCase):

    if is_resource_enabled("pythoncom"):
        def test_win32com(self):
            # EnsureDispatch is case-sensitive
            from win32com.client.gencache import EnsureDispatch
            d = EnsureDispatch("TestDispServerLib.TestDispServer")

            self.assertEqual(d.eval("3.14"), 3.14)
            self.assertEqual(d.eval("1 + 2"), 3)
            self.assertEqual(d.eval("[1 + 2, 'foo', None]"), (3, 'foo', None))

            self.assertEqual(d.eval2("3.14"), 3.14)
            self.assertEqual(d.eval2("1 + 2"), 3)
            self.assertEqual(d.eval2("[1 + 2, 'foo', None]"), (3, 'foo', None))

            d.eval("__import__('comtypes.client').client.CreateObject('Scripting.Dictionary')")

            server_id = d.eval("id(self)")
            self.assertEqual(d.id, server_id)

            self.assertEqual(d.name, "spam, spam, spam")

            d.SetName("foo bar")
            self.assertEqual(d.name, "foo bar")

            d.name = "blah"
            self.assertEqual(d.name, "blah")

        def test_win32com_dyndispatch(self):
            # dynamic Dispatch is case-IN-sensitive
            from win32com.client.dynamic import Dispatch
            d = Dispatch("TestDispServerLib.TestDispServer")

            self.assertEqual(d.eval("3.14"), 3.14)
            self.assertEqual(d.eval("1 + 2"), 3)
            self.assertEqual(d.eval("[1 + 2, 'foo', None]"), (3, 'foo', None))

            self.assertEqual(d.eval2("3.14"), 3.14)
            self.assertEqual(d.eval2("1 + 2"), 3)
            self.assertEqual(d.eval2("[1 + 2, 'foo', None]"), (3, 'foo', None))

            d.eval("__import__('comtypes.client').client.CreateObject('Scripting.Dictionary')")

            self.assertEqual(d.EVAL("3.14"), 3.14)
            self.assertEqual(d.EVAL("1 + 2"), 3)
            self.assertEqual(d.EVAL("[1 + 2, 'foo', None]"), (3, 'foo', None))

            self.assertEqual(d.EVAL2("3.14"), 3.14)
            self.assertEqual(d.EVAL2("1 + 2"), 3)
            self.assertEqual(d.EVAL2("[1 + 2, 'foo', None]"), (3, 'foo', None))

            server_id = d.eval("id(self)")
            self.assertEqual(d.id, server_id)
            self.assertEqual(d.ID, server_id)

            self.assertEqual(d.Name, "spam, spam, spam")
            self.assertEqual(d.nAME, "spam, spam, spam")

            d.SetName("foo bar")
            self.assertEqual(d.Name, "foo bar")

            # fails.  Why?
##            d.name = "blah"
##            self.assertEqual(d.Name, "blah")

    def test_comtypes(self):
        from comtypes.client import CreateObject
        d = CreateObject("TestDispServerLib.TestDispServer")

        self.assertEqual(d.eval("3.14"), 3.14)
        self.assertEqual(d.eval("1 + 2"), 3)
        self.assertEqual(d.eval("[1 + 2, 'foo', None]"), (3, 'foo', None))

        self.assertEqual(d.eval2("3.14"), 3.14)
        self.assertEqual(d.eval2("1 + 2"), 3)
        self.assertEqual(d.eval2("[1 + 2, 'foo', None]"), (3, 'foo', None))

        d.eval("__import__('comtypes.client').client.CreateObject('Scripting.Dictionary')")

        self.assertEqual(d.EVAL("3.14"), 3.14)
        self.assertEqual(d.EVAL("1 + 2"), 3)
        self.assertEqual(d.EVAL("[1 + 2, 'foo', None]"), (3, 'foo', None))

        self.assertEqual(d.EVAL2("3.14"), 3.14)
        self.assertEqual(d.EVAL2("1 + 2"), 3)
        self.assertEqual(d.EVAL2("[1 + 2, 'foo', None]"), (3, 'foo', None))

        server_id = d.eval("id(self)")
        self.assertEqual(d.id, server_id)
        self.assertEqual(d.ID, server_id)

        self.assertEqual(d.Name, "spam, spam, spam")
        self.assertEqual(d.nAME, "spam, spam, spam")

        d.SetName("foo bar")
        self.assertEqual(d.Name, "foo bar")

        d.name = "blah"
        self.assertEqual(d.Name, "blah")

    def test_withjscript(self):
        import os
        jscript = os.path.join(os.path.dirname(__file__), "test_jscript.js")
        errcode = os.system("cscript -nologo %s" % jscript)
        self.assertEqual(errcode, 0)

if __name__ == "__main__":
    unittest.main()
