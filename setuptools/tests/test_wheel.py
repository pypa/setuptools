# -*- coding: utf-8 -*-

"""wheel tests
"""

from distutils.sysconfig import get_config_var
from distutils.util import get_platform
import contextlib
import glob
import inspect
import os
import subprocess
import sys

import pytest

from pkg_resources import Distribution, PathMetadata, PY_MAJOR
from setuptools.wheel import Wheel

from .contexts import tempdir
from .files import build_files
from .textwrap import DALS


WHEEL_INFO_TESTS = (
    ('invalid.whl', ValueError),
    ('simplewheel-2.0-1-py2.py3-none-any.whl', {
        'project_name': 'simplewheel',
        'version': '2.0',
        'build': '1',
        'py_version': 'py2.py3',
        'abi': 'none',
        'platform': 'any',
    }),
    ('simple.dist-0.1-py2.py3-none-any.whl', {
        'project_name': 'simple.dist',
        'version': '0.1',
        'build': None,
        'py_version': 'py2.py3',
        'abi': 'none',
        'platform': 'any',
    }),
    ('example_pkg_a-1-py3-none-any.whl', {
        'project_name': 'example_pkg_a',
        'version': '1',
        'build': None,
        'py_version': 'py3',
        'abi': 'none',
        'platform': 'any',
    }),
    ('PyQt5-5.9-5.9.1-cp35.cp36.cp37-abi3-manylinux1_x86_64.whl', {
        'project_name': 'PyQt5',
        'version': '5.9',
        'build': '5.9.1',
        'py_version': 'cp35.cp36.cp37',
        'abi': 'abi3',
        'platform': 'manylinux1_x86_64',
    }),
)

@pytest.mark.parametrize(
    ('filename', 'info'), WHEEL_INFO_TESTS,
    ids=[t[0] for t in WHEEL_INFO_TESTS]
)
def test_wheel_info(filename, info):
    if inspect.isclass(info):
        with pytest.raises(info):
            Wheel(filename)
        return
    w = Wheel(filename)
    assert {k: getattr(w, k) for k in info.keys()} == info


@contextlib.contextmanager
def build_wheel(extra_file_defs=None, **kwargs):
    file_defs = {
        'setup.py': (DALS(
            '''
            # -*- coding: utf-8 -*-
            from setuptools import setup
            import setuptools
            setup(**%r)
            '''
        ) % kwargs).encode('utf-8'),
    }
    if extra_file_defs:
        file_defs.update(extra_file_defs)
    with tempdir() as source_dir:
        build_files(file_defs, source_dir)
        subprocess.check_call((sys.executable, 'setup.py',
                               '-q', 'bdist_wheel'), cwd=source_dir)
        yield glob.glob(os.path.join(source_dir, 'dist', '*.whl'))[0]


def tree(root):
    def depth(path):
        return len(path.split(os.path.sep))
    def prefix(path_depth):
        if not path_depth:
            return ''
        return '|  ' * (path_depth - 1) + '|-- '
    lines = []
    root_depth = depth(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        filenames.sort()
        dir_depth = depth(dirpath) - root_depth
        if dir_depth > 0:
            lines.append('%s%s/' % (prefix(dir_depth - 1),
                                    os.path.basename(dirpath)))
        for f in filenames:
            lines.append('%s%s' % (prefix(dir_depth), f))
    return '\n'.join(lines) + '\n'


def _check_wheel_install(filename, install_dir, install_tree,
                         project_name, version, requires_txt):
    w = Wheel(filename)
    egg_path = os.path.join(install_dir, w.egg_name())
    w.install_as_egg(egg_path)
    if install_tree is not None:
        install_tree = install_tree.format(
            py_version=PY_MAJOR,
            platform=get_platform(),
            shlib_ext=get_config_var('EXT_SUFFIX') or get_config_var('SO')
        )
        assert install_tree == tree(install_dir)
    metadata = PathMetadata(egg_path, os.path.join(egg_path, 'EGG-INFO'))
    dist = Distribution.from_filename(egg_path, metadata=metadata)
    assert dist.project_name == project_name
    assert dist.version == version
    if requires_txt is None:
        assert not dist.has_metadata('requires.txt')
    else:
        assert requires_txt == dist.get_metadata('requires.txt').lstrip()


class Record(object):

    def __init__(self, id, **kwargs):
        self._id = id
        self._fields = kwargs

    def __repr__(self):
        return '%s(**%r)' % (self._id, self._fields)


WHEEL_INSTALL_TESTS = (

    dict(
        id='basic',
        file_defs={
            'foo': {
                '__init__.py': ''
            }
        },
        setup_kwargs=dict(
            packages=['foo'],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- top_level.txt
            |-- foo/
            |  |-- __init__.py
            '''
        ),
    ),

    dict(
        id='utf-8',
        setup_kwargs=dict(
            description='Description accentuée',
        )
    ),

    dict(
        id='data',
        file_defs={
            'data.txt': DALS(
                '''
                Some data...
                '''
            ),
        },
        setup_kwargs=dict(
            data_files=[('data_dir', ['data.txt'])],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- top_level.txt
            |-- data_dir/
            |  |-- data.txt
            '''
        ),
    ),

    dict(
        id='extension',
        file_defs={
            'extension.c': DALS(
                '''
                #include "Python.h"

                #if PY_MAJOR_VERSION >= 3

                static struct PyModuleDef moduledef = {
                        PyModuleDef_HEAD_INIT,
                        "extension",
                        NULL,
                        0,
                        NULL,
                        NULL,
                        NULL,
                        NULL,
                        NULL
                };

                #define INITERROR return NULL

                PyMODINIT_FUNC PyInit_extension(void)

                #else

                #define INITERROR return

                void initextension(void)

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
                '''
            ),
        },
        setup_kwargs=dict(
            ext_modules=[
                Record('setuptools.Extension',
                       name='extension',
                       sources=['extension.c'])
            ],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}-{platform}.egg/
            |-- extension{shlib_ext}
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- top_level.txt
            '''
        ),
    ),

    dict(
        id='header',
        file_defs={
            'header.h': DALS(
                '''
                '''
            ),
        },
        setup_kwargs=dict(
            headers=['header.h'],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- header.h
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- top_level.txt
            '''
        ),
    ),

    dict(
        id='script',
        file_defs={
            'script.py': DALS(
                '''
                #/usr/bin/python
                print('hello world!')
                '''
            ),
            'script.sh': DALS(
                '''
                #/bin/sh
                echo 'hello world!'
                '''
            ),
        },
        setup_kwargs=dict(
            scripts=['script.py', 'script.sh'],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- top_level.txt
            |  |-- scripts/
            |  |  |-- script.py
            |  |  |-- script.sh
            '''
        ),
    ),

    dict(
        id='requires1',
        install_requires='foobar==2.0',
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- requires.txt
            |  |-- top_level.txt
            '''),
        requires_txt=DALS(
            '''
            foobar==2.0
            '''
        ),
    ),

    dict(
        id='requires2',
        install_requires='''
        bar
        foo<=2.0; %r in sys_platform
        ''' % sys.platform,
        requires_txt=DALS(
            '''
            bar
            foo<=2.0
            '''
        ),
    ),

    dict(
        id='requires3',
        install_requires='''
        bar; %r != sys_platform
        ''' % sys.platform,
    ),

    dict(
        id='requires4',
        install_requires='''
        foo
        ''',
        extras_require={
            'extra': 'foobar>3',
        },
        requires_txt=DALS(
            '''
            foo

            [extra]
            foobar>3
            '''
        ),
    ),

    dict(
        id='requires5',
        extras_require={
            'extra': 'foobar; %r != sys_platform' % sys.platform,
        },
        requires_txt=DALS(
            '''
            [extra]
            '''
        ),
    ),

    dict(
        id='namespace_package',
        file_defs={
            'foo': {
                'bar': {
                    '__init__.py': ''
                },
            },
        },
        setup_kwargs=dict(
            namespace_packages=['foo'],
            packages=['foo.bar'],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- foo-1.0-py{py_version}-nspkg.pth
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- namespace_packages.txt
            |  |-- top_level.txt
            |-- foo/
            |  |-- __init__.py
            |  |-- bar/
            |  |  |-- __init__.py
            '''),
    ),

    dict(
        id='data_in_package',
        file_defs={
            'foo': {
                '__init__.py': '',
                'data_dir': {
                    'data.txt': DALS(
                        '''
                        Some data...
                        '''
                    ),
                }
            }
        },
        setup_kwargs=dict(
            packages=['foo'],
            data_files=[('foo/data_dir', ['foo/data_dir/data.txt'])],
        ),
        install_tree=DALS(
            '''
            foo-1.0-py{py_version}.egg/
            |-- EGG-INFO/
            |  |-- DESCRIPTION.rst
            |  |-- PKG-INFO
            |  |-- RECORD
            |  |-- WHEEL
            |  |-- metadata.json
            |  |-- top_level.txt
            |-- foo/
            |  |-- __init__.py
            |  |-- data_dir/
            |  |  |-- data.txt
            '''
        ),
    ),

)

@pytest.mark.parametrize(
    'params', WHEEL_INSTALL_TESTS,
    ids=list(params['id'] for params in WHEEL_INSTALL_TESTS),
)
def test_wheel_install(params):
    project_name = params.get('name', 'foo')
    version = params.get('version', '1.0')
    install_requires = params.get('install_requires', [])
    extras_require = params.get('extras_require', {})
    requires_txt = params.get('requires_txt', None)
    install_tree = params.get('install_tree')
    file_defs = params.get('file_defs', {})
    setup_kwargs = params.get('setup_kwargs', {})
    with build_wheel(
        name=project_name,
        version=version,
        install_requires=install_requires,
        extras_require=extras_require,
        extra_file_defs=file_defs,
        **setup_kwargs
    ) as filename, tempdir() as install_dir:
        _check_wheel_install(filename, install_dir,
                             install_tree, project_name,
                             version, requires_txt)
