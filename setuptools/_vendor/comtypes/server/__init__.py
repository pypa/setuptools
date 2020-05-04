import comtypes.client, ctypes

################################################################
# Interfaces
class IClassFactory(comtypes.IUnknown):
    _iid_ = comtypes.GUID("{00000001-0000-0000-C000-000000000046}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateInstance",
                           [ctypes.POINTER(comtypes.IUnknown),
                            ctypes.POINTER(comtypes.GUID),
                            ctypes.POINTER(ctypes.c_void_p)]),
        comtypes.STDMETHOD(comtypes.HRESULT, "LockServer",
                           [ctypes.c_int])]

    def CreateInstance(self, punkouter=None, interface=None, dynamic=False):
        if dynamic:
            if interface is not None:
                raise ValueError("interface and dynamic are mutually exclusive")
            realInterface = comtypes.automation.IDispatch
        elif interface is None:
            realInterface = comtypes.IUnknown
        else:
            realInterface = interface
        obj = ctypes.POINTER(realInterface)()
        self.__com_CreateInstance(punkouter, realInterface._iid_, ctypes.byref(obj))
        if dynamic:
            return comtypes.client.dynamic.Dispatch(obj)
        elif interface is None:
            # An interface was not specified, so return the best.
            return comtypes.client.GetBestInterface(obj)
        # An interface was specified and obj is already that interface.
        return obj

##class IExternalConnection(IUnknown):
##    _iid_ = GUID("{00000019-0000-0000-C000-000000000046}")
##    _methods_ = [
##        STDMETHOD(HRESULT, "AddConnection", [c_ulong, c_ulong]),
##        STDMETHOD(HRESULT, "ReleaseConnection", [c_ulong, c_ulong, c_ulong])]

# The following code is untested:

ACTIVEOBJECT_STRONG = 0x0
ACTIVEOBJECT_WEAK   = 0x1

oleaut32 = ctypes.oledll.oleaut32

def RegisterActiveObject(comobj, weak=True):
    punk = comobj._com_pointers_[comtypes.IUnknown._iid_]
    clsid = comobj._reg_clsid_
    if weak:
        flags = ACTIVEOBJECT_WEAK
    else:
        flags = ACTIVEOBJECT_STRONG
    handle = ctypes.c_ulong()
    oleaut32.RegisterActiveObject(punk,
                                  ctypes.byref(clsid),
                                  flags,
                                  ctypes.byref(handle))
    return handle.value

def RevokeActiveObject(handle):
    oleaut32.RevokeActiveObject(handle, None)
