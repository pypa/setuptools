Running ``setuptools`` commands
===============================

Historically, ``setuptools`` allowed running commands via a ``setup.py`` script
at the root of a Python project, as indicated in the examples below::

    python setup.py --help
    python setup.py --help-commands
    python setup.py --version
    python setup.py sdist
    python setup.py bdist_wheel

You could also run commands in other circumstances:

* ``setuptools`` projects without ``setup.py`` (e.g. ``setup.cfg``-only)::

   python -c "import setuptools; setup()" --help

* ``distutils`` projects (with a ``setup.py`` importing ``distutils``)::

   python -c "import setuptools; with open('setup.py') as f: exec(compile(f.read(), 'setup.py', 'exec'))" develop

That is, you can simply list the normal setup commands and options following the quoted part.
