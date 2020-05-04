import array
from comtypes import BSTR, IUnknown
from comtypes.test import is_resource_enabled, get_numpy
from comtypes.test.find_memleak import find_memleak
from ctypes import POINTER, PyDLL, byref, c_double, c_long, pointer, py_object
from ctypes.wintypes import BOOL
import datetime
from decimal import Decimal
import unittest

from comtypes.automation import (
    VARIANT, VT_ARRAY, VT_VARIANT, VT_I4, VT_R4, VT_R8, VT_BSTR, VARIANT_BOOL)
from comtypes.automation import _midlSAFEARRAY
from comtypes.safearray import safearray_as_ndarray
from comtypes._safearray import SafeArrayGetVartype


def get_array(sa):
    """Get an array from a safe array type"""
    with safearray_as_ndarray:
        return sa[0]


def com_refcnt(o):
    """Return the COM refcount of an interface pointer"""
    import gc
    gc.collect()
    gc.collect()
    o.AddRef()
    return o.Release()


class VariantTestCase(unittest.TestCase):
    def test_VARIANT_array(self):
        v = VARIANT()
        v.value = ((1, 2, 3), ("foo", "bar", None))
        self.assertEqual(v.vt, VT_ARRAY | VT_VARIANT)
        self.assertEqual(v.value, ((1, 2, 3), ("foo", "bar", None)))

        def func():
            VARIANT((1, 2, 3), ("foo", "bar", None))

        bytes = find_memleak(func)
        self.assertFalse(bytes, "Leaks %d bytes" % bytes)

    def test_double_array(self):
        a = array.array("d", (3.14, 2.78))
        v = VARIANT(a)
        self.assertEqual(v.vt, VT_ARRAY | VT_R8)
        self.assertEqual(tuple(a.tolist()), v.value)

        def func():
            VARIANT(array.array("d", (3.14, 2.78)))

        bytes = find_memleak(func)
        self.assertFalse(bytes, "Leaks %d bytes" % bytes)

    def test_float_array(self):
        a = array.array("f", (3.14, 2.78))
        v = VARIANT(a)
        self.assertEqual(v.vt, VT_ARRAY | VT_R4)
        self.assertEqual(tuple(a.tolist()), v.value)

    def test_2dim_array(self):
        data = ((1, 2, 3, 4),
                (5, 6, 7, 8),
                (9, 10, 11, 12))
        v = VARIANT(data)
        self.assertEqual(v.value, data)


class SafeArrayTestCase(unittest.TestCase):

    def test_equality(self):
        a = _midlSAFEARRAY(c_long)
        b = _midlSAFEARRAY(c_long)
        self.assertTrue(a is b)

        c = _midlSAFEARRAY(BSTR)
        d = _midlSAFEARRAY(BSTR)
        self.assertTrue(c is d)

        self.assertNotEqual(a, c)

        # XXX remove:
        self.assertEqual((a._itemtype_, a._vartype_),
                             (c_long, VT_I4))
        self.assertEqual((c._itemtype_, c._vartype_),
                             (BSTR, VT_BSTR))

    def test_nested_contexts(self):
        np = get_numpy()
        if np is None:
            return

        t = _midlSAFEARRAY(BSTR)
        sa = t.from_param(["a", "b", "c"])

        first = sa[0]
        with safearray_as_ndarray:
            second = sa[0]
            with safearray_as_ndarray:
                third = sa[0]
            fourth = sa[0]
        fifth = sa[0]

        self.assertTrue(isinstance(first, tuple))
        self.assertTrue(isinstance(second, np.ndarray))
        self.assertTrue(isinstance(third, np.ndarray))
        self.assertTrue(isinstance(fourth, np.ndarray))
        self.assertTrue(isinstance(fifth, tuple))

    def test_VT_BSTR(self):
        t = _midlSAFEARRAY(BSTR)

        sa = t.from_param(["a", "b", "c"])
        self.assertEqual(sa[0], ("a", "b", "c"))
        self.assertEqual(SafeArrayGetVartype(sa), VT_BSTR)

    def test_VT_BSTR_ndarray(self):
        np = get_numpy()
        if np is None:
            return

        t = _midlSAFEARRAY(BSTR)

        sa = t.from_param(["a", "b", "c"])
        arr = get_array(sa)

        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype('<U1'), arr.dtype)
        self.assertTrue((arr == ("a", "b", "c")).all())
        self.assertEqual(SafeArrayGetVartype(sa), VT_BSTR)

    def test_VT_BSTR_leaks(self):
        sb = _midlSAFEARRAY(BSTR)

        def doit():
            sb.from_param(["foo", "bar"])

        bytes = find_memleak(doit)
        self.assertFalse(bytes, "Leaks %d bytes" % bytes)

    def test_VT_I4_leaks(self):
        sa = _midlSAFEARRAY(c_long)

        def doit():
            sa.from_param([1, 2, 3, 4, 5, 6])

        bytes = find_memleak(doit)
        self.assertFalse(bytes, "Leaks %d bytes" % bytes)

    def test_VT_I4(self):
        t = _midlSAFEARRAY(c_long)

        sa = t.from_param([11, 22, 33])

        self.assertEqual(sa[0], (11, 22, 33))

        self.assertEqual(SafeArrayGetVartype(sa), VT_I4)

        # TypeError: len() of unsized object
        self.assertRaises(TypeError, lambda: t.from_param(object()))

    def test_VT_I4_ndarray(self):
        np = get_numpy()
        if np is None:
            return

        t = _midlSAFEARRAY(c_long)

        inarr = np.array([11, 22, 33])
        sa = t.from_param(inarr)

        arr = get_array(sa)

        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype(np.int), arr.dtype)
        self.assertTrue((arr == inarr).all())
        self.assertEqual(SafeArrayGetVartype(sa), VT_I4)

    def test_array(self):
        np = get_numpy()
        if np is None:
            return

        t = _midlSAFEARRAY(c_double)
        pat = pointer(t())

        pat[0] = np.zeros(32, dtype=np.float)
        arr = get_array(pat[0])
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype(np.double), arr.dtype)
        self.assertTrue((arr == (0.0,) * 32).all())

        data = ((1.0, 2.0, 3.0),
                (4.0, 5.0, 6.0),
                (7.0, 8.0, 9.0))
        a = np.array(data, dtype=np.double)
        pat[0] = a
        arr = get_array(pat[0])
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype(np.double), arr.dtype)
        self.assertTrue((arr == data).all())

        data = ((1.0, 2.0), (3.0, 4.0), (5.0, 6.0))
        a = np.array(data,
                        dtype=np.double,
                        order="F")
        pat[0] = a
        arr = get_array(pat[0])
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype(np.double), arr.dtype)
        self.assertEqual(pat[0][0], data)

    def test_VT_VARIANT(self):
        t = _midlSAFEARRAY(VARIANT)

        now = datetime.datetime.now()
        sa = t.from_param([11, "22", None, True, now, Decimal("3.14")])
        self.assertEqual(sa[0], (11, "22", None, True, now, Decimal("3.14")))

        self.assertEqual(SafeArrayGetVartype(sa), VT_VARIANT)

    def test_VT_VARIANT_ndarray(self):
        np = get_numpy()
        if np is None:
            return

        t = _midlSAFEARRAY(VARIANT)

        now = datetime.datetime.now()
        inarr = np.array(
            [11, "22", "33", 44.0, None, True, now, Decimal("3.14")]
        ).reshape(2, 4)
        sa = t.from_param(inarr)
        arr = get_array(sa)
        self.assertEqual(np.dtype(object), arr.dtype)
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertTrue((arr == inarr).all())
        self.assertEqual(SafeArrayGetVartype(sa), VT_VARIANT)

    def test_VT_BOOL(self):
        t = _midlSAFEARRAY(VARIANT_BOOL)

        sa = t.from_param([True, False, True, False])
        self.assertEqual(sa[0], (True, False, True, False))

    def test_VT_BOOL_ndarray(self):
        np = get_numpy()
        if np is None:
            return

        t = _midlSAFEARRAY(VARIANT_BOOL)

        sa = t.from_param([True, False, True, False])
        arr = get_array(sa)
        self.assertEqual(np.dtype(np.bool_), arr.dtype)
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertTrue((arr == (True, False, True, False)).all())

    def test_VT_UNKNOWN_1(self):
        a = _midlSAFEARRAY(POINTER(IUnknown))
        t = _midlSAFEARRAY(POINTER(IUnknown))
        self.assertTrue(a is t)

        from comtypes.typeinfo import CreateTypeLib
        # will never be saved to disk
        punk = CreateTypeLib("spam").QueryInterface(IUnknown)

        # initial refcount
        initial = com_refcnt(punk)

        # This should increase the refcount by 1
        sa = t.from_param([punk])
        self.assertEqual(initial + 1, com_refcnt(punk))

        # Unpacking the array must not change the refcount, and must
        # return an equal object.
        self.assertEqual((punk,), sa[0])
        self.assertEqual(initial + 1, com_refcnt(punk))

        del sa
        self.assertEqual(initial, com_refcnt(punk))

        sa = t.from_param([None])
        self.assertEqual((POINTER(IUnknown)(),), sa[0])

    def test_VT_UNKNOWN_multi(self):
        a = _midlSAFEARRAY(POINTER(IUnknown))
        t = _midlSAFEARRAY(POINTER(IUnknown))
        self.assertTrue(a is t)

        from comtypes.typeinfo import CreateTypeLib
        # will never be saved to disk
        punk = CreateTypeLib("spam").QueryInterface(IUnknown)

        # initial refcount
        initial = com_refcnt(punk)

        # This should increase the refcount by 4
        sa = t.from_param((punk,) * 4)
        self.assertEqual(initial + 4, com_refcnt(punk))

        # Unpacking the array must not change the refcount, and must
        # return an equal object.
        self.assertEqual((punk,)*4, sa[0])
        self.assertEqual(initial + 4, com_refcnt(punk))

        del sa
        self.assertEqual(initial, com_refcnt(punk))

        # This should increase the refcount by 2
        sa = t.from_param((punk, None, punk, None))
        self.assertEqual(initial + 2, com_refcnt(punk))

        null = POINTER(IUnknown)()
        self.assertEqual((punk, null, punk, null), sa[0])

        del sa
        self.assertEqual(initial, com_refcnt(punk))

        # repeat same test, with 2 different com pointers

        plib = CreateTypeLib("foo")
        a, b = com_refcnt(plib), com_refcnt(punk)
        sa = t.from_param([plib, punk, plib])

####        self.failUnlessEqual((plib, punk, plib), sa[0])
        self.assertEqual((a+2, b+1), (com_refcnt(plib), com_refcnt(punk)))

        del sa
        self.assertEqual((a, b), (com_refcnt(plib), com_refcnt(punk)))

    def test_VT_UNKNOWN_multi_ndarray(self):
        np = get_numpy()
        if np is None:
            return

        a = _midlSAFEARRAY(POINTER(IUnknown))
        t = _midlSAFEARRAY(POINTER(IUnknown))
        self.assertTrue(a is t)

        from comtypes.typeinfo import CreateTypeLib
        # will never be saved to disk
        punk = CreateTypeLib("spam").QueryInterface(IUnknown)

        # initial refcount
        initial = com_refcnt(punk)

        # This should increase the refcount by 4
        sa = t.from_param((punk,) * 4)
        self.assertEqual(initial + 4, com_refcnt(punk))

        # Unpacking the array must not change the refcount, and must
        # return an equal object. Creating an ndarray may change the
        # refcount.
        arr = get_array(sa)
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype(object), arr.dtype)
        self.assertTrue((arr == (punk,)*4).all())
        self.assertEqual(initial + 8, com_refcnt(punk))

        del arr
        self.assertEqual(initial + 4, com_refcnt(punk))

        del sa
        self.assertEqual(initial, com_refcnt(punk))

        # This should increase the refcount by 2
        sa = t.from_param((punk, None, punk, None))
        self.assertEqual(initial + 2, com_refcnt(punk))

        null = POINTER(IUnknown)()
        arr = get_array(sa)
        self.assertTrue(isinstance(arr, np.ndarray))
        self.assertEqual(np.dtype(object), arr.dtype)
        self.assertTrue((arr == (punk, null, punk, null)).all())

        del sa
        del arr
        self.assertEqual(initial, com_refcnt(punk))

    def test_UDT(self):
        from comtypes.gen.TestComServerLib import MYCOLOR

        t = _midlSAFEARRAY(MYCOLOR)
        self.assertTrue(t is _midlSAFEARRAY(MYCOLOR))

        sa = t.from_param([MYCOLOR(0, 0, 0), MYCOLOR(1, 2, 3)])

        self.assertEqual([(x.red, x.green, x.blue) for x in sa[0]],
                             [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)])

        def doit():
            t.from_param([MYCOLOR(0, 0, 0), MYCOLOR(1, 2, 3)])
        bytes = find_memleak(doit)
        self.assertFalse(bytes, "Leaks %d bytes" % bytes)

    def test_UDT_ndarray(self):
        np = get_numpy()
        if np is None:
            return

        from comtypes.gen.TestComServerLib import MYCOLOR

        t = _midlSAFEARRAY(MYCOLOR)
        self.assertTrue(t is _midlSAFEARRAY(MYCOLOR))

        sa = t.from_param([MYCOLOR(0, 0, 0), MYCOLOR(1, 2, 3)])
        arr = get_array(sa)

        self.assertTrue(isinstance(arr, np.ndarray))
        # The conversion code allows numpy to choose the dtype of
        # structured data.  This dtype is structured under numpy 1.5, 1.7 and
        # 1.8, and object in 1.6. Instead of assuming either of these, check
        # the array contents based on the chosen type.
        if arr.dtype is np.dtype(object):
            data = [(x.red, x.green, x.blue) for x in arr]
        else:
            float_dtype = np.dtype('float64')
            self.assertIs(arr.dtype[0], float_dtype)
            self.assertIs(arr.dtype[1], float_dtype)
            self.assertIs(arr.dtype[2], float_dtype)
            data = [tuple(x) for x in arr]
        self.assertEqual(data, [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)])

    def test_datetime64_ndarray(self):
        np = get_numpy()
        if np is None:
            return
        try:
            np.datetime64
        except AttributeError:
            return

        dates = np.array([
            np.datetime64("2000-01-01T05:30:00", "s"),
            np.datetime64("1800-01-01T05:30:00", "ms"),
            np.datetime64("2014-03-07T00:12:56", "us"),
            np.datetime64("2000-01-01T12:34:56", "ns"),
        ])

        t = _midlSAFEARRAY(VARIANT)
        sa = t.from_param(dates)
        arr = get_array(sa).astype(dates.dtype)
        self.assertTrue((dates == arr).all())


if is_resource_enabled("pythoncom"):
    try:
        import pythoncom
    except ImportError:
        # pywin32 not installed...
        pass
    else:
        # pywin32 is available.  The pythoncom dll contains two handy
        # exported functions that allow to create a VARIANT from a Python
        # object, also a function that unpacks a VARIANT into a Python
        # object.
        #
        # This allows us to create und unpack SAFEARRAY instances
        # contained in VARIANTs, and check for consistency with the
        # comtypes code.

        _dll = PyDLL(pythoncom.__file__)

        # c:/sf/pywin32/com/win32com/src/oleargs.cpp 213
        # PyObject *PyCom_PyObjectFromVariant(const VARIANT *var)
        unpack = _dll.PyCom_PyObjectFromVariant
        unpack.restype = py_object
        unpack.argtypes = POINTER(VARIANT),

        # c:/sf/pywin32/com/win32com/src/oleargs.cpp 54
        # BOOL PyCom_VariantFromPyObject(PyObject *obj, VARIANT *var)
        _pack = _dll.PyCom_VariantFromPyObject
        _pack.argtypes = py_object, POINTER(VARIANT)
        _pack.restype = BOOL

        def pack(obj):
            var = VARIANT()
            _pack(obj, byref(var))
            return var

        class PyWinTest(unittest.TestCase):
            def test_1dim(self):
                data = (1, 2, 3)
                variant = pack(data)
                self.assertEqual(variant.value, data)
                self.assertEqual(unpack(variant), data)

            def test_2dim(self):
                data = ((1, 2, 3), (4, 5, 6), (7, 8, 9))
                variant = pack(data)
                self.assertEqual(variant.value, data)
                self.assertEqual(unpack(variant), data)

            def test_3dim(self):
                data = ( ( (1, 2), (3, 4), (5, 6) ),
                         ( (7, 8), (9, 10), (11, 12) ) )
                variant = pack(data)
                self.assertEqual(variant.value, data)
                self.assertEqual(unpack(variant), data)

            def test_4dim(self):
                data = ( ( ( ( 1,  2), ( 3,  4) ),
                           ( ( 5,  6), ( 7,  8) ) ),
                         ( ( ( 9, 10), (11, 12) ),
                           ( (13, 14), (15, 16) ) ) )
                variant = pack(data)
                self.assertEqual(variant.value, data)
                self.assertEqual(unpack(variant), data)

if __name__ == "__main__":
    unittest.main()
