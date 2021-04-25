"Development Mode"
==================

Under normal circumstances, the ``distutils`` assume that you are going to
build a distribution of your project, not use it in its "raw" or "unbuilt"
form.  However, if you were to use the ``distutils`` to build a distribution,
you would have to rebuild and reinstall your project every time you made a
change to it during development.

Another problem that sometimes comes up with the ``distutils`` is that you may
need to do development on two related projects at the same time.  You may need
to put both projects' packages in the same directory to run them, but need to
keep them separate for revision control purposes.  How can you do this?

Setuptools allows you to deploy your projects for use in a common directory or
staging area, but without copying any files.  Thus, you can edit each project's
code in its checkout directory, and only need to run build commands when you
change a project's C extensions or similarly compiled files.  You can even
deploy a project into another project's checkout directory, if that's your
preferred way of working (as opposed to using a common independent staging area
or the site-packages directory).

To do this, use the ``setup.py develop`` command.  It works very similarly to
``setup.py install``, except that it doesn't actually install anything.
Instead, it creates a special ``.egg-link`` file in the deployment directory,
that links to your project's source code.  And, if your deployment directory is
Python's ``site-packages`` directory, it will also update the
``easy-install.pth`` file to include your project's source code, thereby making
it available on ``sys.path`` for all programs using that Python installation.

If you have enabled the ``use_2to3`` flag, then of course the ``.egg-link``
will not link directly to your source code when run under Python 3, since
that source code would be made for Python 2 and not work under Python 3.
Instead the ``setup.py develop`` will build Python 3 code under the ``build``
directory, and link there. This means that after doing code changes you will
have to run ``setup.py build`` before these changes are picked up by your
Python 3 installation.

In addition, the ``develop`` command creates wrapper scripts in the target
script directory that will run your in-development scripts after ensuring that
all your ``install_requires`` packages are available on ``sys.path``.

You can deploy the same project to multiple staging areas, e.g. if you have
multiple projects on the same machine that are sharing the same project you're
doing development work.

When you're done with a given development task, you can remove the project
source from a staging area using ``setup.py develop --uninstall``, specifying
the desired staging area if it's not the default.

There are several options to control the precise behavior of the ``develop``
command; see the section on the :ref:`develop <develop>` command below for more details.

Note that you can also apply setuptools commands to non-setuptools projects,
using commands like this::

   python -c "import setuptools; with open('setup.py') as f: exec(compile(f.read(), 'setup.py', 'exec'))" develop

That is, you can simply list the normal setup commands and options following
the quoted part.
