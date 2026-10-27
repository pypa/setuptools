"""Tests for distutils.extension."""

from __future__ import annotations

import os
import pathlib
import re
import warnings
from dataclasses import field
from distutils._dataclass import lenient_dataclass
from distutils.extension import Extension, read_setup_file
from inspect import cleandoc

import pytest


class TestExtension:
    def test_read_setup_file(self):
        # trying to read a Setup file
        # (sample extracted from the PyGame project)
        setup = os.path.join(os.path.dirname(__file__), 'Setup.sample')

        exts = read_setup_file(setup)
        names = [ext.name for ext in exts]
        names.sort()

        # here are the extensions read_setup_file should have created
        # out of the file
        wanted = [
            '_arraysurfarray',
            '_camera',
            '_numericsndarray',
            '_numericsurfarray',
            'base',
            'bufferproxy',
            'cdrom',
            'color',
            'constants',
            'display',
            'draw',
            'event',
            'fastevent',
            'font',
            'gfxdraw',
            'image',
            'imageext',
            'joystick',
            'key',
            'mask',
            'mixer',
            'mixer_music',
            'mouse',
            'movie',
            'overlay',
            'pixelarray',
            'pypm',
            'rect',
            'rwobject',
            'scrap',
            'surface',
            'surflock',
            'time',
            'transform',
        ]

        assert names == wanted

    def test_extension_init(self):
        # the first argument, which is the name, must be a string
        with pytest.raises(TypeError, match="'name' must be a string"):
            Extension(1, [])
        ext = Extension('name', [])
        assert ext.name == 'name'

        # the second argument, which is the list of files, must
        # be an iterable of strings or PathLike objects, and not a string
        with pytest.raises(TypeError, match="'sources' must be an iterable"):
            Extension('name', 'file')
        with pytest.raises(TypeError):
            Extension('name', ['file', 1])
        ext = Extension('name', ['file1', 'file2'])
        assert ext.sources == ['file1', 'file2']
        ext = Extension('name', [pathlib.Path('file1'), pathlib.Path('file2')])
        assert ext.sources == ['file1', 'file2']

        # any non-string iterable of strings or PathLike objects should work
        ext = Extension('name', ('file1', 'file2'))  # tuple
        assert ext.sources == ['file1', 'file2']
        ext = Extension('name', {'file1', 'file2'})  # set
        assert sorted(ext.sources) == ['file1', 'file2']
        ext = Extension('name', iter(['file1', 'file2']))  # iterator
        assert ext.sources == ['file1', 'file2']
        ext = Extension('name', [pathlib.Path('file1'), 'file2'])  # mixed types
        assert ext.sources == ['file1', 'file2']

        # others arguments have defaults
        for attr in (
            'include_dirs',
            'define_macros',
            'undef_macros',
            'library_dirs',
            'libraries',
            'runtime_library_dirs',
            'extra_objects',
            'extra_compile_args',
            'extra_link_args',
            'export_symbols',
            'swig_opts',
            'depends',
        ):
            assert getattr(ext, attr) == []

        assert ext.language is None
        assert ext.optional is False

        # if there are unknown keyword options, warn about them
        msg = re.escape("unknown `Extension` options: 'chic'")
        warnings.simplefilter('always')
        with pytest.warns(UserWarning, match=msg) as w:
            ext = Extension('name', ['file1', 'file2'], chic=True)

        assert len(w) == 1


def test_can_be_extended_by_setuptools() -> None:
    # Emulate how it could be extended in setuptools

    @lenient_dataclass()
    class setuptools_Extension(Extension):
        py_limited_api: bool = False
        _full_name: str = field(init=False, repr=False)

    ext1 = setuptools_Extension("name", ["hello.c"], py_limited_api=True)
    assert ext1.py_limited_api is True
    assert ext1.define_macros == []

    # Without __init__ customization the following warning would be an error:
    msg = re.escape("unknown `setuptools_Extension` options: 'world'")
    with pytest.warns(UserWarning, match=msg):
        ext2 = setuptools_Extension("name", ["hello.c"], world=True)  # type: ignore[call-arg]

    assert "world" not in ext2.__dict__
    assert ext2.py_limited_api is False
    assert "_full_name" not in ext2.__dict__  # not initialized by default
    ext2._full_name = "hello world"  # can still be set in build_ext
    assert ext2._full_name == "hello world"


TYPE_INFERENCE = {
    # Simple example
    """
    from distutils.extension import Extension

    reveal_type(Extension.__init__)
    """: [
        "name: builtins.str",
        "sources: typing.Iterable[builtins.str | os.PathLike[builtins.str]]",
        "include_dirs: builtins.list[builtins.str]",
    ],
    # Inheritance example
    """
    from dataclasses import field
    from distutils._dataclass import lenient_dataclass
    from distutils.extension import Extension

    @lenient_dataclass()
    class setuptools_Extension(Extension):
        py_limited_api: bool = False
        _full_name: str = field(init=False, repr=False)

    reveal_type(setuptools_Extension.__init__)
    """: [
        "libraries: builtins.list[builtins.str]",
        "swig_opts: builtins.list[builtins.str]",
        "py_limited_api: builtins.bool",
        "_full_name: builtins.str",
    ],
}


@pytest.mark.filterwarnings("ignore::EncodingWarning")  # mypy.api.run
@pytest.mark.parametrize("example,expectations", TYPE_INFERENCE.items())
def test_inference_sanity_check(
    tmp_path: pathlib.Path, example: str, expectations: list[str]
) -> None:
    """Ensure type inference is working well for Extension and subclasses"""
    # Skip where mypy is unavailable (e.g. PyPy, cygwin/mingw), as the
    # static type checker tests do naturally via the pytest plugin.
    api = pytest.importorskip("mypy.api")

    f = tmp_path / "typecheck_file.py"
    f.write_text(cleandoc(example), encoding="utf-8")

    # Use an empty config file to avoid interference with test.
    empty = tmp_path / "empty"
    empty.touch()
    # --no-color-output keeps ANSI escapes (emitted on some platforms, e.g.
    # Windows CI) out of the report so the substring checks below match.
    result = api.run([
        os.fspath(f),
        "--config-file",
        os.fspath(empty),
        "--no-color-output",
    ])

    separator = 'note: Revealed type is "def (self:'
    assert separator in result[0]
    _, _, note = result[0].partition(separator)

    # mypy includes or omits the `builtins.` prefix depending on its version;
    # normalize it away so the check is robust across versions.
    note = note.replace("builtins.", "")
    for expectation in expectations:
        assert expectation.replace("builtins.", "") in note
