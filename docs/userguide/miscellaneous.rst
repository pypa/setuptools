.. _Automatic Resource Extraction:

Automatic Resource Extraction
-----------------------------

If you are using tools that expect your resources to be "real" files, or your
project includes non-extension native libraries or other files that your C
extensions expect to be able to access, you may need to list those files in
the ``eager_resources`` argument to ``setup()``, so that the files will be
extracted together, whenever a C extension in the project is imported.

This is especially important if your project includes shared libraries *other*
than distutils-built C extensions, and those shared libraries use file
extensions other than ``.dll``, ``.so``, or ``.dylib``, which are the
extensions that setuptools 0.6a8 and higher automatically detects as shared
libraries and adds to the ``native_libs.txt`` file for you.  Any shared
libraries whose names do not end with one of those extensions should be listed
as ``eager_resources``, because they need to be present in the filesystem when
he C extensions that link to them are used.

The ``pkg_resources`` runtime for compressed packages will automatically
extract *all* C extensions and ``eager_resources`` at the same time, whenever
*any* C extension or eager resource is requested via the ``resource_filename()``
API.  (C extensions are imported using ``resource_filename()`` internally.)
This ensures that C extensions will see all of the "real" files that they
expect to see.

Note also that you can list directory resource names in ``eager_resources`` as
well, in which case the directory's contents (including subdirectories) will be
extracted whenever any C extension or eager resource is requested.

Please note that if you're not sure whether you need to use this argument, you
don't!  It's really intended to support projects with lots of non-Python
dependencies and as a last resort for crufty projects that can't otherwise
handle being compressed.  If your package is pure Python, Python plus data
files, or Python plus C, you really don't need this.  You've got to be using
either C or an external program that needs "real" files in your project before
there's any possibility of ``eager_resources`` being relevant to your project.

Defining Additional Metadata
----------------------------

Some extensible applications and frameworks may need to define their own kinds
of metadata to include in eggs, which they can then access using the
``pkg_resources`` metadata APIs.  Ordinarily, this is done by having plugin
developers include additional files in their ``ProjectName.egg-info``
directory.  However, since it can be tedious to create such files by hand, you
may want to create a distutils extension that will create the necessary files
from arguments to ``setup()``, in much the same way that ``setuptools`` does
for many of the ``setup()`` arguments it adds.  See the section below on
:ref:`Creating ``distutils\`\` Extensions` for more details, especially the
subsection on :ref:`Adding new EGG-INFO Files`.

Setting the ``zip_safe`` flag
-----------------------------

For some use cases (such as bundling as part of a larger application), Python
packages may be run directly from a zip file.
Not all packages, however, are capable of running in compressed form, because
they may expect to be able to access either source code or data files as
normal operating system files.  So, ``setuptools`` can install your project
as a zipfile or a directory, and its default choice is determined by the
project's ``zip_safe`` flag.

You can pass a True or False value for the ``zip_safe`` argument to the
``setup()`` function, or you can omit it.  If you omit it, the ``bdist_egg``
command will analyze your project's contents to see if it can detect any
conditions that would prevent it from working in a zipfile.  It will output
notices to the console about any such conditions that it finds.

Currently, this analysis is extremely conservative: it will consider the
project unsafe if it contains any C extensions or datafiles whatsoever.  This
does *not* mean that the project can't or won't work as a zipfile!  It just
means that the ``bdist_egg`` authors aren't yet comfortable asserting that
the project *will* work.  If the project contains no C or data files, and does
no ``__file__`` or ``__path__`` introspection or source code manipulation, then
there is an extremely solid chance the project will work when installed as a
zipfile.  (And if the project uses ``pkg_resources`` for all its data file
access, then C extensions and other data files shouldn't be a problem at all.
See the :ref:`Accessing Data Files at Runtime` section above for more information.)

However, if ``bdist_egg`` can't be *sure* that your package will work, but
you've checked over all the warnings it issued, and you are either satisfied it
*will* work (or if you want to try it for yourself), then you should set
``zip_safe`` to ``True`` in your ``setup()`` call.  If it turns out that it
doesn't work, you can always change it to ``False``, which will force
``setuptools`` to install your project as a directory rather than as a zipfile.

In the future, as we gain more experience with different packages and become
more satisfied with the robustness of the ``pkg_resources`` runtime, the
"zip safety" analysis may become less conservative.  However, we strongly
recommend that you determine for yourself whether your project functions
correctly when installed as a zipfile, correct any problems if you can, and
then make an explicit declaration of ``True`` or ``False`` for the ``zip_safe``
flag, so that it will not be necessary for ``bdist_egg`` to try to guess
whether your project can work as a zipfile.
