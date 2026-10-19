``setuptools.wheel.Wheel.install_as_egg`` no longer creates namespace package
directories outside of the egg directory. Entries in a wheel's
``namespace_packages.txt`` were joined onto the egg directory without
validation, so an absolute or drive-qualified entry caused an ``__init__.py``
to be written elsewhere on the filesystem. Such entries now raise
``UnsafeMember``, as unsafe archive members already do.
