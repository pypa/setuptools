===============
Release Process
===============

In order to allow for rapid, predictable releases, Setuptools uses a
mechanical technique for releases, enacted on tagged commits by
continuous integration.

To finalize a release, run ``tox -e finalize``, review, then push
the changes.

If tests pass, the release will be uploaded to PyPI.

Release Frequency
-----------------

Some have asked why Setuptools is released so frequently. Because Setuptools
uses a mechanical release process, it's very easy to make releases whenever the
code is stable (tests are passing). As a result, the philosophy is to release
early and often.

While some find the frequent releases somewhat surprising, they only empower
the user. Although releases are made frequently, users can choose the frequency
at which they use those releases. If instead Setuptools contributions were only
released in batches, the user would be constrained to only use Setuptools when
those official releases were made. With frequent releases, the user can govern
exactly how often he wishes to update.

Frequent releases also then obviate the need for dev or beta releases in most
cases. Because releases are made early and often, bugs are discovered and
corrected quickly, in many cases before other users have yet to encounter them.

Release Managers
----------------

Additionally, anyone with push access to the master branch has access to cut
releases.
