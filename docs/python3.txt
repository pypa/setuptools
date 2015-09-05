=====================================================
Supporting both Python 2 and Python 3 with Setuptools
=====================================================

Starting with Distribute version 0.6.2 and Setuptools 0.7, the Setuptools
project supported Python 3. Installing and
using setuptools for Python 3 code works exactly the same as for Python 2
code.

Setuptools provides a facility to invoke 2to3 on the code as a part of the
build process, by setting the keyword parameter ``use_2to3`` to True, but
the Setuptools strongly recommends instead developing a unified codebase
using `six <https://pypi.python.org/pypi/six>`_,
`future <https://pypi.python.org/pypi/future>`_, or another compatibility
library.


Using 2to3
==========

Setuptools attempts to make the porting process easier by automatically
running
2to3 as a part of running tests. To do so, you need to configure the
setup.py so that you can run the unit tests with ``python setup.py test``.

See :ref:`test` for more information on this.

Once you have the tests running under Python 2, you can add the use_2to3
keyword parameters to setup(), and start running the tests under Python 3.
The test command will now first run the build command during which the code
will be converted with 2to3, and the tests will then be run from the build
directory, as opposed from the source directory as is normally done.

Setuptools will convert all Python files, and also all doctests in Python
files. However, if you have doctests located in separate text files, these
will not automatically be converted. By adding them to the
``convert_2to3_doctests`` keyword parameter Setuptools will convert them as
well.

By default, the conversion uses all fixers in the ``lib2to3.fixers`` package.
To use additional fixers, the parameter ``use_2to3_fixers`` can be set
to a list of names of packages containing fixers. To exclude fixers, the
parameter ``use_2to3_exclude_fixers`` can be set to fixer names to be
skipped.

An example setup.py might look something like this::

    from setuptools import setup

    setup(
        name='your.module',
        version='1.0',
        description='This is your awesome module',
        author='You',
        author_email='your@email',
        package_dir={'': 'src'},
        packages=['your', 'you.module'],
        test_suite='your.module.tests',
        use_2to3=True,
        convert_2to3_doctests=['src/your/module/README.txt'],
        use_2to3_fixers=['your.fixers'],
        use_2to3_exclude_fixers=['lib2to3.fixes.fix_import'],
    )

Differential conversion
-----------------------

Note that a file will only be copied and converted during the build process
if the source file has been changed. If you add a file to the doctests
that should be converted, it will not be converted the next time you run
the tests, since it hasn't been modified. You need to remove it from the
build directory. Also if you run the build, install or test commands before
adding the use_2to3 parameter, you will have to remove the build directory
before you run the test command, as the files otherwise will seem updated,
and no conversion will happen.

In general, if code doesn't seem to be converted, deleting the build directory
and trying again is a good safeguard against the build directory getting
"out of sync" with the source directory.

Distributing Python 3 modules
=============================

You can distribute your modules with Python 3 support in different ways. A
normal source distribution will work, but can be slow in installing, as the
2to3 process will be run during the install. But you can also distribute
the module in binary format, such as a binary egg. That egg will contain the
already converted code, and hence no 2to3 conversion is needed during install.

Advanced features
=================

If you don't want to run the 2to3 conversion on the doctests in Python files,
you can turn that off by setting ``setuptools.use_2to3_on_doctests = False``.
