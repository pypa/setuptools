import unittest

import comtypes
import comtypes.client

import comtypes.test
comtypes.test.requires("ui")

class Test(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "w1"):
            self.w1.Quit()
            del self.w1


    def test(self):
        try:
            comtypes.client.GetActiveObject("Word.Application")
        except WindowsError:
            pass
        else:
            # seems word is running, we cannot test this.
            self.fail("MSWord is running, cannot test")

        # create a WORD instance
        self.w1 = w1 = comtypes.client.CreateObject("Word.Application")
        # connect to the running instance
        w2 = comtypes.client.GetActiveObject("Word.Application")

        # check if they are referring to the same object
        self.assertEqual(w1.QueryInterface(comtypes.IUnknown),
                             w2.QueryInterface(comtypes.IUnknown))

        w1.Quit()
        del self.w1

        import time
        time.sleep(1)

        try:
            w2.Visible
        except comtypes.COMError as err:
            variables = err.hresult, err.text, err.details
            self.assertEqual(variables, err[:])
        else:
            raise AssertionError("COMError not raised")

        self.assertRaises(WindowsError, comtypes.client.GetActiveObject, "Word.Application")


if __name__ == "__main__":
    unittest.main()
