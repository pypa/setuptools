.. _declarative config:

------------------------------------------------
Configuring setuptools using ``setup.cfg`` files
------------------------------------------------

.. note:: New in 30.3.0 (8 Dec 2016).

.. important::
    If compatibility with legacy builds (i.e. those not using the :pep:`517`
    build API) is desired, a ``setup.py`` file containing a ``setup()`` function
    call is still required even if your configuration resides in ``setup.cfg``.

``Setuptools`` allows using configuration files (usually :file:`setup.cfg`)
to define a package’s metadata and other options that are normally supplied
to the ``setup()`` function (declarative config).

This approach not only allows automation scenarios but also reduces
boilerplate code in some cases.

.. _example-setup-config:

.. code-block:: ini

    [metadata]
    name = my_package
    version = attr: my_package.VERSION
    author = Josiah Carberry
    author_email = josiah_carberry@brown.edu
    description = My package description
    long_description = file: README.rst, CHANGELOG.rst, LICENSE.rst
    keywords = one, two
    license = BSD-3-Clause
    classifiers =
        Framework :: Django
        Programming Language :: Python :: 3

    [options]
    zip_safe = False
    include_package_data = True
    packages = find:
    python_requires = >=3.7
    install_requires =
        requests
        importlib-metadata; python_version<"3.8"

    [options.package_data]
    * = *.txt, *.rst
    hello = *.msg

    [options.entry_points]
    console_scripts =
        executable-name = my_package.module:function

    [options.extras_require]
    pdf = ReportLab>=1.2; RXP
    rest = docutils>=0.3; pack ==1.1, ==1.3

    [options.packages.find]
    exclude =
        examples*
        tools*
        docs*
        my_package.tests*

Metadata and options are set in the config sections of the same name.

* Keys are the same as the :doc:`keyword arguments </references/keywords>` one
  provides to the ``setup()`` function.

* Complex values can be written comma-separated or placed one per line
  in *dangling* config values. The following are equivalent:

  .. code-block:: ini

      [metadata]
      keywords = one, two

      [metadata]
      keywords =
          one
          two

* In some cases, complex values can be provided in dedicated subsections for
  clarity.

* Some keys allow ``file:``, ``attr:``, ``find:``, and ``find_namespace:`` directives in
  order to cover common usecases.

* Unknown keys are ignored.


Using a ``src/`` layout
=======================

One commonly used configuration has all the Python source code in a
subdirectory (often called the ``src/`` layout), like this::

    ├── src
    │   └── mypackage
    │       ├── __init__.py
    │       └── mod1.py
    ├── setup.py
    └── setup.cfg

You can set up your ``setup.cfg`` to automatically find all your packages in
the subdirectory, using :ref:`package_dir <keyword/package_dir>`, like this:

.. code-block:: ini

    # This example contains just the necessary options for a src-layout, set up
    # the rest of the file as described above.

    [options]
    package_dir=
        =src
    packages=find:

    [options.packages.find]
    where=src

In this example, the value for the :ref:`package_dir <keyword/package_dir>`
configuration (i.e. ``=src``) is parsed as ``{"": "src"}``.
The ``""`` key has a special meaning in this context, and indicates that all the
packages are contained inside the given directory.
Also note that the value for ``[options.packages.find] where`` matches the
value associated with ``""`` in the ``package_dir`` dictionary.

..
   TODO: Add the following tip once the auto-discovery is no longer experimental:

   Starting in version 61, ``setuptools`` can automatically infer the
   configurations for both ``packages`` and ``package_dir`` for projects using
   a ``src/`` layout (as long as no value is specified for ``py_modules``).
   Please see :doc:`package discovery </userguide/package_discovery>` for more
   details.

Specifying values
=================

Some values are treated as simple strings, some allow more logic.

Type names used below:

* ``str`` - simple string
* ``list-comma`` - dangling list or string of comma-separated values
* ``list-semi`` - dangling list or string of semicolon-separated values
* ``bool`` - ``True`` is 1, yes, true
* ``dict`` - list-comma where each entry corresponds to a key/value pair,
  with keys separated from values by ``=``.
  If an entry starts with ``=``, the key is assumed to be an empty string
  (e.g. ``=src`` is parsed as ``{"": "src"}``).
* ``section`` - values are read from a dedicated (sub)section


Special directives:

* ``attr:`` - Value is read from a module attribute.  ``attr:`` supports
  callables and iterables; unsupported types are cast using ``str()``.

  In order to support the common case of a literal value assigned to a variable
  in a module containing (directly or indirectly) third-party imports,
  ``attr:`` first tries to read the value from the module by examining the
  module's AST.  If that fails, ``attr:`` falls back to importing the module.

* ``file:`` - Value is read from a list of files and then concatenated

  .. important::
      The ``file:`` directive is sandboxed and won't reach anything outside the
      project directory (i.e. the directory containing ``setup.cfg``/``pyproject.toml``).

  .. note::
      If you are using an old version of ``setuptools``, you might need to ensure
      that all files referenced by the ``file:`` directive are included in the ``sdist``
      (you can do that via ``MANIFEST.in`` or using plugins such as ``setuptools-scm``,
      please have a look on :doc:`/userguide/miscellaneous` for more information).

      .. versionchanged:: 66.1.0
         Newer versions of ``setuptools`` will automatically add these files to the ``sdist``.


Metadata
--------

.. attention::
    The aliases given below are supported for compatibility reasons,
    but their use is not advised.

==============================  =================  =================  =============== ==========
Key                             Aliases            Type               Minimum Version Notes
==============================  =================  =================  =============== ==========
name                                               str
version                                            attr:, file:, str  39.2.0          [#meta-1]_
url                             home-page          str
download_url                    download-url       str
project_urls                                       dict               38.3.0
author                                             str
author_email                    author-email       str
maintainer                                         str
maintainer_email                maintainer-email   str
classifiers                     classifier         file:, list-comma
license                                            str
license_files                   license_file       list-comma         42.0.0
description                     summary            file:, str
long_description                long-description   file:, str
long_description_content_type                      str                38.6.0
keywords                                           list-comma
platforms                       platform           list-comma
provides                                           list-comma
requires                                           list-comma
obsoletes                                          list-comma
==============================  =================  =================  =============== ==========

**Notes**:

.. [#meta-1] The ``version`` file attribute has only been supported since 39.2.0.

   A version loaded using the ``file:`` directive must comply with PEP 440.
   It is easy to accidentally put something other than a valid version
   string in such a file, so validation is stricter in this case.


Options
-------

=======================  ===================================  =============== ====================
Key                      Type                                 Minimum Version Notes
=======================  ===================================  =============== ====================
zip_safe                 bool
setup_requires           list-semi                            36.7.0
install_requires         file:, list-semi                                     **BETA** [#opt-6]_
extras_require           file:, section                                       **BETA** [#opt-2]_, [#opt-6]_
python_requires          str                                  34.4.0
entry_points             file:, section                       51.0.0
scripts                  list-comma
eager_resources          list-comma
dependency_links         list-comma
tests_require            list-semi
include_package_data     bool
packages                 find:, find_namespace:, list-comma                   [#opt-3]_
package_dir              dict
package_data             section                                              [#opt-1]_
exclude_package_data     section
namespace_packages       list-comma                                           [#opt-5]_
py_modules               list-comma                           34.4.0
data_files               section                              40.6.0          [#opt-4]_
=======================  ===================================  =============== ====================

**Notes**:

.. [#opt-1] In the ``package_data`` section, a key named with a single asterisk
   (``*``) refers to all packages, in lieu of the empty string used in ``setup.py``.

.. [#opt-2] In the ``extras_require`` section, values are parsed as ``list-semi``.
   This implies that in order to include markers, they **must** be *dangling*:

   .. code-block:: ini

      [options.extras_require]
      rest = docutils>=0.3; pack ==1.1, ==1.3
      pdf =
        ReportLab>=1.2
        RXP
        importlib-metadata; python_version < "3.8"

.. [#opt-3] The ``find:`` and ``find_namespace:`` directive can be further configured
   in a dedicated subsection ``options.packages.find``. This subsection accepts the
   same keys as the ``setuptools.find_packages`` and the
   ``setuptools.find_namespace_packages`` function:
   ``where``, ``include``, and ``exclude``.

   The ``find_namespace:`` directive is supported since Python >=3.3.

.. [#opt-4] ``data_files`` is deprecated and should be avoided.
   Please check :doc:`/userguide/datafiles` for more information.

.. [#opt-5] ``namespace_packages`` is deprecated in favour of native/implicit
   namespaces (:pep:`420`). Check :doc:`the Python Packaging User Guide
   <PyPUG:guides/packaging-namespace-packages>` for more information.

.. [#opt-6] ``file:`` directives for reading requirements are supported since version 62.6.
   The format for the file resembles a ``requirements.txt`` file,
   however please keep in mind that all non-comment lines must conform with :pep:`508`
   (``pip``-specify syntaxes, e.g. ``-c/-r/-e`` flags, are not supported).
   Library developers should avoid tightly pinning their dependencies to a specific
   version (e.g. via a "locked" requirements file).


Compatibility with other tools
==============================

Historically, several tools explored declarative package configuration
in parallel. And several of them chose to place the packaging
configuration within the project's :file:`setup.cfg` file.
One of the first was ``distutils2``, which development has stopped in
2013. Other include ``pbr`` which is still under active development or
``d2to1``, which was a plug-in that backports declarative configuration
to ``distutils``, but has had no release since Oct. 2015.
As a way to harmonize packaging tools, ``setuptools``, having held the
position of *de facto* standard, has gradually integrated those
features as part of its core features.

Still this has lead to some confusion and feature incompatibilities:

- some tools support features others don't;
- some have similar features but the declarative syntax differs;

The table below tries to summarize the differences. But, please, refer
to each tool documentation for up-to-date information.

=========================== ========== ========== ===== ===
feature                     setuptools distutils2 d2to1 pbr
=========================== ========== ========== ===== ===
[metadata] description-file S          Y          Y     Y
[files]                     S          Y          Y     Y
entry_points                Y          Y          Y     S
[backwards_compat]          N          Y          Y     Y
=========================== ========== ========== ===== ===

Y: supported, N: unsupported, S: syntax differs (see
:ref:`above example<example-setup-config>`).

Also note that some features were only recently added to ``setuptools``.
Please refer to the previous sections to find out when.
