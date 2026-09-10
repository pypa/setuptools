``Wheel.install_as_egg`` no longer creates namespace package directories
outside of the destination egg directory. Entries in a wheel's
``namespace_packages.txt`` were split on ``.`` and passed straight to
``os.path.join``, so an entry that was absolute, drive-qualified, or UNC
discarded the destination and placed an ``__init__.py`` at a path chosen by
the wheel. Namespace entries are now validated as dotted module names on
every platform -- see GHSA-xmj3-9gf7-h52w.

This code path is reached only by the deprecated ``setup_requires``
mechanism when ``setup()`` is invoked outside a PEP 517 frontend; the
setuptools build backend never reaches it.
