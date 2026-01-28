==========================================================================================
Drawbacks of installing source distributions (``sdist``) and how to improve predictability
==========================================================================================


.. admonition:: Scope and audience

   This page contains relevant information for **package consumers** (people
   installing third-party projects that may have been built with Setuptools).
   It explains why installing from :external+PyPUG:term:`Source Distributions
   <Source Distribution (or "sdist")>` can be less predictable than installing
   from :external+PyPUG:term:`wheels <Wheel>`, and contains tips on how to improve
   **installation-time** reproducibility. It does **not** describe how to build
   packages with Setuptools, nor is it a statement of policy about what
   publishers must do [#publishing]_.


The ``sdist`` format was one of the first packaging formats to be created by the
Python community (predating the advent of ``wheel``). Although very
useful today to distribute and share Python libraries and applications,
``sdist``\s are notoriously difficult to work with in circumstances that
require high build reproducibility and tolerance to disruptions.

This guide reviews the concept of ``sdist``, highlights its potential uses
and drawbacks and explores potential practices to improve build reproducibility
when relying on ``sdist``\s.


What is an ``sdist``?
=====================

You can read more about the ``sdist`` format and its ``wheel`` counterpart in
:external+PyPUG:doc:`/discussions/package-formats`, but for the sake of this
document an ``sdist`` can be considered a simple ``.tar.gz`` archive that
contains all the files necessary to build a Python project that later will be
installed in the end-user's environment.

The most defining characteristic of the ``sdist`` format is its
platform-independence, as the distributions do not include binary executable files.
This format is very flexible and, although usually composed by a simple copy
of the source code files with some extra metadata files added, it can also include
platform-independent code automatically generated during the build
phase [#examples]_.


When is an ``sdist`` useful?
============================

Sometimes it can be tricky to distribute Python packages that contain binary
extensions, especially when they are built for platforms that do not define a
cross-version stable ABI_.
Moreover package indexes like PyPI_ may restrict their offer to a handful of
well-known platforms.
Finally, for certain edge cases, the build process may require machine specific
parameters.

In this context, distributing code via ``sdist``\s becomes a valuable fallback.
It allows users in other platforms to access the source code
and attempt to recompile the extensions locally.


What are the drawbacks of an ``sdist``?
=======================================

Despite their usefulness, working with ``sdist``\s can be challenging. One
major difficulty is reconstructing a compatible build environment in which the
``sdist`` can be processed into a ``wheel``, especially when it comes to build
dependencies.

While :pep:`518` introduced a standard for declaring build dependencies
distributed as Python packages (e.g. via PyPI), many projects also rely on
non-Python dependencies, such as compilers and binary system-level libraries,
that are not declared as a standard metadata. These dependencies can vary
significantly across systems and its installation is often not automated and
undocumented, i.e., simply assumed to be present.

Another issue is *tooling drift*: even if a project was originally buildable
from its ``sdist``, changes in the build dependencies (e.g., updates,
deprecations and security fixes) can break compatibility over time [#pinning]_.
This is a natural tendency of software systems and especially true for older
projects.

Therefore, mission-critical systems and environments that cannot afford
unforeseen/unintended interruptions should not rely on ``sdist``\s.
If your project or product requires high reliability and minimal disruption,
you should adapt your workflow to increase resiliency and reproducibility or
disallow ``sdist``\s all together.


How to improve reproducibility in your workflow and avoid ``sdist`` drawbacks?
==============================================================================

The first step to improve your workflow is to determine whether your workflow
is directly or indirectly relying on ``sdist``\s — and to prevent them from being
compiled on demand.

Installers like ``pip`` or ``uv`` have options that help with this.
For example, you can set the environment variable |PIP_ONLY_BINARY|_ with
the value ``:all:``, to prevent ``sdist``\s from being installed
(see the corresponding `uv alternative`_).
When this setting is enabled, any installation that fails will indicate which
packages are not available as ``wheel``\s, helping you pinpoint installations
relying on ``sdist``\s.

Once these packages are identified, the next step is to build them in
a controlled environment.
You can use ``pip``\'s |PIP_CONSTRAINT|_ environment variable or the
|build-constraint|_ ``uv``\'s CLI option to enforce specific versions of
Python packages [#build-isolation]_.

To further improve the consistency of OS-level tools and libraries,
you can leverage your CI/CD provider's configuration method, for example
`GitHub Workflows`_, `Bitbucket Pipelines`_, `GitLab CI/CD`_, Jenkins_,
CircleCI_ or Semaphore_.

Alternatively, you can use containers (e.g. docker_, nerdctl_ or podman_),
immutable operating system distributions or package managers (e.g. `NixOS/Nix`_)
or configuration management tools (e.g. Ansible_, chef_ or puppet_)
to implement `Infrastructure as Code`_ (IaC) and ensure build environments
are reproducible and version-controlled.

Consider caching the resulting ``wheel``\s
locally via |wheelhouse directories|_ or hosting them in
*private package indexes* (such as devpi_).
This allows you to serve pre-built distributions internally,
which reduces reliance on external sources, improves build stability,
and often results in faster workflows as a welcome side effect.

Finally, it's important to regularly audit your pinned or cached (build)
dependencies for known security vulnerabilities and critical bug fixes and/or
update them accordingly.
This can be done through an *out-of-band* workflow — such as a scheduled job
or a monthly CI/CD pipeline — that does not interfere with your
mission-critical or low-tolerance environments. This approach ensures that your
systems remain secure and up to date without compromising the stability of your
primary workflows.


.. rubric:: Footnotes

.. [#publishing]
   The PyPA recommendation, documented in the `packaging tutorial`_, is to
   publish both ``sdists`` and ``wheels``.

.. [#examples]
   Examples of platform-independent generated code in ``sdist``\s include
   ``.pyx`` files transpiled into ``.c`` and Python code created from
   ``.proto``, JSON schema or grammar files, etc.

.. [#pinning]
   Although developers can try to minimize the impact of tooling drift by
   locking the version of build dependencies, this approach also has
   its own drawbacks. In fact, it is very common in the Python community to
   avoid specifying version caps. For a deeper discussion on this topic, see:
   https://iscinumpy.dev/post/bound-version-constraints/ and
   https://hynek.me/articles/semver-will-not-save-you/.

.. [#build-isolation]
   When a virtual environment with hand picked versions of build dependencies
   is crafted (either manually or via tools supporting one of the
   :external+PyPUG:doc:`/specifications/pylock-toml` or
   :external+pip:doc:`reference/requirements-file-format`), it is also possible
   to use features like |no-isolation|_, |no-build-isolation|_ or the
   `equivalent uv settings`_ to ensure packages are built against the currently
   active virtual environment.


.. _ABI: https://en.wikipedia.org/wiki/Application_binary_interface
.. _PyPI: https://pypi.org
.. |PIP_ONLY_BINARY| replace:: ``PIP_ONLY_BINARY``
.. _PIP_ONLY_BINARY: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-only-binary
.. _uv alternative: https://docs.astral.sh/uv/reference/settings/#pip_only-binary
.. |PIP_CONSTRAINT| replace:: ``PIP_CONSTRAINT``
.. _PIP_CONSTRAINT: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-c
.. |build-constraint| replace:: ``--build-constraint``
.. _build-constraint: https://docs.astral.sh/uv/concepts/projects/build/#build-constraints
.. _GitHub Workflows: https://docs.github.com/en/actions/writing-workflows
.. _Bitbucket Pipelines: https://www.atlassian.com/software/bitbucket/features/pipelines
.. _GitLab CI/CD: https://docs.gitlab.com/ci/
.. _Jenkins: https://www.jenkins.io/doc/
.. _CircleCI: https://circleci.com
.. _Semaphore: https://semaphore.io
.. _docker: https://www.docker.com
.. _nerdctl: https://github.com/containerd/nerdctl
.. _podman: https://podman.io
.. _NixOS/Nix: https://nixos.org
.. _Ansible: https://docs.ansible.com
.. _chef: https://docs.chef.io
.. _puppet: https://www.puppet.com/docs/index.html
.. _Infrastructure as Code: https://en.wikipedia.org/wiki/Infrastructure_as_code
.. |wheelhouse directories| replace:: *"wheelhouse" directories*
.. _wheelhouse directories: https://pip.pypa.io/en/stable/cli/pip_wheel/#examples
.. _devpi: https://doc.devpi.net/
.. |no-isolation| replace:: ``--no-isolation``
.. _no-isolation: https://build.pypa.io/en/stable/#python--m-build---no-isolation
.. |no-build-isolation| replace:: ``--no-build-isolation``
.. _no-build-isolation: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-build-isolation
.. _equivalent uv settings: https://docs.astral.sh/uv/concepts/projects/config/#build-isolation
.. _packaging tutorial: https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives
