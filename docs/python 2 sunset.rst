:orphan:

Python 2 Sunset
===============

Since January 2020 and the release of Setuptools 45, Python 2 is no longer
supported by the most current release (`discussion
<https://github.com/pypa/setuptools/issues/1458>`_). Setuptools as a project
continues to support Python 2 with bugfixes and important features on
Setuptools 44.x.

By design, most users will be unaffected by this change. That's because
Setuptools 45 declares its supported Python versions to exclude Python 2.7,
and installers such as pip 9 or later will honor this declaration and prevent
installation of Setuptools 45 or later in Python 2 environments.

Users that do import any portion of Setuptools 45 or later on Python 2 are
directed to this documentation to provide guidance on how to work around the
issues.

Workarounds
-----------

The best recommendation is to avoid Python 2 and move to Python 3 where
possible. This project acknowledges that not all environments can drop Python
2 support, so provides other options.

In less common scenarios, later versions of Setuptools can be installed on
unsupported Python versions. In these environments, the installer is advised
to first install ``setuptools<45`` to "pin Setuptools" to a compatible
version.

- When using older versions of pip (before 9.0), the ``Requires-Python``
  directive is not honored and invalid versions can be installed. Users are
  advised first to upgrade pip and retry or to pin Setuptools. Use ``pip
  --version`` to determine the version of pip.
- When using ``easy_install``, ``Requires-Python`` is not honored and later
  versions can be installed. In this case, users are advised to pin
  Setuptools. This applies to ``setup.py install`` invocations as well, as
  they use Setuptools under the hood.

It's still not working
----------------------

If after trying the above steps, the Python environment still has incompatible
versions of Setuptools installed, here are some things to try.

1. Uninstall and reinstall Setuptools. Run ``pip uninstall -y setuptools`` for
   the relevant environment. Repeat until there is no Setuptools installed.
   Then ``pip install setuptools``.
2. If possible, attempt to replicate the problem in a second environment
   (virtual machine, friend's computer, etc). If the issue is isolated to just
   one unique enviornment, first determine what is different about those
   environments (or reinstall/reset the failing one to defaults).
3. End users who are not themselves the maintainers for the package they are
   trying to install should contact the support channels for the relevant
   application. Please be considerate of those projects by searching for
   existing issues and following the latest guidance before reaching out for
   support. When filing an issue, be sure to give as much detail as possible
   to help the maintainers understand what factors led to the issue after
   following their recommended guidance.
4. Reach out to your local support groups. There's a good chance someone
   nearby has the expertise and willingness to help.
5. If all else fails, `file this template
   <https://github.com/pypa/setuptools/issues/new?assignees=&labels=Python+2&template=setuptools-warns-about-python-2-incompatibility.md&title=Incompatible+install+in+(summarize+your+environment)>`_
   with Setuptools. Please complete the whole template, providing as much
   detail about what factors led to the issue. Setuptools maintainers will
   summarily close tickets filed without any meaningful detail or engagement
   with the issue.
