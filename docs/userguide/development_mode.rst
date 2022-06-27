Development Mode (a.k.a. "Editable Installs")
=============================================

When creating a Python project, developers usually want to implement and test
changes iteratively, before cutting a release and preparing a distribution archive.

In normal circumstances this can be quite cumbersome and require the developers
to manipulate the ``PATHONPATH`` environment variable or to continuous re-build
and re-install the project.

To facilitate iterative exploration and experimentation, setuptools allows
users to instruct the Python interpreter and its import machinery to load the
code under development directly from the project folder without having to
copy the files to a different location in the disk.
This means that changes in the Python source code can immediately take place
without requiring a new installation.

You can enter this "development mode" by performing an :doc:`editable installation
<pip:topics/local-project-installs>` inside of a :term:`virtual environment`,
using :doc:`pip's <pip:cli/pip_install>` ``-e/--editable`` flag, as shown bellow:

.. code-block:: bash

   $ cd your-python-project
   $ python -m venv .venv
   # Activate your environemt with:
   #      `source .venv/bin/activate` on Unix/macOS
   # or   `.venv\Scripts\activate` on Windows

   $ pip install --editable .

   # Now you have access to your package
   # as if it was installed in .venv
   $ python -c "import your_python_project"


An "editable installation" works very similarly to a regular install with
``pip install .``, except that it only installs your package dependencies,
metadata and wrappers for :ref:`console and GUI scripts <console-scripts>`.
Under the hood, setuptools will try to create a special :mod:`.pth file <site>`
in the target directory (usually ``site-packages``) that extends the
``PYTHONPATH`` or install a custom :doc:`import hook <python:reference/import>`.

When you're done with a given development task, you can simply uninstall your
package (as you would normally do with ``pip uninstall <package name>``).

Please note that, by default an editable install will expose at least all the
files that would be available in a regular installation. However, depending on
the file and directory organization in your project, it might also expose
as a side effect files that would not be normally available.
This is allowed so you can iteratively create new Python modules.
Please have a look on the following section if you are looking for a different behaviour.

.. admonition:: Virtual Environments

   You can think virtual environments as "isolated Python runtime deployments"
   that allow users to install different sets of libraries and tools without
   messing with the global behaviour of the system.

   They are the safest way of testing new projects and can be created easily
   with the :mod:`venv` module from the standard library.

   Please note however that depending on your operating system or distribution,
   ``venv`` might not come installed by default with Python. For those cases,
   you might need to use the OS package manager to install it.
   For example, in Debian/Ubuntu-based systems you can obtain it via:

   .. code-block:: bash

       sudo apt install python3-venv

   Alternatively, you can also try installing :pypi:`virtualenᴠ`.
   More information is available on the Python Packaging User Guide on
   :doc:`PyPUG:guides/installing-using-pip-and-virtual-environments`.

.. note::
    .. versionchanged:: v63.0.0
       Editable installation hooks implemented according to :pep:`660`.
       Support for :pep:`namespace packages <420>` is still **EXPERIMENTAL**.


"Strict" editable installs
--------------------------

When thinking about editable installations, users might have the following
expectations:

1. It should allow developers to add new files (or split/rename existing ones)
   and have them automatically exposed.
2. It should behave as close as possible to a regular installation and help
   users to detect problems (e.g. new files not being included in the distribution).

Unfortunately these expectations are in conflict with each other.
To solve this problem ``setuptools`` allows developers to choose a more
*"strict"* mode for the editable installation. This can be done by passing
a special *configuration setting* via :pypi:`pip`, as indicated bellow:

.. code-block:: bash

    pip install -e . --config-settings editable_mode=strict

In this mode, new files **won't** be exposed and the editable installs will
try to mimic as much as possible the behavior of a regular install.
Under the hood, ``setuptools`` will create a tree of file links in an auxiliary
directory (``$your_project_dir/build``) and add it to ``PYTHONPATH`` via a
:mod:`.pth file <site>`. (Please be careful to not delete this repository
by mistake otherwise your files may stop being accessible).


.. note::
    .. versionadded:: v63.0.0
       *Strict* mode implemented as **EXPERIMENTAL**.


Limitations
-----------

- The *editable* term is used to refer only to Python modules
  inside the package directories. Non-Python files, external (data) files,
  executable script files, binary extensions, headers and metadata may be
  exposed as a *snapshot* of the version they were at the moment of the
  installation.
- Adding new dependencies, entry-points or changing your project's metadata
  require a fresh "editable" re-installation.
- Console scripts and GUI scripts **MUST** be specified via :doc:`entry-points
  </userguide/entry_point>` to work properly.
- *Strict* editable installs require the file system to support
  either :wiki:`symbolic <symbolic link>` or :wiki:`hard links <hard link>`.
- Editable installations may not work with
  :doc:`namespaces created with pkgutil or pkg_resouces
  <PyPUG:guides/packaging-namespace-packages>`.
  Please use :pep:`420`-style implicit namespaces.
- Support for :pep:`420`-style implicit namespace packages for
  projects structured using :ref:`flat-layout` is still **experimental**.
  If you experience problems, you can try converting your package structure
  to the :ref:`src-layout`.

.. attention::
   Editable installs are **not a perfect replacement for regular installs**
   in a test environment. When in doubt, please test your projects as
   installed via a regular wheel. There are tools in the Python ecosystem,
   like :pypi:`tox` or :pypi:`nox`, that can help you with that
   (when used with appropriate configuration).


Legacy Behavior
---------------

If your project is not compatible with the new "editable installs" or you wish
to use the legacy behavior (that mimics the old and deprecated
``python setup.py develop`` command), you can set an environment variable:

.. code-block::

   SETUPTOOLS_USE_FEATURE="legacy-editable"
