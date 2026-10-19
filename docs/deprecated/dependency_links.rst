Specifying dependencies that aren't in PyPI via ``dependency_links``
====================================================================

.. warning::
    Dependency links support has been dropped by pip starting with version
    19.0 (released 2019-01-22).

If your project depends on packages that don't exist on PyPI, you *may* still be
able to depend on them if they are available for download as:

- an egg, in the standard distutils ``sdist`` format,
- a single ``.py`` file, or
- a VCS repository (Subversion, Mercurial, or Git).

You need to add some URLs to the ``dependency_links`` argument to ``setup()``.

The URLs must be either:

1. direct download URLs,
2. the URLs of web pages that contain direct download links, or
3. the repository's URL

In general, it's better to link to web pages, because it is usually less
complex to update a web page than to release a new version of your project.
You can also use a SourceForge ``showfiles.php`` link in the case where a
package you depend on is distributed via SourceForge.

If you depend on a package that's distributed as a single ``.py`` file, you
must include an ``"#egg=project-version"`` suffix to the URL, to give a project
name and version number.  (Be sure to escape any dashes in the name or version
by replacing them with underscores.)  EasyInstall will recognize this suffix
and automatically create a trivial ``setup.py`` to wrap the single ``.py`` file
as an egg.

In the case of a VCS checkout, you should also append ``#egg=project-version``
in order to identify for what package that checkout should be used. You can
append ``@REV`` to the URL's path (before the fragment) to specify a revision.
Additionally, you can also force the VCS being used by prepending the URL with
a certain prefix. Currently available are:

-  ``svn+URL`` for Subversion,
-  ``git+URL`` for Git, and
-  ``hg+URL`` for Mercurial

A more complete example would be:

    ``vcs+proto://host/path@revision#egg=project-version``

Be careful with the version. It should match the one inside the project files.
If you want to disregard the version, you have to omit it both in the
``requires`` and in the URL's fragment.

This will do a checkout (or a clone, in Git and Mercurial parlance) to a
temporary folder and run ``setup.py bdist_egg``.

The ``dependency_links`` option takes the form of a list of URL strings.  For
example, this will cause a search of the specified page for eggs or source
distributions, if the package's dependencies aren't already installed:

.. tab:: setup.cfg

    .. code-block:: ini

        [options]
        #...
        dependency_links = http://peak.telecommunity.com/snapshots/

.. tab:: setup.py

    .. code-block:: python

        setup(
            ...,
            dependency_links=[
                "http://peak.telecommunity.com/snapshots/",
            ],
        )
