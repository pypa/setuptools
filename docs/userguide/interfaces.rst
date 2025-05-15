Supported Interfaces
====================

Setuptools is a complicated library with many interface surfaces and challenges. In addition to its primary purpose as a packaging build backend, Setuptools also has historically served as a standalone builder, installer, uploader, metadata provider, and more. Additionally, because it's implemented as a Python library, its entire functionality is incidentally exposed as a library.

In addition to operating as a library, because newer versions of Setuptools are often used to build older (sometimes decades-old) packages, it has a high burden of stability.

In order to have the ability to make sensible changes to the project, downstream developers and consumers should avoid depending on internal implementation details of the library and should rely only on the supported interfaces:

- *Tier 1*: APIs required by modern PyPA packaging standards (:pep:`517`, :pep:`660`) and Documented APIs for customising build behavior or creating plugins (:doc:`/userguide/extension`, :doc:`/references/keywords`):

   These APIs are expected to be extremely stable and have deprecation notices and periods prior to backward incompatible changes or removals.

   Please note that *functional and integration tests* capture specific behaviors and expectations about how the library and system is intended to work for outside users;
   and *code comments and docstrings* (including in tests) may provide specific protections to limit the changes to behaviors on which a downstream consumer can rely.

- *Tier 2*: Documented ``distutils`` APIs:

   ``setuptools`` strives to honor the interfaces provided by ``distutils`` and
   will coordinate with the ``pypa/distutils`` repository so that the
   appropriate deprecation notices are issued.

   In principle, these are documented in :doc:`/deprecated/distutils/apiref`.
   Please note however that when a suitable replacement is available or advised,
   the existing ``distutils`` API is considered deprecated and should not be used
   (see :pep:`632#migration-advice` and :doc:`/deprecated/distutils-legacy`).

Depending on other behaviors is risky and subject to future breakage. If a project wishes to consider using interfaces that aren't covered above, consider requesting those interfaces to be added prior to depending on them (perhaps through a pull request implementing the change and relevant regression tests).

Please check further information about deprecated and unsupported behaviors in :doc:`/deprecated/index`.


Support Policy Exceptions
-------------------------

Behaviors and interfaces explicitly documented/advertised as deprecated,
or that :obj:`issue deprecation warnings <warnings.warn>`
will be supported up to the end of the announced deprecation period.

However there are a few circumstances in which the Setuptools' maintainers
reserve the right of speeding up the deprecation cycle and shortening deprecation periods:

1. When security vulnerabilities are identified in specific code paths and the
   reworking existing APIs is not viable.
2. When standards in the Python packaging ecosystem externally drive non-backward
   compatible changes in the code base.
3. When changes in behavior are externally driven by 3rd-party dependencies
   and code maintained outside of the ``pypa/setuptools`` repository.

Note that these are exceptional circumstances and that the project will
carefully attempt to find alternatives before resorting to unscheduled removals.


What to do when deprecation periods are undefined?
--------------------------------------------------

In some cases it is difficult to define how long Setuptools will take
to remove certain features, behaviors or APIs.
For example, it may be complicated to assess how wide-spread the usage
of a certain feature is in the ecosystem.

Therefore, Setuptools may start to issue deprecation warnings without a clear due date.
This occurs because we want to notify consumers about upcoming breaking
changes as soon as possible so that they can start working in migration plans.

This does not mean that users should treat this deprecation as low priority or
interpret the lack of due date as a signal that a breaking change will never happen.

The advised course of action is for users to create a migration plan
as soon as they have identified to be subject to a Setuptools deprecation.

Setuptools may introduce relatively short deprecation periods (e.g. 6 months)
when a deprecation warning has already been issued for a long period without a
explicit due date.


How to stay on top of upcoming deprecations?
--------------------------------------------

It is a good idea to employ an automated test suite with relatively good
coverage in your project and keep an eye on the logs.
You can also automate this process by forwarding the standard output/error
streams to a log file and using heuristics to identify deprecations
(e.g. by searching for the word ``deprecation`` or ``deprecated``).
You may need to increase the level of verbosity of your output as
some tools may hide log messages by default (e.g. via ``pip -vv install ...``).

Additionally, if you are supporting a project that depends on Setuptools,
you can implement a CI workflow that leverages
:external+python:ref:`Python warning filters <warning-filter>`
to improve the visibility of warnings.

This workflow can be comprised, for example, of 3 iterative steps that require
developers to acknowledge the deprecation warnings:

1. Leverage Python Warning's Filter to transform warnings into exceptions during automated tests.
2. Devise a migration plan:

   - It is a good idea to track deprecations as if they were issues,
     and apply project management techniques to monitor the progress in handling them.
   - Determine which parts of your code are affected and understand
     the changes required to eliminate the warnings.

3. Modify the warning's filter you are using in the CI to not fail
   with the newly identified exceptions (e.g. by using the ``default`` action
   with a specific category or regular expression for the warning message).
   This can be done globally for the whole test suite or locally in a
   test-by-test basis.

Test tools like :pypi:`pytest` offer CLI and configuration options
to facilitate controlling the warning's filter (see :external+pytest:doc:`how-to/capture-warnings`).

Note that there are many ways to incorporate such workflow in your CI.
For example, if you have enough deployment resources and consider
deprecation warning management to be a day-to-day development test
you can set the warning's filter directly on your main CI loop.
On the other hand if you have critical timelines and cannot afford CI jobs
occasionally failing to flag maintenance, you can consider scheduling a
periodic CI run separated from your main/mission-critical workflow.


What does "support" mean?
-------------------------

Setuptools is a non-profit community-driven open source project and as such
the word "support" is used in a best-effort manner and with limited scope.
For example, it is not always possible to quickly provide fixes for bugs.

We appreciate the patience of the community and incentivise users
impacted by bugs to contribute to fixes in the form of
:doc:`PR submissions </development/developer-guide>`, to speed-up the process.

When we say "a certain feature is supported" we mean that we will do our best
to ensure this feature keeps working as documented.
Note however that, as in any system, unintended breakages may happen.
We appreciate the community understand and `considerate feedback`_.

.. _considerate feedback: https://opensource.how/etiquette/


What to do after the deprecation period ends?
---------------------------------------------

If you have limited development resources and is not able to
devise a migration plan before Setuptools removes a deprecated feature,
you can still resort to restricting the version of Setuptools to be installed.
This usually includes modifying ``[build-system] requires`` in ``pyproject.toml``
and/or specifying ``pip`` :external+pip:ref:`Constraints Files` via
the ``PIP_CONSTRAINT`` environment variable (or passing |build-constraint-uv|_).
Please avoid however to pre-emptively add version constraints if not necessary,
(you can read more about this in https://iscinumpy.dev/post/bound-version-constraints/).

.. |build-constraint-uv| replace:: ``--build-constraint`` to ``uv``
.. _build-constraint-uv: https://docs.astral.sh/uv/concepts/projects/build/#build-constraints


A note on "Public Names"
------------------------

Python devs may be used to the convention that private members are prefixed
with an ``_`` (underscore) character and that any member not marked by this
public. Due to the history and legacy of Setuptools this is not necessarily
the case [#private]_.

In this project, "public interfaces" are defined as interfaces explicitly
documented for 3rd party consumption.

When accessing a member in the ``setuptools`` package, please make sure it is
documented for external usage. Also note that names imported from different
modules/submodules are considered internal implementation details unless
explicitly listed in ``__all__``. The fact that they are accessible in the
namespace of the ``import``-er module is a mere side effect of the way Python works.

.. [#private]
   While names prefixed by ``_`` are always considered private,
   not necessary the absence of the prefix signals public members.
