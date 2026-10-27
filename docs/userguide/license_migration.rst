.. _license-migration:

-------------------------------------------------------
Migrating to PEP 639 License Expressions
-------------------------------------------------------

Starting with setuptools v77.0.0, the ``project.license`` field accepts an
`SPDX license expression <https://spdx.org/licenses/>`_ as defined in
:pep:`639`. The previous TOML-table forms (``license = {text = "..."}`` and
``license = {file = "..."}``) are deprecated and will be removed in a future
version.

This guide helps you migrate your project's license configuration.

.. contents:: Table of Contents
   :local:
   :depth: 2

Background
----------

The ``project.license`` field in ``pyproject.toml`` historically accepted a
TOML table, either with a ``text`` key holding a license description or a
``file`` key pointing at a license file:

.. code-block:: toml

   # Old format (deprecated)
   license = {text = "Apache-2.0"}
   # or
   license = {file = "LICENSE"}

Starting with setuptools v77.0.0, ``project.license`` is instead a string
containing an SPDX license expression, and the files themselves are declared
separately via ``project.license-files``:

.. code-block:: toml

   # New format (PEP 639)
   license = "Apache-2.0"
   license-files = ["LICENSE"]

The SPDX expression format is standardized and supports composing licenses
(for example ``"Apache-2.0 OR MIT"`` or
``"GPL-3.0-only WITH Classpath-exception-2.0"``).

Migrating your configuration
----------------------------

Replace a ``{text = ...}`` license
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the ``text`` value was already a recognized license identifier, use it
directly as an SPDX expression:

.. code-block:: toml

   # Before
   license = {text = "MIT"}

   # After
   license = "MIT"

If the ``text`` was free-form prose rather than a license identifier, express
the license as an SPDX expression and ship the full text as a license file
(see below).

Replace a ``{file = ...}`` license
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Point ``license`` at the SPDX expression and list the file under
``license-files``:

.. code-block:: toml

   # Before
   license = {file = "LICENSE"}

   # After
   license = "Apache-2.0"
   license-files = ["LICENSE"]

``license-files`` accepts glob patterns, so multiple files (for example a
project license plus third-party notices) can be included:

.. code-block:: toml

   license-files = ["LICENSE*", "NOTICE"]

Replace license classifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``License :: ...`` trove classifiers are also deprecated in favor of SPDX
expressions. Drop them from ``classifiers`` and record the license in
``license`` instead:

.. code-block:: toml

   # Before
   classifiers = ["License :: OSI Approved :: MIT License"]

   # After
   license = "MIT"

Requiring a compatible setuptools
---------------------------------

SPDX expressions and the ``license-files`` field are understood by
**setuptools v77.0.0 and later**. This is a *build-time* requirement on
setuptools itself; it is independent of the Python versions your project
supports at runtime (``requires-python``).

Most build frontends (such as :pypi:`build` and :pypi:`pip`) build in an
isolated environment and install the latest setuptools by default, so simply
declaring the minimum in ``[build-system].requires`` is usually enough:

.. code-block:: toml

   [build-system]
   requires = ["setuptools>=77"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "my_package"
   license = "Apache-2.0"
   license-files = ["LICENSE"]

If you need to keep supporting builds with an older setuptools, retain the old
TOML-table form (it continues to work, with a deprecation warning) until you
can require setuptools v77+.

Common SPDX License Expressions
-------------------------------

Here are some common SPDX expressions:

- ``"MIT"`` -- MIT License
- ``"Apache-2.0"`` -- Apache License 2.0
- ``"BSD-3-Clause"`` -- BSD 3-Clause License
- ``"GPL-3.0-only"`` -- GNU General Public License v3.0 only
- ``"Apache-2.0 OR MIT"`` -- Dual licensed (either applies)
- ``"Apache-2.0 AND MIT"`` -- Both licenses apply

For the full list, see the `SPDX License List <https://spdx.org/licenses/>`_.

Troubleshooting
---------------

``SetuptoolsDeprecationWarning: `project.license` as a TOML table is deprecated``

This warning appears when using the old ``{text = ...}`` or ``{file = ...}``
form. Follow the migration steps above to move to an SPDX expression (and
``license-files`` where needed).

**Invalid SPDX expression**

Ensure your expression uses valid SPDX identifiers. Common mistakes:

- Using ``"GPL-3"`` instead of ``"GPL-3.0-only"`` (or ``"GPL-3.0-or-later"``)
- Using ``"BSD"`` instead of ``"BSD-3-Clause"``
- Forgetting the quotes around the expression

References
----------

- :pep:`639` -- Improving License Clarity with Better Package Metadata
- `SPDX License List <https://spdx.org/licenses/>`_
- `Writing your pyproject.toml <https://packaging.python.org/en/latest/guides/writing-pyproject-toml/>`_
