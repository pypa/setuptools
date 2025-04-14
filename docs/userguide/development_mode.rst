Development Mode (a.k.a. "Editable Installs")
=============================================

When creating a Python project, developers usually want to implement and test
changes iteratively, before cutting a release and preparing a distribution archive.

In normal circumstances this can be quite cumbersome and require the developers
to manipulate the ``PYTHONPATH`` environment variable or to continuously re-build
and re-install the project.

To facilitate iterative exploration and experimentation, setuptools allows
users to instruct the Python interpreter and its import machinery to load the
code under development directly from the project folder without having to
copy the files to a different location in the disk.
This means that changes in the Python source code can immediately take place
without requiring a new installation.

You can enter this "development mode" by performing an :doc:`editable installation
<pip:topics/local-project-installs>` inside of a :term:`virtual environment`,
using :doc:`pip's <pip:cli/pip_install>` ``-e/--editable`` flag, as shown below:

.. code-block:: bash

   $ cd your-python-project
   $ python -m venv .venv
   # Activate your environment with:
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

   You can think about virtual environments as "isolated Python runtime deployments"
   that allow users to install different sets of libraries and tools without
   messing with the global behaviour of the system.

   They are a safe way of testing new projects and can be created easily
   with the :mod:`venv` module from the standard library.

   Please note however that depending on your operating system or distribution,
   ``venv`` might not come installed by default with Python. For those cases,
   you might need to use the OS package manager to install it.
   For example, in Debian/Ubuntu-based systems you can obtain it via:

   .. code-block:: bash

       sudo apt install python3-venv

   Alternatively, you can also try installing :pypi:`virtualenv`.
   More information is available on the Python Packaging User Guide on
   :doc:`PyPUG:guides/installing-using-pip-and-virtual-environments`.

.. note::
    .. versionchanged:: v64.0.0
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
a special *configuration setting* via :pypi:`pip`, as indicated below:

.. code-block:: bash

    pip install -e . --config-settings editable_mode=strict

In this mode, new files **won't** be exposed and the editable installs will
try to mimic as much as possible the behavior of a regular install.
Under the hood, ``setuptools`` will create a tree of file links in an auxiliary
directory (``$your_project_dir/build``) and add it to ``PYTHONPATH`` via a
:mod:`.pth file <site>`. (Please be careful to not delete this repository
by mistake otherwise your files may stop being accessible).

.. warning::
   Strict editable installs require auxiliary files to be placed in a
   ``build/__editable__.*`` directory (relative to your project root).

   Please be careful to not remove this directory while testing your project,
   otherwise your editable installation may be compromised.

   You can remove the ``build/__editable__.*`` directory after uninstalling.


.. note::
    .. versionadded:: v64.0.0
       Added new *strict* mode for editable installations.
       The exact details of how this mode is implemented may vary.


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
  This installation mode might also generate auxiliary files under the project directory.
- There is *no guarantee* that the editable installation will be performed
  using a specific technique. Depending on each project, ``setuptools`` may
  select a different approach to ensure the package is importable at runtime.
- There is *no guarantee* that files outside the top-level package directory
  will be accessible after an editable install.
- There is *no guarantee* that attributes like ``__path__`` or ``__file__``
  will correspond to the exact location of the original files (e.g.,
  ``setuptools`` might employ file links to perform the editable installation).
  Users are encouraged to use tools like :mod:`importlib.resources` or
  :mod:`importlib.metadata` when trying to access package files directly.
- Editable installations may not work with
  :doc:`namespaces created with pkgutil or pkg_resources
  <PyPUG:guides/packaging-namespace-packages>`.
  Please use :pep:`420`-style implicit namespaces [#namespaces]_.
- Support for :pep:`420`-style implicit namespace packages for
  projects structured using :ref:`flat-layout` is still **experimental**.
  If you experience problems, you can try converting your package structure
  to the :ref:`src-layout`.
- File system entries in the current working directory
  whose names coincidentally match installed packages
  may take precedence in :doc:`Python's import system <python:reference/import>`.
  Users are encouraged to avoid such scenarios [#cwd]_.
- Setuptools will try to give the right precedence to modules in an editable install.
  However this is not always an easy task. If you have a particular order in
  ``sys.path`` or some specific import precedence that needs to be respected,
  the editable installation as supported by Setuptools might not be able to
  fulfil this requirement, and therefore it might not be the right tool for your use case.

.. attention::
   Editable installs are **not a perfect replacement for regular installs**
   in a test environment. When in doubt, please test your projects as
   installed via a regular wheel. There are tools in the Python ecosystem,
   like :pypi:`tox` or :pypi:`nox`, that can help you with that
   (when used with appropriate configuration).


Legacy Behavior
---------------

If your project is not compatible with the new "editable installs" or you wish
to replicate the legacy behavior, for the time being you can also perform the
installation in the ``compat`` mode:

.. code-block:: bash

    pip install -e . --config-settings editable_mode=compat

This installation mode will try to emulate how ``python setup.py develop``
works (still within the context of :pep:`660`).

.. warning::
   The ``compat`` mode is *transitional* and will be removed in
   future versions of ``setuptools``, it exists only to help during the
   migration period.
   Also note that support for this mode is limited:
   it is safe to assume that the ``compat`` mode is offered "as is", and
   improvements are unlikely to be implemented.
   Users are encouraged to try out the new editable installation techniques
   and make the necessary adaptations.

.. note::
   Newer versions of ``pip`` no longer run the fallback command
   ``python setup.py develop`` when the ``pyproject.toml`` file is present.
   This means that setting the environment variable
   ``SETUPTOOLS_ENABLE_FEATURES="legacy-editable"``
   will have no effect when installing a package with ``pip``.


How editable installations work
-------------------------------

*Advanced topic*

There are many techniques that can be used to expose packages under development
in such a way that they are available as if they were installed.
Depending on the project file structure and the selected mode, ``setuptools``
will choose one of these approaches for the editable installation [#criteria]_.

A non-exhaustive list of implementation mechanisms is presented below.
More information is available on the text of :pep:`PEP 660 <660#what-to-put-in-the-wheel>`.

- A static ``.pth`` file [#static_pth]_ can be added to one of the directories
  listed in :func:`site.getsitepackages` or :func:`site.getusersitepackages` to
  extend :obj:`sys.path`.
- A directory containing a *farm of file links* that mimic the
  project structure and point to the original files can be employed.
  This directory can then be added to :obj:`sys.path` using a static ``.pth`` file.
- A dynamic ``.pth`` file [#dynamic_pth]_ can also be used to install an
  "import :term:`finder`" (:obj:`~importlib.abc.MetaPathFinder` or
  :obj:`~importlib.abc.PathEntryFinder`) that will hook into Python's
  :doc:`import system <python:reference/import>` machinery.

.. attention::
   ``Setuptools`` offers **no guarantee** of which technique will be used to
   perform an editable installation. This will vary from project to project
   and may change depending on the specific version of ``setuptools`` being
   used.


----

.. rubric:: Notes

.. [#namespaces]
   You *may* be able to use *strict* editable installations with namespace
   packages created with ``pkgutil`` or ``pkg_namespaces``, however this is not
   officially supported.

.. [#cwd]
   Techniques like the :ref:`src-layout` or tooling-specific options like
   `tox's changedir <https://tox.wiki/en/stable/config.html#conf-changedir>`_
   can be used to prevent such kinds of situations (checkout `this blog post
   <https://blog.ganssle.io/articles/2019/08/test-as-installed.html>`_ for more
   insights).

.. [#criteria]
   ``setuptools`` strives to find a balance between allowing the user to see
   the effects of project files being edited while still trying to keep the
   editable installation as similar as possible to a regular installation.

.. [#static_pth]
   i.e., a ``.pth`` file where each line correspond to a path that should be
   added to :obj:`sys.path`. See :mod:`Site-specific configuration hook <site>`.

.. [#dynamic_pth]
   i.e., a ``.pth`` file that starts where each line starts with an ``import``
   statement and executes arbitrary Python code. See :mod:`Site-specific
   configuration hook <site>`.
