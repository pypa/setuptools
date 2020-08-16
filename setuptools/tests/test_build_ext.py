import sys
import distutils.command.build_ext as orig
from distutils.sysconfig import get_config_var

from setuptools.command.build_ext import build_ext, get_abi3_suffix
from setuptools.dist import Distribution
from setuptools.extension import Extension

from . import environment
from .files import build_files
from .textwrap import DALS


class TestBuildExt:
    def test_get_ext_filename(self):
        """
        Setuptools needs to give back the same
        result as distutils, even if the fullname
        is not in ext_map.
        """
        dist = Distribution()
        cmd = build_ext(dist)
        cmd.ext_map['foo/bar'] = ''
        res = cmd.get_ext_filename('foo')
        wanted = orig.build_ext.get_ext_filename(cmd, 'foo')
        assert res == wanted

    def test_abi3_filename(self):
        """
        Filename needs to be loadable by several versions
        of Python 3 if 'is_abi3' is truthy on Extension()
        """
        print(get_abi3_suffix())

        extension = Extension('spam.eggs', ['eggs.c'], py_limited_api=True)
        dist = Distribution(dict(ext_modules=[extension]))
        cmd = build_ext(dist)
        cmd.finalize_options()
        assert 'spam.eggs' in cmd.ext_map
        res = cmd.get_ext_filename('spam.eggs')

        if not get_abi3_suffix():
            assert res.endswith(get_config_var('EXT_SUFFIX'))
        elif sys.platform == 'win32':
            assert res.endswith('eggs.pyd')
        else:
            assert 'abi3' in res


def test_build_ext_config_handling(tmpdir_cwd):
    files = {
        'setup.py': DALS(
            """
            from setuptools import Extension, setup
            setup(
                name='foo',
                version='0.0.0',
                ext_modules=[Extension('foo', ['foo.c'])],
            )
            """),
        'foo.c': DALS(
            """
            #include "Python.h"

            #if PY_MAJOR_VERSION >= 3

            static struct PyModuleDef moduledef = {
                    PyModuleDef_HEAD_INIT,
                    "foo",
                    NULL,
                    0,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL
            };

            #define INITERROR return NULL

            PyMODINIT_FUNC PyInit_foo(void)

            #else

            #define INITERROR return

            void initfoo(void)

            #endif
            {
            #if PY_MAJOR_VERSION >= 3
                PyObject *module = PyModule_Create(&moduledef);
            #else
                PyObject *module = Py_InitModule("extension", NULL);
            #endif
                if (module == NULL)
                    INITERROR;
            #if PY_MAJOR_VERSION >= 3
                return module;
            #endif
            }
            """),
        'setup.cfg': DALS(
            """
            [build]
            build-base = foo_build
            """),
    }
    build_files(files)
    code, output = environment.run_setup_py(
        cmd=['build'], data_stream=(0, 2),
    )
    assert code == 0, '\nSTDOUT:\n%s\nSTDERR:\n%s' % output
