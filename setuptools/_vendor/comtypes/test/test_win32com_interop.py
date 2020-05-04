import unittest

from ctypes import PyDLL, py_object, c_void_p, byref, POINTER
from ctypes.wintypes import BOOL

from comtypes import IUnknown
from comtypes.client import CreateObject
from comtypes.automation import IDispatch
from comtypes.test import requires

requires("pythoncom")
import pythoncom
import win32com.client

# We use the PyCom_PyObjectFromIUnknown function in pythoncom25.dll to
# convert a comtypes COM pointer into a pythoncom COM pointer.
# Fortunately this function is exported by the dll...
#
# This is the C prototype; we must pass 'True' as third argument:
#
# PyObject *PyCom_PyObjectFromIUnknown(IUnknown *punk, REFIID riid, BOOL bAddRef)

_PyCom_PyObjectFromIUnknown = PyDLL(pythoncom.__file__).PyCom_PyObjectFromIUnknown
_PyCom_PyObjectFromIUnknown.restype = py_object
_PyCom_PyObjectFromIUnknown.argtypes = (POINTER(IUnknown), c_void_p, BOOL)

def comtypes2pywin(ptr, interface=None):
    """Convert a comtypes pointer 'ptr' into a pythoncom
    PyI<interface> object.

    'interface' specifies the interface we want; it must be a comtypes
    interface class.  The interface must be implemented by the object;
    and the interface must be known to pythoncom.

    If 'interface' is specified, comtypes.IUnknown is used.
    """
    if interface is None:
        interface = IUnknown
    return _PyCom_PyObjectFromIUnknown(ptr, byref(interface._iid_), True)

################################################################

def comtypes_get_refcount(ptr):
    """Helper function for testing: return the COM reference count of
    a comtypes COM object"""
    ptr.AddRef()
    return ptr.Release()

from comtypes import COMObject

class MyComObject(COMObject):
    """A completely trivial COM object implementing IDispatch. Calling
    any methods will return the error code E_NOTIMPL (except the
    IUnknown methods; they are implemented in the base class."""
    _com_interfaces_ = [IDispatch]

################################################################

class Test(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "ie"):
            self.ie.Quit()
            del self.ie

    def test_mycomobject(self):
        o = MyComObject()
        p = comtypes2pywin(o, IDispatch)
        disp = win32com.client.Dispatch(p)
        self.assertEqual(repr(disp), "<COMObject <unknown>>")

    def test_ie(self):
        # Convert a comtypes COM interface pointer into a win32com COM
        # pointer.
        ie = self.ie = CreateObject("InternetExplorer.Application")
        # The COM refcount of the created object is 1:
        self.assertEqual(comtypes_get_refcount(ie), 1)
        # IE starts invisible:
        self.assertEqual(ie.Visible, False)

        # Create a pythoncom PyIDispatch object from it:
        p = comtypes2pywin(ie, interface=IDispatch)
        self.assertEqual(comtypes_get_refcount(ie), 2)

        # Make it usable...
        disp = win32com.client.Dispatch(p)
        self.assertEqual(comtypes_get_refcount(ie), 2)
        self.assertEqual(disp.Visible, False)

        # Cleanup and make sure that the COM refcounts are correct
        del p, disp
        self.assertEqual(comtypes_get_refcount(ie), 1)

if __name__ == "__main__":
    unittest.main()
