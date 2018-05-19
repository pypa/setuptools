===============
Release Process
===============

In order to allow for rapid, predictable releases, Setuptools uses a
mechanical technique for releases, enacted by Travis following a
successful build of a tagged release per
`PyPI deployment <https://docs.travis-ci.com/user/deployment/pypi>`_.

Prior to cutting a release, please use `towncrier`_ to update
``CHANGES.rst`` to summarize the changes since the last release.
To update the changelog:

1. Install towncrier via ``pip install towncrier`` if not already installed.
2. Preview the new ``CHANGES.rst`` entry by running
   ``towncrier --draft --version {new.version.number}`` (enter the desired
   version number for the next release).  If any changes are needed, make
   them and generate a new preview until the output is acceptable.  Run
   ``git add`` for any modified files.
3. Run ``towncrier --version {new.version.number}`` to stage the changelog
   updates in git.
4. Verify that there are no remaining ``changelog.d/*.rst`` files.  If a
   file was named incorrectly, it may be ignored by towncrier.
5. Review the updated ``CHANGES.rst`` file.  If any changes are needed,
   make the edits and stage them via ``git add CHANGES.rst``.

Once the changelog edits are staged and ready to commit, cut a release by
installing and running ``bump2version --allow-dirty {part}`` where ``part``
is major, minor, or patch based on the scope of the changes in the
release. Then, push the commits to the master branch::

    $ git push origin master
    $ git push --tags

If tests pass, the release will be uploaded to PyPI (from the Python 3.6
tests).

.. _towncrier: https://pypi.org/project/towncrier/

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
