Development Mode
================

Under normal circumstances, the ``setuptools`` assume that you are going to
build a distribution of your project, not use it in its "raw" or "unbuilt"
form.  However, if you were to use the ``setuptools`` to build a distribution,
you would have to rebuild and reinstall your project every time you made a
change to it during development.

Another problem that sometimes comes is that you may
need to do development on two related projects at the same time.  You may need
to put both projects' packages in the same directory to run them, but need to
keep them separate for revision control purposes.  How can you do this?

Setuptools allows you to deploy your projects for use in a common directory or
staging area, but without copying any files.  Thus, you can edit each project's
code in its checkout directory, and only need to run build commands when you
change files that need to be compiled or the provided metadata and setuptools configuration.

You can perform a ``pip`` installation passing the ``-e/--editable``
flag (e.g., ``pip install -e .``). It works very similarly to
``pip install .``, except that it doesn't actually install anything.
Instead, it creates a special ``.egg-link`` file in the target directory
(usually ``site-packages``) that links to your project's source code.
It may also update an existing ``easy-install.pth`` file
to include your project's source code, thereby making
it available on ``sys.path`` for all programs using that Python installation.

You can deploy the same project to multiple staging areas, e.g., if you have
multiple projects on the same machine that are sharing the same project you're
doing development work.

When you're done with a given development task, you can simply uninstall your
package (as you would normally do with ``pip uninstall <package name>``).
