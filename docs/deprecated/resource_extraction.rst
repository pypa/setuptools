.. _Automatic Resource Extraction:

Automatic Resource Extraction
=============================

In a modern setup, Python packages are usually installed as directories,
and all the files can be found on deterministic locations on the disk.
This means that most of the tools expect package resources to be "real" files.

There are a few occasions however that packages are loaded in a different way
(e.g., from a zip file), which is incompatible with the assumptions mentioned above.
Moreover, a package developer may also include non-extension native libraries or other files that
C extensions may expect to be able to access.

In these scenarios, the use of :mod:`importlib.resources` is recommended.

Old implementations (prior to the advent of :mod:`importlib.resources`) and
long-living projects, however, may still rely on the library ``pkg_resources``
to access these files.

If you have to support such systems, or want to provide backward compatibility
for ``pkg_resources``, you may need to add an special configuration
to ``setuptools`` when packaging a project.
This can be done by listing as ``eager_resources`` (argument to ``setup()``
in ``setup.py`` or field in ``setup.cfg``) all the files that need to be
extracted together, whenever a C extension in the project is imported.

This is especially important if your project includes shared libraries *other*
than ``distutils``/``setuptools``-built C extensions, and those shared libraries use file
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
