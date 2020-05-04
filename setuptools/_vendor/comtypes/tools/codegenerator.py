# Code generator to generate code for everything contained in COM type
# libraries.
import os
import io
import keyword
from comtypes.tools import typedesc
import comtypes.client
import comtypes.client._generate

version = "$Rev$"[6:-2]

__warn_on_munge__ = __debug__


class lcid(object):
    def __repr__(self):
        return "_lcid"
lcid = lcid()

class dispid(object):
    def __init__(self, memid):
        self.memid = memid

    def __repr__(self):
        return "dispid(%s)" % self.memid

class helpstring(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "helpstring(%r)" % self.text


# XXX Should this be in ctypes itself?
ctypes_names = {
    "unsigned char": "c_ubyte",
    "signed char": "c_byte",
    "char": "c_char",

    "wchar_t": "c_wchar",

    "short unsigned int": "c_ushort",
    "short int": "c_short",

    "long unsigned int": "c_ulong",
    "long int": "c_long",
    "long signed int": "c_long",

    "unsigned int": "c_uint",
    "int": "c_int",

    "long long unsigned int": "c_ulonglong",
    "long long int": "c_longlong",

    "double": "c_double",
    "float": "c_float",

    # Hm...
    "void": "None",
}

def get_real_type(tp):
    if type(tp) is typedesc.Typedef:
        return get_real_type(tp.typ)
    elif isinstance(tp, typedesc.CvQualifiedType):
        return get_real_type(tp.typ)
    return tp

ASSUME_STRINGS = True

def _calc_packing(struct, fields, pack, isStruct):
    # Try a certain packing, raise PackingError if field offsets,
    # total size ot total alignment is wrong.
    if struct.size is None: # incomplete struct
        return -1
    if struct.name in dont_assert_size:
        return None
    if struct.bases:
        size = struct.bases[0].size
        total_align = struct.bases[0].align
    else:
        size = 0
        total_align = 8 # in bits
    for i, f in enumerate(fields):
        if f.bits: # this code cannot handle bit field sizes.
##            print "##XXX FIXME"
            return -2 # XXX FIXME
        s, a = storage(f.typ)
        if pack is not None:
            a = min(pack, a)
        if size % a:
            size += a - size % a
        if isStruct:
            if size != f.offset:
                raise PackingError("field %s offset (%s/%s)" % (f.name, size, f.offset))
            size += s
        else:
            size = max(size, s)
        total_align = max(total_align, a)
    if total_align != struct.align:
        raise PackingError("total alignment (%s/%s)" % (total_align, struct.align))
    a = total_align
    if pack is not None:
        a = min(pack, a)
    if size % a:
        size += a - size % a
    if size != struct.size:
        raise PackingError("total size (%s/%s)" % (size, struct.size))

def calc_packing(struct, fields):
    # try several packings, starting with unspecified packing
    isStruct = isinstance(struct, typedesc.Structure)
    for pack in [None, 16*8, 8*8, 4*8, 2*8, 1*8]:
        try:
            _calc_packing(struct, fields, pack, isStruct)
        except PackingError as details:
            continue
        else:
            if pack is None:
                return None
            return pack/8
    raise PackingError("PACKING FAILED: %s" % details)

class PackingError(Exception):
    pass

try:
    set
except NameError:
    # Python 2.3
    from sets import Set as set

# XXX These should be filtered out in gccxmlparser.
dont_assert_size = set(
    [
    "__si_class_type_info_pseudo",
    "__class_type_info_pseudo",
    ]
    )

def storage(t):
    # return the size and alignment of a type
    if isinstance(t, typedesc.Typedef):
        return storage(t.typ)
    elif isinstance(t, typedesc.ArrayType):
        s, a = storage(t.typ)
        return s * (int(t.max) - int(t.min) + 1), a
    return int(t.size), int(t.align)

################################################################

class Generator(object):

    def __init__(self, ofi, known_symbols=None):
        self._externals = {}
        self.output = ofi
        self.stream = io.StringIO()
        self.imports = io.StringIO()
##        self.stream = self.imports = self.output
        self.known_symbols = known_symbols or {}

        self.done = set() # type descriptions that have been generated
        self.names = set() # names that have been generated

    def generate(self, item):
        if item in self.done:
            return
        if isinstance(item, typedesc.StructureHead):
            name = getattr(item.struct, "name", None)
        else:
            name = getattr(item, "name", None)
        if name in self.known_symbols:
            mod = self.known_symbols[name]
            print("from %s import %s" % (mod, name), file=self.imports)
            self.done.add(item)
            if isinstance(item, typedesc.Structure):
                self.done.add(item.get_head())
                self.done.add(item.get_body())
            return
        mth = getattr(self, type(item).__name__)
        # to avoid infinite recursion, we have to mark it as done
        # before actually generating the code.
        self.done.add(item)
        mth(item)

    def generate_all(self, items):
        for item in items:
            self.generate(item)

    def _make_relative_path(self, path1, path2):
        """path1 and path2 are pathnames.
        Return path1 as a relative path to path2, if possible.
        """
        path1 = os.path.abspath(path1)
        path2 = os.path.abspath(path2)
        common = os.path.commonprefix([os.path.normcase(path1),
                                       os.path.normcase(path2)])
        if not os.path.isdir(common):
            return path1
        if not common.endswith("\\"):
            return path1
        if not os.path.isdir(path2):
            path2 = os.path.dirname(path2)
        # strip the common prefix
        path1 = path1[len(common):]
        path2 = path2[len(common):]

        parts2 = path2.split("\\")
        return "..\\" * len(parts2) + path1

    def generate_code(self, items, filename=None):
        self.filename = filename
        if filename is not None:
            # Hm, what is the CORRECT encoding?
            print("# -*- coding: mbcs -*-", file=self.output)
            if os.path.isabs(filename):
                # absolute path
                print("typelib_path = %r" % filename, file=self.output)
            elif not os.path.dirname(filename) and not os.path.isfile(filename):
                # no directory given, and not in current directory.
                print("typelib_path = %r" % filename, file=self.output)
            else:
                # relative path; make relative to comtypes.gen.
                path = self._make_relative_path(filename, comtypes.gen.__path__[0])
                print("import os", file=self.output)
                print("typelib_path = os.path.normpath(", file=self.output)
                print("    os.path.abspath(os.path.join(os.path.dirname(__file__),", file=self.output)
                print("                                 %r)))" % path, file=self.output)

                p = os.path.normpath(os.path.abspath(os.path.join(comtypes.gen.__path__[0],
                                                                  path)))
                assert os.path.isfile(p)
        print("_lcid = 0 # change this if required", file=self.imports)
        print("from ctypes import *", file=self.imports)
        items = set(items)
        loops = 0
        while items:
            loops += 1
            self.more = set()
            self.generate_all(items)

            items |= self.more
            items -= self.done

        self.output.write(self.imports.getvalue())
        self.output.write("\n\n")
        self.output.write(self.stream.getvalue())

        import textwrap
        wrapper = textwrap.TextWrapper(subsequent_indent="           ",
                                       break_long_words=False)
        # XXX The space before '%s' is needed to make sure that the entire list
        #     does not get pushed to the next line when the first name is
        #     excessively long.
        text = "__all__ = [ %s]" % ", ".join([repr(str(n)) for n in self.names])

        for line in wrapper.wrap(text):
            print(line, file=self.output)
        print("from comtypes import _check_version; _check_version(%r)" % version, file=self.output)
        return loops

    def type_name(self, t, generate=True):
        # Return a string, containing an expression which can be used
        # to refer to the type. Assumes the 'from ctypes import *'
        # namespace is available.
        if isinstance(t, typedesc.SAFEARRAYType):
            return "_midlSAFEARRAY(%s)" % self.type_name(t.typ)
##        if isinstance(t, typedesc.CoClass):
##            return "%s._com_interfaces_[0]" % t.name
        if isinstance(t, typedesc.Typedef):
            return t.name
        if isinstance(t, typedesc.PointerType):
            if ASSUME_STRINGS:
                x = get_real_type(t.typ)
                if isinstance(x, typedesc.FundamentalType):
                    if x.name == "char":
                        self.need_STRING()
                        return "STRING"
                    elif x.name == "wchar_t":
                        self.need_WSTRING()
                        return "WSTRING"

            result = "POINTER(%s)" % self.type_name(t.typ, generate)
            # XXX Better to inspect t.typ!
            if result.startswith("POINTER(WINFUNCTYPE"):
                return result[len("POINTER("):-1]
            if result.startswith("POINTER(CFUNCTYPE"):
                return result[len("POINTER("):-1]
            elif result == "POINTER(None)":
                return "c_void_p"
            return result
        elif isinstance(t, typedesc.ArrayType):
            return "%s * %s" % (self.type_name(t.typ, generate), int(t.max)+1)
        elif isinstance(t, typedesc.FunctionType):
            args = [self.type_name(x, generate) for x in [t.returns] + list(t.iterArgTypes())]
            if "__stdcall__" in t.attributes:
                return "WINFUNCTYPE(%s)" % ", ".join(args)
            else:
                return "CFUNCTYPE(%s)" % ", ".join(args)
        elif isinstance(t, typedesc.CvQualifiedType):
            # const and volatile are ignored
            return "%s" % self.type_name(t.typ, generate)
        elif isinstance(t, typedesc.FundamentalType):
            return ctypes_names[t.name]
        elif isinstance(t, typedesc.Structure):
            return t.name
        elif isinstance(t, typedesc.Enumeration):
            if t.name:
                return t.name
            return "c_int" # enums are integers
        return t.name

    def need_VARIANT_imports(self, value):
        text = repr(value)
        if "Decimal(" in text:
            print("from decimal import Decimal", file=self.imports)
        if "datetime.datetime(" in text:
            print("import datetime", file=self.imports)

    _STRING_defined = False
    def need_STRING(self):
        if self._STRING_defined:
            return
        print("STRING = c_char_p", file=self.imports)
        self._STRING_defined = True

    _WSTRING_defined = False
    def need_WSTRING(self):
        if self._WSTRING_defined:
            return
        print("WSTRING = c_wchar_p", file=self.imports)
        self._WSTRING_defined = True

    _OPENARRAYS_defined = False
    def need_OPENARRAYS(self):
        if self._OPENARRAYS_defined:
            return
        print("OPENARRAY = POINTER(c_ubyte) # hack, see comtypes/tools/codegenerator.py", file=self.imports)
        self._OPENARRAYS_defined = True

    _arraytypes = 0
    def ArrayType(self, tp):
        self._arraytypes += 1
        self.generate(get_real_type(tp.typ))
        self.generate(tp.typ)

    _enumvalues = 0
    def EnumValue(self, tp):
        value = int(tp.value)
        if keyword.iskeyword(tp.name):
            # XXX use logging!
            if __warn_on_munge__:
                print("# Fixing keyword as EnumValue for %s" % tp.name)
            tp.name += "_"
        print("%s = %d" % (tp.name, value), file=self.stream)
        self.names.add(tp.name)
        self._enumvalues += 1

    _enumtypes = 0
    def Enumeration(self, tp):
        self._enumtypes += 1
        print(file=self.stream)
        if tp.name:
            print("# values for enumeration '%s'" % tp.name, file=self.stream)
        else:
            print("# values for unnamed enumeration", file=self.stream)
        # Some enumerations have the same name for the enum type
        # and an enum value.  Excel's XlDisplayShapes is such an example.
        # Since we don't have separate namespaces for the type and the values,
        # we generate the TYPE last, overwriting the value. XXX
        for item in tp.values:
            self.generate(item)
        if tp.name:
            print("%s = c_int # enum" % tp.name, file=self.stream)
            self.names.add(tp.name)

    _GUID_defined = False
    def need_GUID(self):
        if self._GUID_defined:
            return
        self._GUID_defined = True
        modname = self.known_symbols.get("GUID")
        if modname:
            print("from %s import GUID" % modname, file=self.imports)

    _typedefs = 0
    def Typedef(self, tp):
        self._typedefs += 1
        if type(tp.typ) in (typedesc.Structure, typedesc.Union):
            self.generate(tp.typ.get_head())
            self.more.add(tp.typ)
        else:
            self.generate(tp.typ)
        if self.type_name(tp.typ) in self.known_symbols:
            stream = self.imports
        else:
            stream = self.stream
        if tp.name != self.type_name(tp.typ):
            print("%s = %s" % \
                  (tp.name, self.type_name(tp.typ)), file=stream)
        self.names.add(tp.name)

    def FundamentalType(self, item):
        pass # we should check if this is known somewhere

    def StructureHead(self, head):
        for struct in head.struct.bases:
            self.generate(struct.get_head())
            self.more.add(struct)
        if head.struct.location:
            print("# %s %s" % head.struct.location, file=self.stream)
        basenames = [self.type_name(b) for b in head.struct.bases]
        if basenames:
            self.need_GUID()
            method_names = [m.name for m in head.struct.members if type(m) is typedesc.Method]
            print("class %s(%s):" % (head.struct.name, ", ".join(basenames)), file=self.stream)
            print("    _iid_ = GUID('{}') # please look up iid and fill in!", file=self.stream)
            if "Enum" in method_names:
                print("    def __iter__(self):", file=self.stream)
                print("        return self.Enum()", file=self.stream)
            elif method_names == "Next Skip Reset Clone".split():
                print("    def __iter__(self):", file=self.stream)
                print("        return self", file=self.stream)
                print(file=self.stream)
                print("    def next(self):", file=self.stream)
                print("         arr, fetched = self.Next(1)", file=self.stream)
                print("         if fetched == 0:", file=self.stream)
                print("             raise StopIteration", file=self.stream)
                print("         return arr[0]", file=self.stream)
        else:
            methods = [m for m in head.struct.members if type(m) is typedesc.Method]
            if methods:
                # Hm. We cannot generate code for IUnknown...
                print("assert 0, 'cannot generate code for IUnknown'", file=self.stream)
                print("class %s(_com_interface):" % head.struct.name, file=self.stream)
                print("    pass", file=self.stream)
            elif type(head.struct) == typedesc.Structure:
                print("class %s(Structure):" % head.struct.name, file=self.stream)
                if hasattr(head.struct, "_recordinfo_"):
                    print("    _recordinfo_ = %r" % (head.struct._recordinfo_,), file=self.stream)
                else:
                    print("    pass", file=self.stream)
            elif type(head.struct) == typedesc.Union:
                print("class %s(Union):" % head.struct.name, file=self.stream)
                print("    pass", file=self.stream)
        self.names.add(head.struct.name)

    _structures = 0
    def Structure(self, struct):
        self._structures += 1
        self.generate(struct.get_head())
        self.generate(struct.get_body())

    Union = Structure

    def StructureBody(self, body):
        fields = []
        methods = []
        for m in body.struct.members:
            if type(m) is typedesc.Field:
                fields.append(m)
                if type(m.typ) is typedesc.Typedef:
                    self.generate(get_real_type(m.typ))
                self.generate(m.typ)
            elif type(m) is typedesc.Method:
                methods.append(m)
                self.generate(m.returns)
                self.generate_all(m.iterArgTypes())
            elif type(m) is typedesc.Constructor:
                pass

        # we don't need _pack_ on Unions (I hope, at least), and not
        # on COM interfaces:
        if not methods:
            try:
                pack = calc_packing(body.struct, fields)
                if pack is not None:
                    print("%s._pack_ = %s" % (body.struct.name, pack), file=self.stream)
            except PackingError as details:
                # if packing fails, write a warning comment to the output.
                import warnings
                message = "Structure %s: %s" % (body.struct.name, details)
                warnings.warn(message, UserWarning)
                print("# WARNING: %s" % details, file=self.stream)

        if fields:
            if body.struct.bases:
                assert len(body.struct.bases) == 1
                self.generate(body.struct.bases[0].get_body())
            # field definition normally span several lines.
            # Before we generate them, we need to 'import' everything they need.
            # So, call type_name for each field once,
            for f in fields:
                self.type_name(f.typ)
            print("%s._fields_ = [" % body.struct.name, file=self.stream)
            if body.struct.location:
                print("    # %s %s" % body.struct.location, file=self.stream)
            # unnamed fields will get autogenerated names "_", "_1". "_2", "_3", ...
            unnamed_index = 0
            for f in fields:
                if not f.name:
                    if unnamed_index:
                        fieldname = "_%d" % unnamed_index
                    else:
                        fieldname = "_"
                    unnamed_index += 1
                    print("    # Unnamed field renamed to '%s'" % fieldname, file=self.stream)
                else:
                    fieldname = f.name
                if f.bits is None:
                    print("    ('%s', %s)," % (fieldname, self.type_name(f.typ)), file=self.stream)
                else:
                    print("    ('%s', %s, %s)," % (fieldname, self.type_name(f.typ), f.bits), file=self.stream)
            print("]", file=self.stream)

            if body.struct.size is None:
                msg = ("# The size provided by the typelib is incorrect.\n"
                       "# The size and alignment check for %s is skipped.")
                print(msg % body.struct.name, file=self.stream)
            elif body.struct.name not in dont_assert_size:
                size = body.struct.size // 8
                print("assert sizeof(%s) == %s, sizeof(%s)" % \
                      (body.struct.name, size, body.struct.name), file=self.stream)
                align = body.struct.align // 8
                print("assert alignment(%s) == %s, alignment(%s)" % \
                      (body.struct.name, align, body.struct.name), file=self.stream)

        if methods:
            self.need_COMMETHOD()
            # method definitions normally span several lines.
            # Before we generate them, we need to 'import' everything they need.
            # So, call type_name for each field once,
            for m in methods:
                self.type_name(m.returns)
                for a in m.iterArgTypes():
                    self.type_name(a)
            print("%s._methods_ = [" % body.struct.name, file=self.stream)
            if body.struct.location:
                print("# %s %s" % body.struct.location, file=self.stream)

            for m in methods:
                if m.location:
                    print("    # %s %s" % m.location, file=self.stream)
                print("    COMMETHOD([], %s, '%s'," % (
                    self.type_name(m.returns),
                    m.name), file=self.stream)
                for a in m.iterArgTypes():
                    print("               ( [], %s, )," % self.type_name(a), file=self.stream)
                    print("             ),", file=self.stream)
            print("]", file=self.stream)

    _midlSAFEARRAY_defined = False
    def need_midlSAFEARRAY(self):
        if self._midlSAFEARRAY_defined:
            return
        print("from comtypes.automation import _midlSAFEARRAY", file=self.imports)
        self._midlSAFEARRAY_defined = True

    _CoClass_defined = False
    def need_CoClass(self):
        if self._CoClass_defined:
            return
        print("from comtypes import CoClass", file=self.imports)
        self._CoClass_defined = True

    _dispid_defined = False
    def need_dispid(self):
        if self._dispid_defined:
            return
        print("from comtypes import dispid", file=self.imports)
        self._dispid_defined = True

    _COMMETHOD_defined = False
    def need_COMMETHOD(self):
        if self._COMMETHOD_defined:
            return
        print("from comtypes import helpstring", file=self.imports)
        print("from comtypes import COMMETHOD", file=self.imports)
        self._COMMETHOD_defined = True

    _DISPMETHOD_defined = False
    def need_DISPMETHOD(self):
        if self._DISPMETHOD_defined:
            return
        print("from comtypes import DISPMETHOD, DISPPROPERTY, helpstring", file=self.imports)
        self._DISPMETHOD_defined = True

    ################################################################
    # top-level typedesc generators
    #
    def TypeLib(self, lib):
        # lib.name, lib.gui, lib.major, lib.minor, lib.doc

        # Hm, in user code we have to write:
        # class MyServer(COMObject, ...):
        #     _com_interfaces_ = [MyTypeLib.IInterface]
        #     _reg_typelib_ = MyTypeLib.Library._reg_typelib_
        #                               ^^^^^^^
        # Should the '_reg_typelib_' attribute be at top-level in the
        # generated code, instead as being an attribute of the
        # 'Library' symbol?
        print("class Library(object):", file=self.stream)
        if lib.doc:
            print("    %r" % lib.doc, file=self.stream)
        if lib.name:
            print("    name = %r" % lib.name, file=self.stream)
        print("    _reg_typelib_ = (%r, %r, %r)" % (lib.guid, lib.major, lib.minor), file=self.stream)
        print(file=self.stream)

    def External(self, ext):
        # ext.docs - docstring of typelib
        # ext.symbol_name - symbol to generate
        # ext.tlib - the ITypeLib pointer to the typelibrary containing the symbols definition
        #
        # ext.name filled in here

        libdesc = str(ext.tlib.GetLibAttr()) # str(TLIBATTR) is unique for a given typelib
        if libdesc in self._externals: # typelib wrapper already created
            modname = self._externals[libdesc]
            # we must fill in ext.name, it is used by self.type_name()
            ext.name = "%s.%s" % (modname, ext.symbol_name)
            return

        modname = comtypes.client._generate._name_module(ext.tlib)
        ext.name = "%s.%s" % (modname, ext.symbol_name)
        self._externals[libdesc] = modname
        print("import", modname, file=self.imports)
        comtypes.client.GetModule(ext.tlib)

    def Constant(self, tp):
        print("%s = %r # Constant %s" % (tp.name,
                                         tp.value,
                                         self.type_name(tp.typ, False)), file=self.stream)
        self.names.add(tp.name)

    def SAFEARRAYType(self, sa):
        self.generate(sa.typ)
        self.need_midlSAFEARRAY()

    _pointertypes = 0
    def PointerType(self, tp):
        self._pointertypes += 1
        if type(tp.typ) is typedesc.ComInterface:
            # this defines the class
            self.generate(tp.typ.get_head())
            # this defines the _methods_
            self.more.add(tp.typ)
        elif type(tp.typ) is typedesc.PointerType:
            self.generate(tp.typ)
        elif type(tp.typ) in (typedesc.Union, typedesc.Structure):
            self.generate(tp.typ.get_head())
            self.more.add(tp.typ)
        elif type(tp.typ) is typedesc.Typedef:
            self.generate(tp.typ)
        else:
            self.generate(tp.typ)

    def CoClass(self, coclass):
        self.need_GUID()
        self.need_CoClass()
        print("class %s(CoClass):" % coclass.name, file=self.stream)
        doc = getattr(coclass, "doc", None)
        if doc:
            print("    %r" % doc, file=self.stream)
        print("    _reg_clsid_ = GUID(%r)" % coclass.clsid, file=self.stream)
        print("    _idlflags_ = %s" % coclass.idlflags, file=self.stream)
        if self.filename is not None:
            print("    _typelib_path_ = typelib_path", file=self.stream)
##X        print >> self.stream, "POINTER(%s).__ctypes_from_outparam__ = wrap" % coclass.name

        libid = coclass.tlibattr.guid
        wMajor, wMinor = coclass.tlibattr.wMajorVerNum, coclass.tlibattr.wMinorVerNum
        print("    _reg_typelib_ = (%r, %s, %s)" % (str(libid), wMajor, wMinor), file=self.stream)

        for itf, idlflags in coclass.interfaces:
            self.generate(itf.get_head())
        implemented = []
        sources = []
        for item in coclass.interfaces:
            # item is (interface class, impltypeflags)
            if item[1] & 2: # IMPLTYPEFLAG_FSOURCE
                # source interface
                where = sources
            else:
                # sink interface
                where = implemented
            if item[1] & 1: # IMPLTYPEFLAG_FDEAULT
                # The default interface should be the first item on the list
                where.insert(0, item[0].name)
            else:
                where.append(item[0].name)
        if implemented:
            print("%s._com_interfaces_ = [%s]" % (coclass.name, ", ".join(implemented)), file=self.stream)
        if sources:
            print("%s._outgoing_interfaces_ = [%s]" % (coclass.name, ", ".join(sources)), file=self.stream)
        print(file=self.stream)
        self.names.add(coclass.name)

    def ComInterface(self, itf):
        self.generate(itf.get_head())
        self.generate(itf.get_body())
        self.names.add(itf.name)

    def _is_enuminterface(self, itf):
        # Check if this is an IEnumXXX interface
        if not itf.name.startswith("IEnum"):
            return False
        member_names = [mth.name for mth in itf.members]
        for name in ("Next", "Skip", "Reset", "Clone"):
            if name not in member_names:
                return False
        return True

    def ComInterfaceHead(self, head):
        if head.itf.name in self.known_symbols:
            return
        base = head.itf.base
        if head.itf.base is None:
            # we don't beed to generate IUnknown
            return
        self.generate(base.get_head())
        self.more.add(base)
        basename = self.type_name(head.itf.base)

        self.need_GUID()
        print("class %s(%s):" % (head.itf.name, basename), file=self.stream)
        print("    _case_insensitive_ = True", file=self.stream)
        doc = getattr(head.itf, "doc", None)
        if doc:
            print("    %r" % doc, file=self.stream)
        print("    _iid_ = GUID(%r)" % head.itf.iid, file=self.stream)
        print("    _idlflags_ = %s" % head.itf.idlflags, file=self.stream)

        if self._is_enuminterface(head.itf):
            print("    def __iter__(self):", file=self.stream)
            print("        return self", file=self.stream)
            print(file=self.stream)

            print("    def next(self):", file=self.stream)
            print("        item, fetched = self.Next(1)", file=self.stream)
            print("        if fetched:", file=self.stream)
            print("            return item", file=self.stream)
            print("        raise StopIteration", file=self.stream)
            print(file=self.stream)

            print("    def __getitem__(self, index):", file=self.stream)
            print("        self.Reset()", file=self.stream)
            print("        self.Skip(index)", file=self.stream)
            print("        item, fetched = self.Next(1)", file=self.stream)
            print("        if fetched:", file=self.stream)
            print("            return item", file=self.stream)
            print("        raise IndexError(index)", file=self.stream)
            print(file=self.stream)

    def ComInterfaceBody(self, body):
        # The base class must be fully generated, including the
        # _methods_ list.
        self.generate(body.itf.base)

        # make sure we can generate the body
        for m in body.itf.members:
            for a in m.arguments:
                self.generate(a[0])
            self.generate(m.returns)

        self.need_COMMETHOD()
        self.need_dispid()
        print("%s._methods_ = [" % body.itf.name, file=self.stream)
        for m in body.itf.members:
            if isinstance(m, typedesc.ComMethod):
                self.make_ComMethod(m, "dual" in body.itf.idlflags)
            else:
                raise TypeError("what's this?")

        print("]", file=self.stream)
        print("################################################################", file=self.stream)
        print("## code template for %s implementation" % body.itf.name, file=self.stream)
        print("##class %s_Impl(object):" % body.itf.name, file=self.stream)

        methods = {}
        for m in body.itf.members:
            if isinstance(m, typedesc.ComMethod):
                # m.arguments is a sequence of tuples:
                # (argtype, argname, idlflags, docstring)
                # Some typelibs have unnamed method parameters!
                inargs = [a[1] or '<unnamed>' for a in m.arguments
                        if not 'out' in a[2]]
                outargs = [a[1] or '<unnamed>' for a in m.arguments
                           if 'out' in a[2]]
                if 'propget' in m.idlflags:
                    methods.setdefault(m.name, [0, inargs, outargs, m.doc])[0] |= 1
                elif 'propput' in m.idlflags:
                    methods.setdefault(m.name, [0, inargs[:-1], inargs[-1:], m.doc])[0] |= 2
                else:
                    methods[m.name] = [0, inargs, outargs, m.doc]

        for name, (typ, inargs, outargs, doc) in methods.items():
            if typ == 0: # method
                print("##    def %s(%s):" % (name, ", ".join(["self"] + inargs)), file=self.stream)
                print("##        %r" % (doc or "-no docstring-"), file=self.stream)
                print("##        #return %s" % (", ".join(outargs)), file=self.stream)
            elif typ == 1: # propget
                print("##    @property", file=self.stream)
                print("##    def %s(%s):" % (name, ", ".join(["self"] + inargs)), file=self.stream)
                print("##        %r" % (doc or "-no docstring-"), file=self.stream)
                print("##        #return %s" % (", ".join(outargs)), file=self.stream)
            elif typ == 2: # propput
                print("##    def _set(%s):" % ", ".join(["self"] + inargs + outargs), file=self.stream)
                print("##        %r" % (doc or "-no docstring-"), file=self.stream)
                print("##    %s = property(fset = _set, doc = _set.__doc__)" % name, file=self.stream)
            elif typ == 3: # propget + propput
                print("##    def _get(%s):" % ", ".join(["self"] + inargs), file=self.stream)
                print("##        %r" % (doc or "-no docstring-"), file=self.stream)
                print("##        #return %s" % (", ".join(outargs)), file=self.stream)
                print("##    def _set(%s):" % ", ".join(["self"] + inargs + outargs), file=self.stream)
                print("##        %r" % (doc or "-no docstring-"), file=self.stream)
                print("##    %s = property(_get, _set, doc = _set.__doc__)" % name, file=self.stream)
            else:
                raise RuntimeError("BUG")
            print("##", file=self.stream)
        print(file=self.stream)

    def DispInterface(self, itf):
        self.generate(itf.get_head())
        self.generate(itf.get_body())
        self.names.add(itf.name)

    def DispInterfaceHead(self, head):
        self.generate(head.itf.base)
        basename = self.type_name(head.itf.base)

        self.need_GUID()
        print("class %s(%s):" % (head.itf.name, basename), file=self.stream)
        print("    _case_insensitive_ = True", file=self.stream)
        doc = getattr(head.itf, "doc", None)
        if doc:
            print("    %r" % doc, file=self.stream)
        print("    _iid_ = GUID(%r)" % head.itf.iid, file=self.stream)
        print("    _idlflags_ = %s" % head.itf.idlflags, file=self.stream)
        print("    _methods_ = []", file=self.stream)

    def DispInterfaceBody(self, body):
        # make sure we can generate the body
        for m in body.itf.members:
            if isinstance(m, typedesc.DispMethod):
                for a in m.arguments:
                    self.generate(a[0])
                self.generate(m.returns)
            elif isinstance(m, typedesc.DispProperty):
                self.generate(m.typ)
            else:
                raise TypeError(m)

        self.need_dispid()
        self.need_DISPMETHOD()
        print("%s._disp_methods_ = [" % body.itf.name, file=self.stream)
        for m in body.itf.members:
            if isinstance(m, typedesc.DispMethod):
                self.make_DispMethod(m)
            elif isinstance(m, typedesc.DispProperty):
                self.make_DispProperty(m)
            else:
                raise TypeError(m)
        print("]", file=self.stream)

    ################################################################
    # non-toplevel method generators
    #
    def make_ComMethod(self, m, isdual):
        # typ, name, idlflags, default
        if isdual:
            idlflags = [dispid(m.memid)] + m.idlflags
        else:
            # We don't include the dispid for non-dispatch COM interfaces
            idlflags = m.idlflags
        if __debug__ and m.doc:
            idlflags.insert(1, helpstring(m.doc))
        code = "    COMMETHOD(%r, %s, '%s'" % (
            idlflags,
            self.type_name(m.returns),
            m.name)

        if not m.arguments:
            print("%s)," % code, file=self.stream)
        else:
            print("%s," % code, file=self.stream)
            self.stream.write("              ")
            arglist = []
            for typ, name, idlflags, default in m.arguments:
                type_name = self.type_name(typ)
                ###########################################################
                # IDL files that contain 'open arrays' or 'conformant
                # varying arrays' method parameters are strange.
                # These arrays have both a 'size_is()' and
                # 'length_is()' attribute, like this example from
                # dia2.idl (in the DIA SDK):
                #
                # interface IDiaSymbol: IUnknown {
                # ...
                #     HRESULT get_dataBytes(
                #         [in] DWORD cbData,
                #         [out] DWORD *pcbData,
                #         [out, size_is(cbData),
                #          length_is(*pcbData)] BYTE data[]
                #     );
                #
                # The really strange thing is that the decompiled type
                # library then contains this declaration, which declares
                # the interface itself as [out] method parameter:
                #
                # interface IDiaSymbol: IUnknown {
                # ...
                #     HRESULT _stdcall get_dataBytes(
                #         [in] unsigned long cbData,
                #         [out] unsigned long* pcbData,
                #         [out] IDiaSymbol data);
                #
                # Of course, comtypes does not accept a COM interface
                # as method parameter; so replace the parameter type
                # with the comtypes spelling of 'unsigned char *', and
                # mark the parameter as [in, out], so the IDL
                # equivalent would be like this:
                #
                # interface IDiaSymbol: IUnknown {
                # ...
                #     HRESULT _stdcall get_dataBytes(
                #         [in] unsigned long cbData,
                #         [out] unsigned long* pcbData,
                #         [in, out] BYTE data[]);
                ###########################################################
                if isinstance(typ, typedesc.ComInterface):
                    self.need_OPENARRAYS()
                    type_name = "OPENARRAY"
                    if 'in' not in idlflags:
                        idlflags.append('in')
                if 'lcid' in idlflags:# and 'in' in idlflags:
                    default = lcid
                if default is not None:
                    self.need_VARIANT_imports(default)
                    arglist.append("( %r, %s, '%s', %r )" % (
                        idlflags,
                        type_name,
                        name,
                        default))
                else:
                    arglist.append("( %r, %s, '%s' )" % (
                        idlflags,
                        type_name,
                        name))
            self.stream.write(",\n              ".join(arglist))
            print("),", file=self.stream)

    def make_DispMethod(self, m):
        idlflags = [dispid(m.dispid)] + m.idlflags
        if __debug__ and m.doc:
            idlflags.insert(1, helpstring(m.doc))
        # typ, name, idlflags, default
        code = "    DISPMETHOD(%r, %s, '%s'" % (
            idlflags,
            self.type_name(m.returns),
            m.name)

        if not m.arguments:
            print("%s)," % code, file=self.stream)
        else:
            print("%s," % code, file=self.stream)
            self.stream.write("               ")
            arglist = []
            for typ, name, idlflags, default in m.arguments:
                self.need_VARIANT_imports(default)
                if default is not None:
                    arglist.append("( %r, %s, '%s', %r )" % (
                        idlflags,
                        self.type_name(typ),
                        name,
                        default))
                else:
                    arglist.append("( %r, %s, '%s' )" % (
                        idlflags,
                        self.type_name(typ),
                        name,
                        ))
            self.stream.write(",\n               ".join(arglist))
            print("),", file=self.stream)

    def make_DispProperty(self, prop):
        idlflags = [dispid(prop.dispid)] + prop.idlflags
        if __debug__ and prop.doc:
            idlflags.insert(1, helpstring(prop.doc))
        print("    DISPPROPERTY(%r, %s, '%s')," % (
            idlflags,
            self.type_name(prop.typ),
            prop.name), file=self.stream)

# shortcut for development
if __name__ == "__main__":
    from . import tlbparser
    tlbparser.main()
