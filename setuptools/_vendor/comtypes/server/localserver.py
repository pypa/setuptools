from ctypes import *
import comtypes
from comtypes.hresult import *
from comtypes.server import IClassFactory
import logging
import queue

logger = logging.getLogger(__name__)
_debug = logger.debug

REGCLS_SINGLEUSE = 0       # class object only generates one instance
REGCLS_MULTIPLEUSE = 1     # same class object genereates multiple inst.
REGCLS_MULTI_SEPARATE = 2  # multiple use, but separate control over each
REGCLS_SUSPENDED      = 4  # register it as suspended, will be activated
REGCLS_SURROGATE      = 8  # must be used when a surrogate process

def run(classes):
    classobjects = [ClassFactory(cls) for cls in classes]
    comtypes.COMObject.__run_localserver__(classobjects)

class ClassFactory(comtypes.COMObject):
    _com_interfaces_ = [IClassFactory]
    _locks = 0
    _queue = None
    regcls = REGCLS_MULTIPLEUSE

    def __init__(self, cls, *args, **kw):
        super(ClassFactory, self).__init__()
        self._cls = cls
        self._register_class()
        self._args = args
        self._kw = kw

    def IUnknown_AddRef(self, this):
        return 2

    def IUnknown_Release(self, this):
        return 1

    def _register_class(self):
        regcls = getattr(self._cls, "_regcls_", self.regcls)
        cookie = c_ulong()
        ptr = self._com_pointers_[comtypes.IUnknown._iid_]
        clsctx = self._cls._reg_clsctx_
        clsctx &= ~comtypes.CLSCTX_INPROC # reset the inproc flags
        oledll.ole32.CoRegisterClassObject(byref(comtypes.GUID(self._cls._reg_clsid_)),
                                           ptr,
                                           clsctx,
                                           regcls,
                                           byref(cookie))
        self.cookie = cookie

    def _revoke_class(self):
        oledll.ole32.CoRevokeClassObject(self.cookie)

    def CreateInstance(self, this, punkOuter, riid, ppv):
        _debug("ClassFactory.CreateInstance(%s)", riid[0])
        obj = self._cls(*self._args, **self._kw)
        result = obj.IUnknown_QueryInterface(None, riid, ppv)
        _debug("CreateInstance() -> %s", result)
        return result

    def LockServer(self, this, fLock):
        if fLock:
            comtypes.COMObject.__server__.Lock()
        else:
            comtypes.COMObject.__server__.Unlock()
        return S_OK
