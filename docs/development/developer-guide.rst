================================
Developer's Guide for Setuptools
================================

If you want to know more about contributing on Setuptools, this is the place.


-------------------
Recommended Reading
-------------------

Please read `How to write the perfect pull request
<https://blog.jaraco.com/how-to-write-perfect-pull-request/>`_ for some tips
on contributing to open source projects. Although the article is not
authoritative, it was authored by the maintainer of Setuptools, so reflects
his opinions and will improve the likelihood of acceptance and quality of
contribution.

------------------
Project Management
------------------

Setuptools is maintained primarily in GitHub at `this home
<https://github.com/pypa/setuptools>`_. Setuptools is maintained under the
Python Packaging Authority (PyPA) with several core contributors. All bugs
for Setuptools are filed and the canonical source is maintained in GitHub.

User support and discussions are done through
`GitHub Discussions <https://github.com/pypa/setuptools/discussions>`_,
or the issue tracker (for specific issues).

Discussions about development happen on GitHub Discussions or
the ``setuptools`` channel on `PyPA Discord <https://discord.com/invite/pypa>`_.

-----------------
Authoring Tickets
-----------------

Before authoring any source code, it's often prudent to file a ticket
describing the motivation behind making changes. First search to see if a
ticket already exists for your issue. If not, create one. Try to think from
the perspective of the reader. Explain what behavior you expected, what you
got instead, and what factors might have contributed to the unexpected
behavior. In GitHub, surround a block of code or traceback with the triple
backtick "\`\`\`" so that it is formatted nicely.

Filing a ticket provides a forum for justification, discussion, and
clarification. The ticket provides a record of the purpose for the change and
any hard decisions that were made. It provides a single place for others to
reference when trying to understand why the software operates the way it does
or why certain changes were made.

Setuptools makes extensive use of hyperlinks to tickets in the changelog so
that system integrators and other users can get a quick summary, but then
jump to the in-depth discussion about any subject referenced.

---------------------
Making a pull request
---------------------

When making a pull request, please
:ref:`include a short summary of the changes <Adding change notes
with your PRs>` and a reference to any issue tickets that the PR is
intended to solve.
All PRs with code changes should include tests. All changes should
include a changelog entry.

.. include:: ../../newsfragments/README.rst

-------------------
Auto-Merge Requests
-------------------

To support running all code through CI, even lightweight contributions,
the project employs Mergify to auto-merge pull requests tagged as
auto-merge.

Use ``hub pull-request -l auto-merge`` to create such a pull request
from the command line after pushing a new branch.

-------
Testing
-------

The primary tests are run using tox.  Make sure you have tox installed,
and invoke it::

    $ tox

Under continuous integration, additional tests may be run. See the
``.travis.yml`` file for full details on the tests run under Travis-CI.

-------------------
Semantic Versioning
-------------------

Setuptools follows ``semver``.

.. explain value of reflecting meaning in versions.

----------------------
Building Documentation
----------------------

Setuptools relies on the `Sphinx`_ system for building documentation.
The `published documentation`_ is hosted on Read the Docs.

To build the docs locally, use tox::

    $ tox -e docs

.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _published documentation: https://setuptools.pypa.io/en/latest/

---------------------
Vendored Dependencies
---------------------

Setuptools has some dependencies, but due to `bootstrapping issues
<https://github.com/pypa/setuptools/issues/980>`_, those dependencies
cannot be declared as they won't be resolved soon enough to build
setuptools from source. Eventually, this limitation may be lifted as
PEP 517/518 reach ubiquitous adoption, but for now, Setuptools
cannot declare dependencies other than through
``setuptools/_vendor/vendored.txt`` and
``pkg_resources/_vendor/vendored.txt``.

All the dependencies specified in these files are "vendorized" using a
simple Python script ``tools/vendor.py``.

To refresh the dependencies, run the following command::

    $ tox -e vendor
