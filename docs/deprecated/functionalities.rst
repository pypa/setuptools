"Eggsecutable" Scripts
----------------------

.. deprecated:: 45.3.0

Occasionally, there are situations where it's desirable to make an ``.egg``
file directly executable.  You can do this by including an entry point such
as the following::

    setup(
        # other arguments here...
        entry_points={
            "setuptools.installation": [
                "eggsecutable = my_package.some_module:main_func",
            ]
        }
    )

Any eggs built from the above setup script will include a short executable
prelude that imports and calls ``main_func()`` from ``my_package.some_module``.
The prelude can be run on Unix-like platforms (including Mac and Linux) by
invoking the egg with ``/bin/sh``, or by enabling execute permissions on the
``.egg`` file.  For the executable prelude to run, the appropriate version of
Python must be available via the ``PATH`` environment variable, under its
"long" name.  That is, if the egg is built for Python 2.3, there must be a
``python2.3`` executable present in a directory on ``PATH``.

IMPORTANT NOTE: Eggs with an "eggsecutable" header cannot be renamed, or
invoked via symlinks.  They *must* be invoked using their original filename, in
order to ensure that, once running, ``pkg_resources`` will know what project
and version is in use.  The header script will check this and exit with an
error if the ``.egg`` file has been renamed or is invoked via a symlink that
changes its base name.
