# util.py
import warnings
import types
import collections
import itertools


_bslash = chr(92)


class __config_flags:
    """Internal class for defining compatibility and debugging flags"""

    _all_names = []
    _fixed_names = []
    _type_desc = "configuration"

    @classmethod
    def _set(cls, dname, value):
        if dname in cls._fixed_names:
            warnings.warn(
                "{}.{} {} is {} and cannot be overridden".format(
                    cls.__name__,
                    dname,
                    cls._type_desc,
                    str(getattr(cls, dname)).upper(),
                )
            )
            return
        if dname in cls._all_names:
            setattr(cls, dname, value)
        else:
            raise ValueError("no such {} {!r}".format(cls._type_desc, dname))

    enable = classmethod(lambda cls, name: cls._set(name, True))
    disable = classmethod(lambda cls, name: cls._set(name, False))


def col(loc, strg):
    """Returns current column within a string, counting newlines as line separators.
   The first column is number 1.

   Note: the default parsing behavior is to expand tabs in the input string
   before starting the parsing process.  See
   :class:`ParserElement.parseString` for more
   information on parsing strings containing ``<TAB>`` s, and suggested
   methods to maintain a consistent view of the parsed string, the parse
   location, and line and column positions within the parsed string.
   """
    s = strg
    return 1 if 0 < loc < len(s) and s[loc - 1] == "\n" else loc - s.rfind("\n", 0, loc)


def lineno(loc, strg):
    """Returns current line number within a string, counting newlines as line separators.
    The first line is number 1.

    Note - the default parsing behavior is to expand tabs in the input string
    before starting the parsing process.  See :class:`ParserElement.parseString`
    for more information on parsing strings containing ``<TAB>`` s, and
    suggested methods to maintain a consistent view of the parsed string, the
    parse location, and line and column positions within the parsed string.
    """
    return strg.count("\n", 0, loc) + 1


def line(loc, strg):
    """Returns the line of text containing loc within a string, counting newlines as line separators.
       """
    lastCR = strg.rfind("\n", 0, loc)
    nextCR = strg.find("\n", loc)
    return strg[lastCR + 1 : nextCR] if nextCR >= 0 else strg[lastCR + 1 :]


class _UnboundedCache:
    def __init__(self):
        cache = {}
        cache_get = cache.get
        self.not_in_cache = not_in_cache = object()

        def get(self, key):
            return cache_get(key, not_in_cache)

        def set(self, key, value):
            cache[key] = value

        def clear(self):
            cache.clear()

        def cache_len(self):
            return len(cache)

        self.size = None
        self.get = types.MethodType(get, self)
        self.set = types.MethodType(set, self)
        self.clear = types.MethodType(clear, self)
        self.__len__ = types.MethodType(cache_len, self)


class _FifoCache:
    def __init__(self, size):
        self.not_in_cache = not_in_cache = object()
        cache = collections.OrderedDict()
        cache_get = cache.get

        def get(self, key):
            return cache_get(key, not_in_cache)

        def set(self, key, value):
            cache[key] = value
            try:
                while len(cache) > size:
                    cache.popitem(last=False)
            except KeyError:
                pass

        def clear(self):
            cache.clear()

        def cache_len(self):
            return len(cache)

        self.size = size
        self.get = types.MethodType(get, self)
        self.set = types.MethodType(set, self)
        self.clear = types.MethodType(clear, self)
        self.__len__ = types.MethodType(cache_len, self)


def _escapeRegexRangeChars(s):
    # escape these chars: ^-[]
    for c in r"\^-[]":
        s = s.replace(c, _bslash + c)
    s = s.replace("\n", r"\n")
    s = s.replace("\t", r"\t")
    return str(s)


def _collapseStringToRanges(s, re_escape=True):
    def is_consecutive(c):
        c_int = ord(c)
        is_consecutive.prev, prev = c_int, is_consecutive.prev
        if c_int - prev > 1:
            is_consecutive.value = next(is_consecutive.counter)
        return is_consecutive.value

    is_consecutive.prev = 0
    is_consecutive.counter = itertools.count()
    is_consecutive.value = -1

    def escape_re_range_char(c):
        return "\\" + c if c in r"\^-][" else c

    if not re_escape:
        escape_re_range_char = lambda c: c

    ret = []
    for _, chars in itertools.groupby(sorted(s), key=is_consecutive):
        first = last = next(chars)
        for c in chars:
            last = c
        if first == last:
            ret.append(escape_re_range_char(first))
        else:
            ret.append(
                "{}-{}".format(escape_re_range_char(first), escape_re_range_char(last))
            )
    return "".join(ret)


def _flatten(L):
    ret = []
    for i in L:
        if isinstance(i, list):
            ret.extend(_flatten(i))
        else:
            ret.append(i)
    return ret
