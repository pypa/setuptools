===============
Release Process
===============

In order to allow for rapid, predictable releases, Setuptools uses a
mechanical technique for releases, enacted by Travis following a
successful build of a tagged release per
`PyPI deployment <https://docs.travis-ci.com/user/deployment/pypi>`_.

Prior to cutting a release, please check that the CHANGES.rst reflects
the summary of changes since the last release.
Ideally, these changelog entries would have been added
along with the changes, but it's always good to check.
Think about it from the
perspective of a user not involved with the development--what would
that person want to know about what has changed--or from the
perspective of your future self wanting to know when a particular
change landed.

To cut a release, install and run ``bump2version {part}`` where ``part``
is major, minor, or patch based on the scope of the changes in the
release. Then, push the commits to the master branch. If tests pass,
the release will be uploaded to PyPI (from the Python 3.6 tests).

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
