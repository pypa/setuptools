Porting from Distutils
======================

Setuptools and the PyPA have a `stated goal <https://github.com/pypa/packaging-problems/issues/127>`_ to make Setuptools the reference API for distutils.

Since the 49.1.2 release, Setuptools includes a local, vendored copy of distutils (from late copies of CPython) that is disabled by default. To enable the use of this copy of distutils when invoking setuptools, set the enviroment variable:

	SETUPTOOLS_USE_DISTUTILS=local

This behavior is planned to become the default.

Prefer Setuptools
-----------------

As Distutils is deprecated, any usage of functions or objects from distutils is similarly discouraged, and Setuptools aims to replace or deprecate all such uses. This section describes the recommended replacements.

``distutils.core.setup`` → ``setuptools.setup``

``distutils.cmd.Command`` → ``setuptools.Command``

``distutils.log`` → (no replacement yet)

``distutils.version.*`` → ``packaging.version.*``

If a project relies on uses of ``distutils`` that do not have a suitable replacement above, please search the `Setuptools issue tracker <https://github.com/pypa/setuptools/issues/>`_ and file a request, describing the use-case so that Setuptools' maintainers can investigate. Please provide enough detail to help the maintainers understand how distutils is used, what value it provides, and why that behavior should be supported.
