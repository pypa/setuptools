# unicode.py

import sys
from itertools import filterfalse


class _lazyclassproperty:
    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__
        self.__name__ = fn.__name__

    def __get__(self, obj, cls):
        if cls is None:
            cls = type(obj)
        if not hasattr(cls, "_intern") or any(
            cls._intern is getattr(superclass, "_intern", [])
            for superclass in cls.__mro__[1:]
        ):
            cls._intern = {}
        attrname = self.fn.__name__
        if attrname not in cls._intern:
            cls._intern[attrname] = self.fn(cls)
        return cls._intern[attrname]


class unicode_set:
    """
    A set of Unicode characters, for language-specific strings for
    ``alphas``, ``nums``, ``alphanums``, and ``printables``.
    A unicode_set is defined by a list of ranges in the Unicode character
    set, in a class attribute ``_ranges``, such as::

        _ranges = [(0x0020, 0x007e), (0x00a0, 0x00ff),]

    A unicode set can also be defined using multiple inheritance of other unicode sets::

        class CJK(Chinese, Japanese, Korean):
            pass
    """

    _ranges = []

    @classmethod
    def _get_chars_for_ranges(cls):
        ret = []
        for cc in cls.__mro__:
            if cc is unicode_set:
                break
            for rr in cc._ranges:
                ret.extend(range(rr[0], rr[-1] + 1))
        return [chr(c) for c in sorted(set(ret))]

    @_lazyclassproperty
    def printables(cls):
        "all non-whitespace characters in this range"
        return "".join(filterfalse(str.isspace, cls._get_chars_for_ranges()))

    @_lazyclassproperty
    def alphas(cls):
        "all alphabetic characters in this range"
        return "".join(filter(str.isalpha, cls._get_chars_for_ranges()))

    @_lazyclassproperty
    def nums(cls):
        "all numeric digit characters in this range"
        return "".join(filter(str.isdigit, cls._get_chars_for_ranges()))

    @_lazyclassproperty
    def alphanums(cls):
        "all alphanumeric characters in this range"
        return cls.alphas + cls.nums


class pyparsing_unicode(unicode_set):
    """
    A namespace class for defining common language unicode_sets.
    """

    _ranges = [(32, sys.maxunicode)]

    class Latin1(unicode_set):
        "Unicode set for Latin-1 Unicode Character Range"
        _ranges = [
            (0x0020, 0x007E),
            (0x00A0, 0x00FF),
        ]

    class LatinA(unicode_set):
        "Unicode set for Latin-A Unicode Character Range"
        _ranges = [
            (0x0100, 0x017F),
        ]

    class LatinB(unicode_set):
        "Unicode set for Latin-B Unicode Character Range"
        _ranges = [
            (0x0180, 0x024F),
        ]

    class Greek(unicode_set):
        "Unicode set for Greek Unicode Character Ranges"
        _ranges = [
            (0x0370, 0x03FF),
            (0x1F00, 0x1F15),
            (0x1F18, 0x1F1D),
            (0x1F20, 0x1F45),
            (0x1F48, 0x1F4D),
            (0x1F50, 0x1F57),
            (0x1F59,),
            (0x1F5B,),
            (0x1F5D,),
            (0x1F5F, 0x1F7D),
            (0x1F80, 0x1FB4),
            (0x1FB6, 0x1FC4),
            (0x1FC6, 0x1FD3),
            (0x1FD6, 0x1FDB),
            (0x1FDD, 0x1FEF),
            (0x1FF2, 0x1FF4),
            (0x1FF6, 0x1FFE),
        ]

    class Cyrillic(unicode_set):
        "Unicode set for Cyrillic Unicode Character Range"
        _ranges = [(0x0400, 0x04FF)]

    class Chinese(unicode_set):
        "Unicode set for Chinese Unicode Character Range"
        _ranges = [
            (0x4E00, 0x9FFF),
            (0x3000, 0x303F),
        ]

    class Japanese(unicode_set):
        "Unicode set for Japanese Unicode Character Range, combining Kanji, Hiragana, and Katakana ranges"
        _ranges = []

        class Kanji(unicode_set):
            "Unicode set for Kanji Unicode Character Range"
            _ranges = [
                (0x4E00, 0x9FBF),
                (0x3000, 0x303F),
            ]

        class Hiragana(unicode_set):
            "Unicode set for Hiragana Unicode Character Range"
            _ranges = [
                (0x3040, 0x309F),
            ]

        class Katakana(unicode_set):
            "Unicode set for Katakana  Unicode Character Range"
            _ranges = [
                (0x30A0, 0x30FF),
            ]

    class Korean(unicode_set):
        "Unicode set for Korean Unicode Character Range"
        _ranges = [
            (0xAC00, 0xD7AF),
            (0x1100, 0x11FF),
            (0x3130, 0x318F),
            (0xA960, 0xA97F),
            (0xD7B0, 0xD7FF),
            (0x3000, 0x303F),
        ]

    class CJK(Chinese, Japanese, Korean):
        "Unicode set for combined Chinese, Japanese, and Korean (CJK) Unicode Character Range"
        pass

    class Thai(unicode_set):
        "Unicode set for Thai Unicode Character Range"
        _ranges = [
            (0x0E01, 0x0E3A),
            (0x0E3F, 0x0E5B),
        ]

    class Arabic(unicode_set):
        "Unicode set for Arabic Unicode Character Range"
        _ranges = [
            (0x0600, 0x061B),
            (0x061E, 0x06FF),
            (0x0700, 0x077F),
        ]

    class Hebrew(unicode_set):
        "Unicode set for Hebrew Unicode Character Range"
        _ranges = [
            (0x0590, 0x05FF),
        ]

    class Devanagari(unicode_set):
        "Unicode set for Devanagari Unicode Character Range"
        _ranges = [(0x0900, 0x097F), (0xA8E0, 0xA8FF)]


pyparsing_unicode.Japanese._ranges = (
    pyparsing_unicode.Japanese.Kanji._ranges
    + pyparsing_unicode.Japanese.Hiragana._ranges
    + pyparsing_unicode.Japanese.Katakana._ranges
)

# define ranges in language character sets
pyparsing_unicode.العربية = pyparsing_unicode.Arabic
pyparsing_unicode.中文 = pyparsing_unicode.Chinese
pyparsing_unicode.кириллица = pyparsing_unicode.Cyrillic
pyparsing_unicode.Ελληνικά = pyparsing_unicode.Greek
pyparsing_unicode.עִברִית = pyparsing_unicode.Hebrew
pyparsing_unicode.日本語 = pyparsing_unicode.Japanese
pyparsing_unicode.Japanese.漢字 = pyparsing_unicode.Japanese.Kanji
pyparsing_unicode.Japanese.カタカナ = pyparsing_unicode.Japanese.Katakana
pyparsing_unicode.Japanese.ひらがな = pyparsing_unicode.Japanese.Hiragana
pyparsing_unicode.한국어 = pyparsing_unicode.Korean
pyparsing_unicode.ไทย = pyparsing_unicode.Thai
pyparsing_unicode.देवनागरी = pyparsing_unicode.Devanagari
