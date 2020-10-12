===================================
Contributing to the documentation
===================================
This is to provide some guidance on contributing to setuptools'
documentation for those unfamiliar with sphinx. setuptools' documentation is built using 
`Sphinx <https://pypi.org/project/Sphinx/>`_ and written in `reStructuredText <https://docutils.sourceforge.io/rst.html>`_.

First navigate to the ``docs/`` folder. Some dependencies are required to build the 
documentation::

  pip install -r requirements.txt

Then, invoke the ``make`` program to build the documentation in the desired
format. For example::

  make html

.. note::
  Learn more about the `make program <https://en.wikipedia.org/wiki/Make_(software)>`_
  and `pip install <https://pip.pypa.io/en/stable/reference/pip_install/#id18>`_

Configuring the build process
=============================
The configuration for sphinx is written in ``conf.py``. As of now, the
entry point is ``index.rst`` in ``docs/`` directory. It creates links
to files nested deeper in the directory.
