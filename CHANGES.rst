v60.0.2
-------


Misc
^^^^
* #2938: Select 'posix_user' for the scheme unless falling back to stdlib, then use 'unix_user'.


v60.0.1
-------


Misc
^^^^
* #2944: Add support for extended install schemes in easy_install.


v60.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2896: Setuptools once again makes its local copy of distutils the default. To override, set SETUPTOOLS_USE_DISTUTILS=stdlib.


v59.8.0
-------


Changes
^^^^^^^
* #2935: Merge pypa/distutils@460b59f0e68dba17e2465e8dd421bbc14b994d1f.


v59.7.0
-------


Changes
^^^^^^^
* #2930: Require Python 3.7


v59.6.0
-------


Changes
^^^^^^^
* #2925: Merge with pypa/distutils@92082ee42c including introduction of deprecation warning on Version classes.


v59.5.0
-------


Changes
^^^^^^^
* #2914: Merge with pypa/distutils@8f2df0bf6.


v59.4.0
-------


Changes
^^^^^^^
* #2893: Restore deprecated support for newlines in the Summary field.


v59.3.0
-------


Changes
^^^^^^^
* #2902: Merge with pypa/distutils@85db7a41242.

Misc
^^^^
* #2906: In ensure_local_distutils, re-use DistutilsMetaFinder to load the module. Avoids race conditions when _distutils_system_mod is employed.


v59.2.0
-------


Changes
^^^^^^^
* #2875: Introduce changes from pypa/distutils@514e9d0, including support for overrides from Debian and pkgsrc, unlocking the possibility of making SETUPTOOLS_USE_DISTUTILS=local the default again.


v59.1.1
-------


Misc
^^^^
* #2885: Fixed errors when encountering LegacyVersions.


v59.1.0
-------


Changes
^^^^^^^
* #2497: Update packaging to 21.2.
* #2877: Back out deprecation of setup_requires and replace instead by a deprecation of setuptools.installer and fetch_build_egg. Now setup_requires is still supported when installed as part of a PEP 517 build, but is deprecated when an unsatisfied requirement is encountered.
* #2879: Bump packaging to 21.2.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2867: PNG/ICO images replaced with SVG in the docs.
* #2867: Added support to SVG "favicons" via "in-tree" Sphinx extension.


v59.0.1
-------


Misc
^^^^
* #2880: Removed URL requirement for ``pytest-virtualenv`` in ``setup.cfg``.
  PyPI rejects packages with dependencies external to itself.
  Instead the test dependency was overwritten via ``tox.ini``


v59.0.0
-------


Deprecations
^^^^^^^^^^^^
* #2856: Support for custom commands that inherit directly from ``distutils`` is
  **deprecated**. Users should extend classes provided by setuptools instead.

Breaking Changes
^^^^^^^^^^^^^^^^
* #2870: Started failing on invalid inline description with line breaks :class:`ValueError` -- by :user:`webknjaz`

Changes
^^^^^^^
* #2698: Exposed exception classes from ``distutils.errors`` via ``setuptools.errors``.
* #2866: Incorporate changes from pypa/distutils@f1b0a2b.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2227: Added sphinx theme customisations to display the new logo in the sidebar and
  use its colours as "accent" in the documentation -- by :user:`abravalheri`
* #2227: Added new setuptools logo, including editable files and artwork documentation
  -- by :user:`abravalheri`
* #2698: Added mentions to ``setuptools.errors`` as a way of handling custom command
  errors.
* #2698: Added instructions to migrate from ``distutils.commands`` and
  ``distutils.errors`` in the porting guide.
* #2871: Added a note to the docs that it is possible to install
  ``setup.py``-less projects in editable mode with :doc:`pip v21.1+
  <pip:index>`, only having ``setup.cfg`` and ``pyproject.toml`` in
  project root -- by :user:`webknjaz`


v58.5.3
-------


Misc
^^^^
* #2849: Add fallback for custom ``build_py`` commands inheriting directly from
  :mod:`distutils`, while still handling ``include_package_data=True`` for
  ``sdist``.


v58.5.2
-------


Misc
^^^^
* #2847: Suppress 'setup.py install' warning under bdist_wheel.


v58.5.1
-------


Misc
^^^^
* #2846: Move PkgResourcesDeprecationWarning above implicitly-called function so that it's in the namespace when version warnings are generated in an environment that contains them.


v58.5.0
-------


Changes
^^^^^^^
* #1461: Fix inconsistency with ``include_package_data`` and ``packages_data`` in sdist
  by replacing the loop breaking mechanism between the ``sdist`` and
  ``egg_info`` commands -- by :user:`abravalheri`


v58.4.0
-------


Changes
^^^^^^^
* #2497: Officially deprecated PEP 440 non-compliant versions.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2832: Removed the deprecated ``data_files`` option from the example in the
  declarative configuration docs -- by :user:`abravalheri`
* #2832: Change type of ``data_files`` option from ``dict`` to ``section`` in
  declarative configuration docs (to match previous example) -- by
  :user:`abravalheri`


v58.3.0
-------


Changes
^^^^^^^
* #917: ``setup.py install`` and ``easy_install`` commands are now officially deprecated. Use other standards-based installers (like pip) and builders (like build). Workloads reliant on this behavior should pin to this major version of Setuptools. See `Why you shouldn't invoke setup.py directly <https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html>`_ for more background.
* #1988: Deprecated the ``bdist_rpm`` command. Binary packages should be built as wheels instead.
  -- by :user:`hugovk`
* #2785: Replace ``configparser``'s ``readfp`` with ``read_file``, deprecated since Python 3.2.
  -- by :user:`hugovk`
* #2823: Officially deprecated support for ``setup_requires``. Users are encouraged instead to migrate to PEP 518 ``build-system.requires`` in ``pyproject.toml``. Users reliant on ``setup_requires`` should consider pinning to this major version to avoid disruption.

Misc
^^^^
* #2762: Changed codecov.yml to configure the threshold to be lower
  -- by :user:`tanvimoharir`


v58.2.0
-------


Changes
^^^^^^^
* #2757: Add windows arm64 launchers for scripts generated by easy_install.
* #2800: Added ``--owner`` and ``--group`` options to the ``sdist`` command,
  for specifying file ownership within the produced tarball (similarly
  to the corresponding distutils ``sdist`` options).

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2792: Document how the legacy and non-legacy versions are compared, and reference to the `PEP 440 <https://www.python.org/dev/peps/pep-0440/>`_ scheme.


v58.1.0
-------


Changes
^^^^^^^
* #2796: Merge with pypa/distutils@02e9f65ab0


v58.0.4
-------


Misc
^^^^
* #2773: Retain case in setup.cfg during sdist.


v58.0.3
-------


Misc
^^^^
* #2777: Build does not fail fast when ``use_2to3`` is supplied but set to a false value.


v58.0.2
-------


Misc
^^^^
* #2769: Build now fails fast when ``use_2to3`` is supplied.


v58.0.1
-------


Misc
^^^^
* #2765: In Distribution.finalize_options, suppress known removed entry points to avoid issues with older Setuptools.


v58.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2086: Removed support for 2to3 during builds. Projects should port to a unified codebase or pin to an older version of Setuptools using PEP 518 build-requires.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2746: add python_requires example


v57.5.0
-------


Changes
^^^^^^^
* #2712: Added implicit globbing support for `[options.data_files]` values.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2737: fix various syntax and style errors in code snippets in docs


v57.4.0
-------


Changes
^^^^^^^
* #2722: Added support for ``SETUPTOOLS_EXT_SUFFIX`` environment variable to override the suffix normally detected from the ``sysconfig`` module.


v57.3.0
-------


Changes
^^^^^^^
* #2465: Documentation is now published using the Furo theme.


v57.2.0
-------


Changes
^^^^^^^
* #2724: Added detection of Windows ARM64 build environments using the ``VSCMD_ARG_TGT_ARCH`` environment variable.


v57.1.0
-------


Changes
^^^^^^^
* #2692: Globs are now sorted in 'license_files' restoring reproducibility by eliminating variance from disk order.
* #2714: Update to distutils at pypa/distutils@e2627b7.
* #2715: Removed reliance on deprecated ssl.match_hostname by removing the ssl support. Now any index operations rely on the native SSL implementation.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2604: Revamped the backward/cross tool compatibility section to remove
  some confusion.
  Add some examples and the version since when ``entry_points`` are
  supported in declarative configuration.
  Tried to make the reading flow a bit leaner, gather some information
  that were a bit dispersed.


v57.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2645: License files excluded via the ``MANIFEST.in`` but matched by either
  the ``license_file`` (deprecated) or ``license_files`` options,
  will be nevertheless included in the source distribution. - by :user:`cdce8p`

Changes
^^^^^^^
* #2628: Write long description in message payload of PKG-INFO file. - by :user:`cdce8p`
* #2645: Added ``License-File`` (multiple) to the output package metadata.
  The field will contain the path of a license file, matched by the
  ``license_file`` (deprecated) and ``license_files`` options,
  relative to ``.dist-info``. - by :user:`cdce8p`
* #2678: Moved Setuptools' own entry points into declarative config.
* #2680: Vendored `more_itertools <https://pypi.org/project/more-itertools>`_ for Setuptools.
* #2681: Setuptools own setup.py no longer declares setup_requires, but instead expects wheel to be installed as declared by pyproject.toml.

Misc
^^^^
* #2650: Updated the docs build tooling to support the latest version of
  Towncrier and show the previews of not-yet-released setuptools versions
  in the changelog -- :user:`webknjaz`


v56.2.0
-------


Changes
^^^^^^^
* #2640: Fixed handling of multiline license strings. - by :user:`cdce8p`
* #2641: Setuptools will now always try to use the latest supported
  metadata version for ``PKG-INFO``. - by :user:`cdce8p`


v56.1.0
-------


Changes
^^^^^^^
* #2653: Incorporated assorted changes from pypa/distutils.
* #2657: Adopted docs from distutils.
* #2663: Added Visual Studio Express 2017 support -- by :user:`dofuuz`

Misc
^^^^
* #2644: Fixed ``DeprecationWarning`` due to ``threading.Thread.setDaemon`` in tests -- by :user:`tirkarthi`
* #2654: Made the changelog generator compatible
  with Towncrier >= 19.9 -- :user:`webknjaz`
* #2664: Relax the deprecation message in the distutils hack.


v56.0.0
-------


Deprecations
^^^^^^^^^^^^
* #2620: The ``license_file`` option is now marked as deprecated.
  Use ``license_files`` instead. -- by :user:`cdce8p`

Breaking Changes
^^^^^^^^^^^^^^^^
* #2620: If neither ``license_file`` nor ``license_files`` is specified, the ``sdist``
  option will now auto-include files that match the following patterns:
  ``LICEN[CS]E*``, ``COPYING*``, ``NOTICE*``, ``AUTHORS*``.
  This matches the behavior of ``bdist_wheel``. -- by :user:`cdce8p`

Changes
^^^^^^^
* #2620: The ``license_file`` and ``license_files`` options now support glob patterns. -- by :user:`cdce8p`
* #2632: Implemented ``VendorImporter.find_spec()`` method to get rid
  of ``ImportWarning`` that Python 3.10 emits when only the old-style
  importer hooks are present -- by :user:`webknjaz`

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2620: Added documentation for the ``license_files`` option. -- by :user:`cdce8p`


v55.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2566: Remove the deprecated ``bdist_wininst`` command. Binary packages should be built as wheels instead. -- by :user:`hroncok`


v54.2.0
-------


Changes
^^^^^^^
* #2608: Added informative error message to PEP 517 build failures owing to
  an empty ``setup.py`` -- by :user:`layday`


v54.1.3
-------

No significant changes.


v54.1.2
-------


Misc
^^^^
* #2595: Reduced scope of dash deprecation warning to Setuptools/distutils only -- by :user:`melissa-kun-li`


v54.1.1
-------


Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2584: Added ``sphinx-inline-tabs`` extension to allow for comparison of ``setup.py`` and its equivalent ``setup.cfg`` -- by :user:`amy-lei`

Misc
^^^^
* #2592: Made option keys in the ``[metadata]`` section of ``setup.cfg`` case-sensitive. Users having
  uppercase option spellings will get a warning suggesting to make them to lowercase
  -- by :user:`melissa-kun-li`


v54.1.0
-------


Changes
^^^^^^^
* #1608: Removed the conversion of dashes to underscores in the :code:`extras_require` and :code:`data_files` of :code:`setup.cfg` to support the usage of dashes. Method will warn users when they use a dash-separated key which in the future will only allow an underscore. Note: the method performs the dash to underscore conversion to preserve compatibility, but future versions will no longer support it -- by :user:`melissa-kun-li`


v54.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2582: Simplified build-from-source story by providing bootstrapping metadata in a separate egg-info directory. Build requirements no longer include setuptools itself. Sdist once again includes the pyproject.toml. Project can no longer be installed from source on pip 19.x, but install from source is still supported on pip < 19 and pip >= 20 and install from wheel is still supported with pip >= 9.

Changes
^^^^^^^
* #1932: Handled :code:`AttributeError` by raising :code:`DistutilsSetupError` in :code:`dist.check_specifier()` when specifier is not a string -- by :user:`melissa-kun-li`
* #2570: Correctly parse cmdclass in setup.cfg.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2553: Added userguide example for markers in extras_require -- by :user:`pwoolvett`


v53.1.0
-------


Changes
^^^^^^^
* #1937: Preserved case-sensitivity of keys in setup.cfg so that entry point names are case-sensitive. Changed sensitivity of configparser. NOTE: Any projects relying on case-insensitivity will need to adapt to accept the original case as published. -- by :user:`melissa-kun-li`
* #2573: Fixed error in uploading a Sphinx doc with the :code:`upload_docs` command. An html builder will be used.
  Note: :code:`upload_docs` is deprecated for PyPi, but is supported for other sites -- by :user:`melissa-kun-li`


v53.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #1527: Removed bootstrap script. Now Setuptools requires pip or another pep517-compliant builder such as 'build' to build. Now Setuptools can be installed from Github main branch.


v52.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2537: Remove fallback support for fetch_build_eggs using easy_install. Now pip is required for setup_requires to succeed.
* #2544: Removed 'easy_install' top-level model (runpy entry point) and 'easy_install' console script.
* #2545: Removed support for eggsecutables.

Changes
^^^^^^^
* #2459: Tests now run in parallel via pytest-xdist, completing in about half the time. Special thanks to :user:`webknjaz` for hard work implementing test isolation. To run without parallelization, disable the plugin with ``tox -- -p no:xdist``.


v51.3.3
-------


Misc
^^^^
* #2539: Fix AttributeError in Description validation.


v51.3.2
-------


Misc
^^^^
* #1390: Validation of Description field now is more lenient, emitting a warning and mangling the value to be valid (replacing newlines with spaces).


v51.3.1
-------


Misc
^^^^
* #2536: Reverted tag deduplication handling.


v51.3.0
-------


Changes
^^^^^^^
* #1390: Newlines in metadata description/Summary now trigger a ValueError.
* #2481: Define ``create_module()`` and ``exec_module()`` methods in ``VendorImporter``
  to get rid of ``ImportWarning`` -- by :user:`hroncok`
* #2489: ``pkg_resources`` behavior for zipimport now matches the regular behavior, and finds
  ``.egg-info`` (previoulsy would only find ``.dist-info``) -- by :user:`thatch`
* #2529: Fixed an issue where version tags may be added multiple times


v51.2.0
-------


Changes
^^^^^^^
* #2493: Use importlib.import_module() rather than the deprecated loader.load_module()
  in pkg_resources namespace delaration -- by :user:`encukou`

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2525: Fix typo in the document page about entry point. -- by :user:`jtr109`

Misc
^^^^
* #2534: Avoid hitting network during test_easy_install.


v51.1.2
-------


Misc
^^^^
* #2505: Disable inclusion of package data as it causes 'tests' to be included as data.


v51.1.1
-------


Misc
^^^^
* #2534: Avoid hitting network during test_virtualenv.test_test_command.


v51.1.0
-------


Changes
^^^^^^^
* #2486: Project adopts jaraco/skeleton for shared package maintenance.

Misc
^^^^
* #2477: Restore inclusion of rst files in sdist.
* #2484: Setuptools has replaced the master branch with the main branch.
* #2485: Fixed failing test when pip 20.3+ is present.
  -- by :user:`yan12125`
* #2487: Fix tests with pytest 6.2
  -- by :user:`yan12125`


v51.0.0
-------


Breaking Changes
^^^^^^^^^^^^^^^^
* #2435: Require Python 3.6 or later.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2430: Fixed inconsistent RST title nesting levels caused by #2399
  -- by :user:`webknjaz`
* #2430: Fixed a typo in Sphinx docs that made docs dev section disappear
  as a result of PR #2426 -- by :user:`webknjaz`

Misc
^^^^
* #2471: Removed the tests that guarantee that the vendored dependencies can be built by distutils.


v50.3.2
-------



Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2394: Extended towncrier news template to include change note categories.
  This allows to see what types of changes a given version introduces
  -- by :user:`webknjaz`
* #2427: Started enforcing strict syntax and reference validation
  in the Sphinx docs -- by :user:`webknjaz`
* #2428: Removed redundant Sphinx ``Makefile`` support -- by :user:`webknjaz`

Misc
^^^^
* #2401: Enabled test results reporting in AppVeyor CI
  -- by :user:`webknjaz`
* #2420: Replace Python 3.9.0 beta with 3.9.0 final on GitHub Actions.
* #2421: Python 3.9 Trove classifier got added to the dist metadata
  -- by :user:`webknjaz`


v50.3.1
-------



Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2093: Finalized doc revamp.
* #2097: doc: simplify index and group deprecated files
* #2102: doc overhaul step 2: break main doc into multiple sections
* #2111: doc overhaul step 3: update userguide
* #2395: Added a ``:user:`` role to Sphinx config -- by :user:`webknjaz`
* #2395: Added an illustrative explanation about the change notes to fragments dir -- by :user:`webknjaz`

Misc
^^^^
* #2379: Travis CI test suite now tests against PPC64.
* #2413: Suppress EOF errors (and other exceptions) when importing lib2to3.


v50.3.0
-------



Changes
^^^^^^^
* #2368: In distutils, restore support for monkeypatched CCompiler.spawn per pypa/distutils#15.


v50.2.0
-------



Changes
^^^^^^^
* #2355: When pip is imported as part of a build, leave distutils patched.
* #2380: There are some setuptools specific changes in the
  ``setuptools.command.bdist_rpm`` module that are no longer needed, because
  they are part of the ``bdist_rpm`` module in distutils in Python
  3.5.0. Therefore, code was removed from ``setuptools.command.bdist_rpm``.


v50.1.0
-------



Changes
^^^^^^^
* #2350: Setuptools reverts using the included distutils by default. Platform maintainers and system integrators and others are *strongly* encouraged to set ``SETUPTOOLS_USE_DISTUTILS=local`` to help identify and work through the reported issues with distutils adoption, mainly to file issues and pull requests with pypa/distutils such that distutils performs as needed across every supported environment.


v50.0.3
-------



Misc
^^^^
* #2363: Restore link_libpython support on Python 3.7 and earlier (see pypa/distutils#9).


v50.0.2
-------



Misc
^^^^
* #2352: In distutils hack, use absolute import rather than relative to avoid bpo-30876.


v50.0.1
-------



Misc
^^^^
* #2357: Restored Python 3.5 support in distutils.util for missing ``subprocess._optim_args_from_interpreter_flags``.
* #2358: Restored AIX support on Python 3.8 and earlier.
* #2361: Add Python 3.10 support to _distutils_hack. Get the 'Loader' abstract class
  from importlib.abc rather than importlib.util.abc (alias removed in Python
  3.10).


v50.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #2232: Once again, Setuptools overrides the stdlib distutils on import. For environments or invocations where this behavior is undesirable, users are provided with a temporary escape hatch. If the environment variable ``SETUPTOOLS_USE_DISTUTILS`` is set to ``stdlib``, Setuptools will fall back to the legacy behavior. Use of this escape hatch is discouraged, but it is provided to ease the transition while proper fixes for edge cases can be addressed.

Changes
^^^^^^^
* #2334: In MSVC module, refine text in error message.


v49.6.0
-------



Changes
^^^^^^^
* #2129: In pkg_resources, no longer detect any pathname ending in .egg as a Python egg. Now the path must be an unpacked egg or a zip file.


v49.5.0
-------



Changes
^^^^^^^
* #2306: When running as a PEP 517 backend, setuptools does not try to install
  ``setup_requires`` itself. They are reported as build requirements for the
  frontend to install.


v49.4.0
-------



Changes
^^^^^^^
* #2310: Updated vendored packaging version to 20.4.


v49.3.2
-------



Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2300: Improve the ``safe_version`` function documentation

Misc
^^^^
* #2297: Once again, in stubs prefer exec_module to the deprecated load_module.


v49.3.1
-------



Changes
^^^^^^^
* #2316: Removed warning when ``distutils`` is imported before ``setuptools`` when ``distutils`` replacement is not enabled.


v49.3.0
-------



Changes
^^^^^^^
* #2259: Setuptools now provides a .pth file (except for editable installs of setuptools) to the target environment to ensure that when enabled, the setuptools-provided distutils is preferred before setuptools has been imported (and even if setuptools is never imported). Honors the SETUPTOOLS_USE_DISTUTILS environment variable.


v49.2.1
-------



Misc
^^^^
* #2257: Fixed two flaws in distutils._msvccompiler.MSVCCompiler.spawn.


v49.2.0
-------



Changes
^^^^^^^
* #2230: Now warn the user when setuptools is imported after distutils modules have been loaded (exempting PyPy for 3.6), directing the users of packages to import setuptools first.


v49.1.3
-------



Misc
^^^^
* #2212: (Distutils) Allow spawn to accept environment. Avoid monkey-patching global state.
* #2249: Fix extension loading technique in stubs.


v49.1.2
-------



Changes
^^^^^^^
* #2232: In preparation for re-enabling a local copy of distutils, Setuptools now honors an environment variable, SETUPTOOLS_USE_DISTUTILS. If set to 'stdlib' (current default), distutils will be used from the standard library. If set to 'local' (default in a imminent backward-incompatible release), the local copy of distutils will be used.


v49.1.1
-------



Misc
^^^^
* #2094: Removed pkg_resources.py2_warn module, which is no longer reachable.


v49.0.1
-------



Misc
^^^^
* #2228: Applied fix for pypa/distutils#3, restoring expectation that spawn will raise a DistutilsExecError when attempting to execute a missing file.


v49.1.0
-------



Changes
^^^^^^^
* #2228: Disabled distutils adoption for now while emergent issues are addressed.


v49.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #2165: Setuptools no longer installs a site.py file during easy_install or develop installs. As a result, .eggs on PYTHONPATH will no longer take precedence over other packages on sys.path. If this issue affects your production environment, please reach out to the maintainers at #2165.

Changes
^^^^^^^
* #2137: Removed (private) pkg_resources.RequirementParseError, now replaced by packaging.requirements.InvalidRequirement. Kept the name for compatibility, but users should catch InvalidRequirement instead.
* #2180: Update vendored packaging in pkg_resources to 19.2.

Misc
^^^^
* #2199: Fix exception causes all over the codebase by using ``raise new_exception from old_exception``


v48.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #2143: Setuptools adopts distutils from the Python 3.9 standard library and no longer depends on distutils in the standard library. When importing ``setuptools`` or ``setuptools.distutils_patch``, Setuptools will expose its bundled version as a top-level ``distutils`` package (and unload any previously-imported top-level distutils package), retaining the expectation that ``distutils``' objects are actually Setuptools objects.
  To avoid getting any legacy behavior from the standard library, projects are advised to always "import setuptools" prior to importing anything from distutils. This behavior happens by default when using ``pip install`` or ``pep517.build``. Workflows that rely on ``setup.py (anything)`` will need to first ensure setuptools is imported. One way to achieve this behavior without modifying code is to invoke Python thus: ``python -c "import setuptools; exec(open('setup.py').read())" (anything)``.


v47.3.2
-------



Misc
^^^^
* #2071: Replaced references to the deprecated imp package with references to importlib


v47.3.1
-------



Misc
^^^^
* #1973: Removed ``pkg_resources.py31compat.makedirs`` in favor of the stdlib. Use ``os.makedirs()`` instead.
* #2198: Restore ``__requires__`` directive in easy-install wrapper scripts.


v47.3.0
-------



Changes
^^^^^^^
* #2197: Console script wrapper for editable installs now has a unified template and honors importlib_metadata if present for faster script execution on older Pythons.

Misc
^^^^
* #2195: Fix broken entry points generated by easy-install (pip editable installs).


v47.2.0
-------



Changes
^^^^^^^
* #2194: Editable-installed entry points now load significantly faster on Python versions 3.8+.
* #1471: Incidentally fixed by #2194 on Python 3.8 or when importlib_metadata is present.


v47.1.1
-------



Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2156: Update mailing list pointer in developer docs

Incorporate changes from v44.1.1:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* #2158: Avoid loading working set during ``Distribution.finalize_options`` prior to invoking ``_install_setup_requires``, broken since v42.0.0.


v44.1.1
-------



Misc
^^^^
* #2158: Avoid loading working set during ``Distribution.finalize_options`` prior to invoking ``_install_setup_requires``, broken since v42.0.0.


v47.1.0
-------



Changes
^^^^^^^
* #2070: In wheel-to-egg conversion, use simple pkg_resources-style namespace declaration for packages that declare namespace_packages.


v47.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #2094: Setuptools now actively crashes under Python 2. Python 3.5 or later is required. Users of Python 2 should use ``setuptools<45``.

Changes
^^^^^^^
* #1700: Document all supported keywords by migrating the ones from distutils.


v46.4.0
-------



Changes
^^^^^^^
* #1753: ``attr:`` now extracts variables through rudimentary examination of the AST,
  thereby supporting modules with third-party imports. If examining the AST
  fails to find the variable, ``attr:`` falls back to the old behavior of
  importing the module. Works on Python 3 only.


v46.3.1
-------

No significant changes.


v46.3.0
-------



Changes
^^^^^^^
* #2089: Package index functionality no longer attempts to remove an md5 fragment from the index URL. This functionality, added for distribute #163 is no longer relevant.

Misc
^^^^
* #2041: Preserve file modes during pkg files copying, but clear read only flag for target afterwards.
* #2105: Filter ``2to3`` deprecation warnings from ``TestDevelop.test_2to3_user_mode``.


v46.2.0
-------



Changes
^^^^^^^
* #2040: Deprecated the ``bdist_wininst`` command. Binary packages should be built as wheels instead.
* #2062: Change 'Mac OS X' to 'macOS' in code.
* #2075: Stop recognizing files ending with ``.dist-info`` as distribution metadata.
* #2086: Deprecate 'use_2to3' functionality. Packagers are encouraged to use single-source solutions or build tool chains to manage conversions outside of setuptools.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1698: Added documentation for ``build_meta`` (a bare minimum, not completed).

Misc
^^^^
* #2082: Filter ``lib2to3`` ``PendingDeprecationWarning`` and ``DeprecationWarning`` in tests,
  because ``lib2to3`` is `deprecated in Python 3.9 <https://bugs.python.org/issue40360>`_.


v46.1.3
-------

No significant changes.


v46.1.2
-------



Misc
^^^^
* #1458: Added template for reporting Python 2 incompatibilities.


v46.1.1
-------

No significant changes.


v46.1.0
-------



Changes
^^^^^^^
* #308: Allow version number normalization to be bypassed by wrapping in a 'setuptools.sic()' call.
* #1424: Prevent keeping files mode for package_data build. It may break a build if user's package data has read only flag.
* #1431: In ``easy_install.check_site_dir``, ensure the installation directory exists.
* #1563: In ``pkg_resources`` prefer ``find_spec`` (PEP 451) to ``find_module``.

Incorporate changes from v44.1.0:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* #1704: Set sys.argv[0] in setup script run by build_meta.__legacy__
* #1959: Fix for Python 4: replace unsafe six.PY3 with six.PY2
* #1994: Fixed a bug in the "setuptools.finalize_distribution_options" hook that lead to ignoring the order attribute of entry points managed by this hook.


v44.1.0
-------



Changes
^^^^^^^
* #1704: Set sys.argv[0] in setup script run by build_meta.__legacy__
* #1959: Fix for Python 4: replace unsafe six.PY3 with six.PY2
* #1994: Fixed a bug in the "setuptools.finalize_distribution_options" hook that lead to ignoring the order attribute of entry points managed by this hook.


v46.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #65: Once again as in 3.0, removed the Features feature.

Changes
^^^^^^^
* #1890: Fix vendored dependencies so importing ``setuptools.extern.some_module`` gives the same object as ``setuptools._vendor.some_module``. This makes Metadata picklable again.
* #1899: Test suite now fails on warnings.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #2011: Fix broken link to distutils docs on package_data

Misc
^^^^
* #1991: Include pkg_resources test data in sdist, so tests can be executed from it.


v45.3.0
-------



Changes
^^^^^^^
* #1557: Deprecated eggsecutable scripts and updated docs.
* #1904: Update msvc.py to use CPython 3.8.0 mechanism to find msvc 14+


v45.2.0
-------



Changes
^^^^^^^
* #1905: Fixed defect in _imp, introduced in 41.6.0 when the 'tests' directory is not present.
* #1941: Improve editable installs with PEP 518 build isolation:

  * The ``--user`` option is now always available. A warning is issued if the user site directory is not available.
  * The error shown when the install directory is not in ``PYTHONPATH`` has been turned into a warning.
* #1981: Setuptools now declares its ``tests`` and ``docs`` dependencies in metadata (extras).
* #1985: Add support for installing scripts in environments where bdist_wininst is missing (i.e. Python 3.9).

Misc
^^^^
* #1968: Add flake8-2020 to check for misuse of sys.version or sys.version_info.


v45.1.0
-------



Changes
^^^^^^^
* #1458: Add minimum sunset date and preamble to Python 2 warning.
* #1704: Set sys.argv[0] in setup script run by build_meta.__legacy__
* #1974: Add Python 3 Only Trove Classifier and remove universal wheel declaration for more complete transition from Python 2.


v45.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1458: Drop support for Python 2. Setuptools now requires Python 3.5 or later. Install setuptools using pip >=9 or pin to Setuptools <45 to maintain 2.7 support.

Changes
^^^^^^^
* #1959: Fix for Python 4: replace unsafe six.PY3 with six.PY2


v44.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1908: Drop support for Python 3.4.


v43.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1634: Include ``pyproject.toml`` in source distribution by default. Projects relying on the previous behavior where ``pyproject.toml`` was excluded by default should stop relying on that behavior or add ``exclude pyproject.toml`` to their MANIFEST.in file.

Changes
^^^^^^^
* #1927: Setuptools once again declares 'setuptools' in the ``build-system.requires`` and adds PEP 517 build support by declaring itself as the ``build-backend``. It additionally specifies ``build-system.backend-path`` to rely on itself for those builders that support it.


v42.0.2
-------

Changes
^^^^^^^

* #1921: Fix support for easy_install's ``find-links`` option in ``setup.cfg``.
* #1922: Build dependencies (setup_requires and tests_require) now install transitive dependencies indicated by extras.


v42.0.1
-------



Changes
^^^^^^^
* #1918: Fix regression in handling wheels compatibility tags.


v42.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1830, #1909: Mark the easy_install script and setuptools command as deprecated, and use `pip <https://pip.pypa.io/en/stable/>`_ when available to fetch/build wheels for missing ``setup_requires``/``tests_require`` requirements, with the following differences in behavior:
   * support for ``python_requires``
   * better support for wheels (proper handling of priority with respect to PEP 425 tags)
   * PEP 517/518 support
   * eggs are not supported
   * no support for the ``allow_hosts`` easy_install option (``index_url``/``find_links`` are still honored)
   * pip environment variables are honored (and take precedence over easy_install options)
* #1898: Removed the "upload" and "register" commands in favor of `twine <https://pypi.org/p/twine>`_.

Changes
^^^^^^^
* #1767: Add support for the ``license_files`` option in ``setup.cfg`` to automatically
  include multiple license files in a source distribution.
* #1829: Update handling of wheels compatibility tags:
  * add support for manylinux2010
  * fix use of removed 'm' ABI flag in Python 3.8 on Windows
* #1861: Fix empty namespace package installation from wheel.
* #1877: Setuptools now exposes a new entry point hook "setuptools.finalize_distribution_options", enabling plugins like `setuptools_scm <https://pypi.org/project/setuptools_scm>`_ to configure options on the distribution at finalization time.


v41.6.0
-------



Changes
^^^^^^^
* #479: Replace usage of deprecated ``imp`` module with local re-implementation in ``setuptools._imp``.


v41.5.1
-------



Changes
^^^^^^^
* #1891: Fix code for detecting Visual Studio's version on Windows under Python 2.


v41.5.0
-------



Changes
^^^^^^^
* #1811: Improve Visual C++ 14.X support, mainly for Visual Studio 2017 and 2019.
* #1814: Fix ``pkg_resources.Requirement`` hash/equality implementation: take PEP 508 direct URL into account.
* #1824: Fix tests when running under ``python3.10``.
* #1878: Formally deprecated the ``test`` command, with the recommendation that users migrate to ``tox``.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1860: Update documentation to mention the egg format is not supported by pip and dependency links support was dropped starting with pip 19.0.
* #1862: Drop ez_setup documentation: deprecated for some time (last updated in 2016), and still relying on easy_install (deprecated too).
* #1868: Drop most documentation references to (deprecated) EasyInstall.
* #1884: Added a trove classifier to document support for Python 3.8.

Misc
^^^^
* #1886: Added Python 3.8 release to the Travis test matrix.


v41.4.0
-------



Changes
^^^^^^^
* #1847: In declarative config, now traps errors when invalid ``python_requires`` values are supplied.


v41.3.0
-------



Changes
^^^^^^^
* #1690: When storing extras, rely on OrderedSet to retain order of extras as indicated by the packager, which will also be deterministic on Python 2.7 (with PYTHONHASHSEED unset) and Python 3.6+.

Misc
^^^^
* #1858: Fixed failing integration test triggered by 'long_description_content_type' in packaging.


v41.2.0
-------



Changes
^^^^^^^
* #479: Remove some usage of the deprecated ``imp`` module.

Misc
^^^^
* #1565: Changed html_sidebars from string to list of string as per
  https://www.sphinx-doc.org/en/master/changes.html#id58


v41.1.0
-------



Misc
^^^^
* #1697: Moved most of the constants from setup.py to setup.cfg
* #1749: Fixed issue with the PEP 517 backend where building a source distribution would fail if any tarball existed in the destination directory.
* #1750: Fixed an issue with PEP 517 backend where wheel builds would fail if the destination directory did not already exist.
* #1756: Force metadata-version >= 1.2. when project urls are present.
* #1769: Improve ``package_data`` check: ensure the dictionary values are lists/tuples of strings.
* #1788: Changed compatibility fallback logic for ``html.unescape`` to avoid accessing ``HTMLParser.unescape`` when not necessary. ``HTMLParser.unescape`` is deprecated and will be removed in Python 3.9.
* #1790: Added the file path to the error message when a ``UnicodeDecodeError`` occurs while reading a metadata file.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1776: Use license classifiers rather than the license field.


v41.0.1
-------



Changes
^^^^^^^
* #1671: Fixed issue with the PEP 517 backend that prevented building a wheel when the ``dist/`` directory contained existing ``.whl`` files.
* #1709: In test.paths_on_python_path, avoid adding unnecessary duplicates to the PYTHONPATH.
* #1741: In package_index, now honor "current directory" during a checkout of git and hg repositories under Windows


v41.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1735: When parsing setup.cfg files, setuptools now requires the files to be encoded as UTF-8. Any other encoding will lead to a UnicodeDecodeError. This change removes support for specifying an encoding using a 'coding: ' directive in the header of the file, a feature that was introduces in 40.7. Given the recent release of the aforementioned feature, it is assumed that few if any projects are utilizing the feature to specify an encoding other than UTF-8.


v40.9.0
-------



Changes
^^^^^^^
* #1675: Added support for ``setup.cfg``-only projects when using the ``setuptools.build_meta`` backend. Projects that have enabled PEP 517 no longer need to have a ``setup.py`` and can use the purely declarative ``setup.cfg`` configuration file instead.
* #1720: Added support for ``pkg_resources.parse_requirements``-style requirements in ``setup_requires`` when ``setup.py`` is invoked from the ``setuptools.build_meta`` build backend.
* #1664: Added the path to the ``PKG-INFO`` or ``METADATA`` file in the exception
  text when the ``Version:`` header can't be found.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1705: Removed some placeholder documentation sections referring to deprecated features.


v40.8.0
-------



Changes
^^^^^^^
* #1652: Added the ``build_meta:__legacy__`` backend, a "compatibility mode" PEP 517 backend that can be used as the default when ``build-backend`` is left unspecified in ``pyproject.toml``.
* #1635: Resource paths are passed to ``pkg_resources.resource_string`` and similar no longer accept paths that traverse parents, that begin with a leading ``/``. Violations of this expectation raise DeprecationWarnings and will become errors. Additionally, any paths that are absolute on Windows are strictly disallowed and will raise ValueErrors.
* #1536: ``setuptools`` will now automatically include licenses if ``setup.cfg`` contains a ``license_file`` attribute, unless this file is manually excluded inside ``MANIFEST.in``.


v40.7.3
-------



Changes
^^^^^^^
* #1670: In package_index, revert to using a copy of splituser from Python 3.8. Attempts to use ``urllib.parse.urlparse`` led to problems as reported in #1663 and #1668. This change serves as an alternative to #1499 and fixes #1668.


v40.7.2
-------



Changes
^^^^^^^
* #1666: Restore port in URL handling in package_index.


v40.7.1
-------



Changes
^^^^^^^
* #1660: On Python 2, when reading config files, downcast options from text to bytes to satisfy distutils expectations.


v40.7.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1551: File inputs for the ``license`` field in ``setup.cfg`` files now explicitly raise an error.

Changes
^^^^^^^
* #1180: Add support for non-ASCII in setup.cfg (#1062). Add support for native strings on some parameters (#1136).
* #1499: ``setuptools.package_index`` no longer relies on the deprecated ``urllib.parse.splituser`` per Python #27485.
* #1544: Added tests for PackageIndex.download (for git URLs).
* #1625: In PEP 517 build_meta builder, ensure that sdists are built as gztar per the spec.


v40.6.3
-------



Changes
^^^^^^^
* #1594: PEP 517 backend no longer declares setuptools as a dependency as it can be assumed.


v40.6.2
-------



Changes
^^^^^^^
* #1592: Fix invalid dependency on external six module (instead of vendored version).


v40.6.1
-------



Changes
^^^^^^^
* #1590: Fixed regression where packages without ``author`` or ``author_email`` fields generated malformed package metadata.


v40.6.0
-------



Deprecations
^^^^^^^^^^^^
* #1541: Officially deprecated the ``requires`` parameter in ``setup()``.

Changes
^^^^^^^
* #1519: In ``pkg_resources.normalize_path``, additional path normalization is now performed to ensure path values to a directory is always the same, preventing false positives when checking scripts have a consistent prefix to set up on Windows.
* #1545: Changed the warning class of all deprecation warnings; deprecation warning classes are no longer derived from ``DeprecationWarning`` and are thus visible by default.
* #1554: ``build_meta.build_sdist`` now includes ``setup.py`` in source distributions by default.
* #1576: Started monkey-patching ``get_metadata_version`` and ``read_pkg_file`` onto ``distutils.DistributionMetadata`` to retain the correct version on the ``PKG-INFO`` file in the (deprecated) ``upload`` command.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1395: Changed Pyrex references to Cython in the documentation.
* #1456: Documented that the ``rpmbuild`` packages is required for the ``bdist_rpm`` command.
* #1537: Documented how to use ``setup.cfg`` for ``src/ layouts``
* #1539: Added minimum version column in ``setup.cfg`` metadata table.
* #1552: Fixed a minor typo in the python 2/3 compatibility documentation.
* #1553: Updated installation instructions to point to ``pip install`` instead of ``ez_setup.py``.
* #1560: Updated ``setuptools`` distribution documentation to remove some outdated information.
* #1564: Documented ``setup.cfg`` minimum version for version and project_urls.

Misc
^^^^
* #1533: Restricted the ``recursive-include setuptools/_vendor`` to contain only .py and .txt files.
* #1572: Added the ``concurrent.futures`` backport ``futures`` to the Python 2.7 test suite requirements.


v40.5.0
-------



Changes
^^^^^^^
* #1335: In ``pkg_resources.normalize_path``, fix issue on Cygwin when cwd contains symlinks.
* #1502: Deprecated support for downloads from Subversion in package_index/easy_install.
* #1517: Dropped use of six.u in favor of ``u""`` literals.
* #1520: Added support for ``data_files`` in ``setup.cfg``.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1525: Fixed rendering of the deprecation warning in easy_install doc.


v40.4.3
-------



Changes
^^^^^^^
* #1480: Bump vendored pyparsing in pkg_resources to 2.2.1.


v40.4.2
-------



Misc
^^^^
* #1497: Updated gitignore in repo.


v40.4.1
-------



Changes
^^^^^^^
* #1480: Bump vendored pyparsing to 2.2.1.


v40.4.0
-------



Changes
^^^^^^^
* #1481: Join the sdist ``--dist-dir`` and the ``build_meta`` sdist directory argument to point to the same target (meaning the build frontend no longer needs to clean manually the dist dir to avoid multiple sdist presence, and setuptools no longer needs to handle conflicts between the two).


v40.3.0
-------



Changes
^^^^^^^
* #1402: Fixed a bug with namespace packages under Python 3.6 when one package in
  current directory hides another which is installed.
* #1427: Set timestamp of ``.egg-info`` directory whenever ``egg_info`` command is run.
* #1474: ``build_meta.get_requires_for_build_sdist`` now does not include the ``wheel`` package anymore.
* #1486: Suppress warnings in pkg_resources.handle_ns.

Misc
^^^^
* #1479: Remove internal use of six.binary_type.


v40.2.0
-------



Changes
^^^^^^^
* #1466: Fix handling of Unicode arguments in PEP 517 backend


v40.1.1
--------



Changes
^^^^^^^
* #1465: Fix regression with ``egg_info`` command when tagging is used.


v40.1.0
-------



Changes
^^^^^^^
* #1410: Deprecated ``upload`` and ``register`` commands.
* #1312: Introduced find_namespace_packages() to find PEP 420 namespace packages.
* #1420: Added find_namespace: directive to config parser.
* #1418: Solved race in when creating egg cache directories.
* #1450: Upgraded vendored PyParsing from 2.1.10 to 2.2.0.
* #1451: Upgraded vendored appdirs from 1.4.0 to 1.4.3.
* #1388: Fixed "Microsoft Visual C++ Build Tools" link in exception when Visual C++ not found.
* #1389: Added support for scripts which have unicode content.
* #1416: Moved several Python version checks over to using ``six.PY2`` and ``six.PY3``.

Misc
^^^^
* #1441: Removed spurious executable permissions from files that don't need them.


v40.0.0
-------



Breaking Changes
^^^^^^^^^^^^^^^^
* #1342: Drop support for Python 3.3.

Changes
^^^^^^^
* #1366: In package_index, fixed handling of encoded entities in URLs.
* #1383: In pkg_resources VendorImporter, avoid removing packages imported from the root.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1379: Minor doc fixes after actually using the new release process.
* #1385: Removed section on non-package data files.
* #1403: Fix developer's guide.

Misc
^^^^
* #1404: Fix PEP 518 configuration: set build requirements in ``pyproject.toml`` to ``["wheel"]``.


v39.2.0
-------



Changes
^^^^^^^
* #1359: Support using "file:" to load a PEP 440-compliant package version from
  a text file.
* #1360: Fixed issue with a mismatch between the name of the package and the
  name of the .dist-info file in wheel files
* #1364: Add ``__dir__()`` implementation to ``pkg_resources.Distribution()`` that
  includes the attributes in the ``_provider`` instance variable.
* #1365: Take the package_dir option into account when loading the version from
  a module attribute.

Documentation changes
^^^^^^^^^^^^^^^^^^^^^
* #1353: Added coverage badge to README.
* #1356: Made small fixes to the developer guide documentation.
* #1357: Fixed warnings in documentation builds and started enforcing that the
  docs build without warnings in tox.
* #1376: Updated release process docs.

Misc
^^^^
* #1343: The ``setuptools`` specific ``long_description_content_type``,
  ``project_urls`` and ``provides_extras`` fields are now set consistently
  after any ``distutils`` ``setup_keywords`` calls, allowing them to override
  values.
* #1352: Added ``tox`` environment for documentation builds.
* #1354: Added ``towncrier`` for changelog management.
* #1355: Add PR template.
* #1368: Fixed tests which failed without network connectivity.
* #1369: Added unit tests for PEP 425 compatibility tags support.
* #1372: Stop testing Python 3.3 in Travis CI, now that the latest version of
  ``wheel`` no longer installs on it.

v39.1.0
-------

* #1340: Update all PyPI URLs to reflect the switch to the
  new Warehouse codebase.
* #1337: In ``pkg_resources``, now support loading resources
  for modules loaded by the ``SourcelessFileLoader``.
* #1332: Silence spurious wheel related warnings on Windows.

v39.0.1
-------

* #1297: Restore Unicode handling for Maintainer fields in
  metadata.

v39.0.0
-------

* #1296: Setuptools now vendors its own direct dependencies, no
  longer relying on the dependencies as vendored by pkg_resources.

* #296: Removed long-deprecated support for iteration on
  Version objects as returned by ``pkg_resources.parse_version``.
  Removed the ``SetuptoolsVersion`` and
  ``SetuptoolsLegacyVersion`` names as well. They should not
  have been used, but if they were, replace with
  ``Version`` and ``LegacyVersion`` from ``packaging.version``.

v38.7.0
-------

* #1288: Add support for maintainer in PKG-INFO.

v38.6.1
-------

* #1292: Avoid generating ``Provides-Extra`` in metadata when
  no extra is present (but environment markers are).

v38.6.0
-------

* #1286: Add support for Metadata 2.1 (PEP 566).

v38.5.2
-------

* #1285: Fixed RuntimeError in pkg_resources.parse_requirements
  on Python 3.7 (stemming from PEP 479).

v38.5.1
-------

* #1271: Revert to Cython legacy ``build_ext`` behavior for
  compatibility.

v38.5.0
-------

* #1229: Expand imports in ``build_ext`` to refine detection of
  Cython availability.

* #1270: When Cython is available, ``build_ext`` now uses the
  new_build_ext.

v38.4.1
-------

* #1257: In bdist_egg.scan_module, fix ValueError on Python 3.7.

v38.4.0
-------

* #1231: Removed warning when PYTHONDONTWRITEBYTECODE is enabled.

v38.3.0
-------

* #1210: Add support for PEP 345 Project-URL metadata.
* #1207: Add support for ``long_description_type`` to setup.cfg
  declarative config as intended and documented.

v38.2.5
-------

* #1232: Fix trailing slash handling in ``pkg_resources.ZipProvider``.

v38.2.4
-------

* #1220: Fix ``data_files`` handling when installing from wheel.

v38.2.3
-------

* fix Travis' Python 3.3 job.

v38.2.2
-------

* #1214: fix handling of namespace packages when installing
  from a wheel.

v38.2.1
-------

* #1212: fix encoding handling of metadata when installing
  from a wheel.

v38.2.0
-------

* #1200: easy_install now support installing from wheels:
  they will be installed as standalone unzipped eggs.

v38.1.0
-------

* #1208: Improve error message when failing to locate scripts
  in egg-info metadata.

v38.0.0
-------

* #458: In order to support deterministic builds, Setuptools no
  longer allows packages to declare ``install_requires`` as
  unordered sequences (sets or dicts).

v37.0.0
-------

* #878: Drop support for Python 2.6. Python 2.6 users should
  rely on 'setuptools < 37dev'.

v36.8.0
-------

* #1190: In SSL support for package index operations, use SNI
  where available.

v36.7.3
-------

* #1175: Bug fixes to ``build_meta`` module.

v36.7.2
-------

* #701: Fixed duplicate test discovery on Python 3.

v36.7.1
-------

* #1193: Avoid test failures in bdist_egg when
  PYTHONDONTWRITEBYTECODE is set.

v36.7.0
-------

* #1054: Support ``setup_requires`` in ``setup.cfg`` files.

v36.6.1
-------

* #1132: Removed redundant and costly serialization/parsing step
  in ``EntryPoint.__init__``.

* #844: ``bdist_egg --exclude-source-files`` now tested and works
  on Python 3.

v36.6.0
-------

* #1143: Added ``setuptools.build_meta`` module, an implementation
  of PEP-517 for Setuptools-defined packages.

* #1143: Added ``dist_info`` command for producing dist_info
  metadata.

v36.5.0
-------

* #170: When working with Mercurial checkouts, use Windows-friendly
  syntax for suppressing output.

* Inspired by #1134, performed substantial refactoring of
  ``pkg_resources.find_on_path`` to facilitate an optimization
  for paths with many non-version entries.

v36.4.0
-------

* #1075: Add new ``Description-Content-Type`` metadata field. `See here for
  documentation on how to use this field.
  <https://packaging.python.org/specifications/#description-content-type>`_

* #1068: Sort files and directories when building eggs for
  deterministic order.

* #196: Remove caching of easy_install command in fetch_build_egg.
  Fixes issue where ``pytest-runner-N.N`` would satisfy the installation
  of ``pytest``.

* #1129: Fix working set dependencies handling when replacing conflicting
  distributions (e.g. when using ``setup_requires`` with a conflicting
  transitive dependency, fix #1124).

* #1133: Improved handling of README files extensions and added
  Markdown to the list of searched READMES.

* #1135: Improve performance of pkg_resources import by not invoking
  ``access`` or ``stat`` and using ``os.listdir`` instead.

v36.3.0
-------

* #1131: Make possible using several files within ``file:`` directive
  in metadata.long_description in ``setup.cfg``.

v36.2.7
-------

* fix #1105: Fix handling of requirements with environment
  markers when declared in ``setup.cfg`` (same treatment as
  for #1081).

v36.2.6
-------

* #462: Don't assume a directory is an egg by the ``.egg``
  extension alone.

v36.2.5
-------

* #1093: Fix test command handler with extras_require.
* #1112, #1091, #1115: Now using Trusty containers in
  Travis for CI and CD.

v36.2.4
-------

* #1092: ``pkg_resources`` now uses ``inspect.getmro`` to
  resolve classes in method resolution order.

v36.2.3
-------

* #1102: Restore behavior for empty extras.

v36.2.2
-------

* #1099: Revert commit a3ec721, restoring intended purpose of
  extras as part of a requirement declaration.

v36.2.1
-------

* fix #1086
* fix #1087
* support extras specifiers in install_requires requirements

v36.2.0
-------

* #1081: Environment markers indicated in ``install_requires``
  are now processed and treated as nameless ``extras_require``
  with markers, allowing their metadata in requires.txt to be
  correctly generated.

* #1053: Tagged commits are now released using Travis-CI
  build stages, meaning releases depend on passing tests on
  all supported Python versions (Linux) and not just the latest
  Python version.

v36.1.1
-------

* #1083: Correct ``py31compat.makedirs`` to correctly honor
  ``exist_ok`` parameter.
* #1083: Also use makedirs compatibility throughout setuptools.

v36.1.0
-------

* #1083: Avoid race condition on directory creation in
  ``pkg_resources.ensure_directory``.

* Removed deprecation of and restored support for
  ``upload_docs`` command for sites other than PyPI.
  Only warehouse is dropping support, but services like
  `devpi <http://doc.devpi.net/latest/>`_ continue to
  support docs built by setuptools' plugins. See
  `this comment <https://bitbucket.org/hpk42/devpi/issues/388/support-rtd-model-for-building-uploading#comment-34292423>`_
  for more context on the motivation for this change.

v36.0.1
-------

* #1042: Fix import in py27compat module that still
  referenced six directly, rather than through the externs
  module (vendored packages hook).

v36.0.0
-------

* #980 and others: Once again, Setuptools vendors all
  of its dependencies. It seems to be the case that in
  the Python ecosystem, all build tools must run without
  any dependencies (build, runtime, or otherwise). At
  such a point that a mechanism exists that allows
  build tools to have dependencies, Setuptools will adopt
  it.

v35.0.2
-------

* #1015: Fix test failures on Python 3.7.

* #1024: Add workaround for Jython #2581 in monkey module.

v35.0.1
-------

* #992: Revert change introduced in v34.4.1, now
  considered invalid.

* #1016: Revert change introduced in v35.0.0 per #1014,
  referencing #436. The approach had unintended
  consequences, causing sdist installs to be missing
  files.

v35.0.0
-------

* #436: In egg_info.manifest_maker, no longer read
  the file list from the manifest file, and instead
  re-build it on each build. In this way, files removed
  from the specification will not linger in the manifest.
  As a result, any files manually added to the manifest
  will be removed on subsequent egg_info invocations.
  No projects should be manually adding files to the
  manifest and should instead use MANIFEST.in or SCM
  file finders to force inclusion of files in the manifest.

v34.4.1
-------

* #1008: In MSVC support, use always the last version available for Windows SDK and UCRT SDK.

* #1008: In MSVC support, fix "vcruntime140.dll" returned path with Visual Studio 2017.

* #992: In msvc.msvc9_query_vcvarsall, ensure the
  returned dicts have str values and not Unicode for
  compatibility with os.environ.

v34.4.0
-------

* #995: In MSVC support, add support for "Microsoft Visual Studio 2017" and "Microsoft Visual Studio Build Tools 2017".

* #999 via #1007: Extend support for declarative package
  config in a setup.cfg file to include the options
  ``python_requires`` and ``py_modules``.

v34.3.3
-------

* #967 (and #997): Explicitly import submodules of
  packaging to account for environments where the imports
  of those submodules is not implied by other behavior.

v34.3.2
-------

* #993: Fix documentation upload by correcting
  rendering of content-type in _build_multipart
  on Python 3.

v34.3.1
-------

* #988: Trap ``os.unlink`` same as ``os.remove`` in
  ``auto_chmod`` error handler.

* #983: Fixes to invalid escape sequence deprecations on
  Python 3.6.

v34.3.0
-------

* #941: In the upload command, if the username is blank,
  default to ``getpass.getuser()``.

* #971: Correct distutils findall monkeypatch to match
  appropriate versions (namely Python 3.4.6).

v34.2.0
-------

* #966: Add support for reading dist-info metadata and
  thus locating Distributions from zip files.

* #968: Allow '+' and '!' in egg fragments
  so that it can take package names that contain
  PEP 440 conforming version specifiers.

v34.1.1
-------

* #953: More aggressively employ the compatibility issue
  originally added in #706.

v34.1.0
-------

* #930: ``build_info`` now accepts two new parameters
  to optimize and customize the building of C libraries.

v34.0.3
-------

* #947: Loosen restriction on the version of six required,
  restoring compatibility with environments relying on
  six 1.6.0 and later.

v34.0.2
-------

* #882: Ensure extras are honored when building the
  working set.
* #913: Fix issue in develop if package directory has
  a trailing slash.

v34.0.1
-------

* #935: Fix glob syntax in graft.

v34.0.0
-------

* #581: Instead of vendoring the growing list of
  dependencies that Setuptools requires to function,
  Setuptools now requires these dependencies just like
  any other project. Unlike other projects, however,
  Setuptools cannot rely on ``setup_requires`` to
  demand the dependencies it needs to install because
  its own machinery would be necessary to pull those
  dependencies if not present (a bootstrapping problem).
  As a result, Setuptools no longer supports self upgrade or
  installation in the general case. Instead, users are
  directed to use pip to install and upgrade using the
  ``wheel`` distributions of setuptools.

  Users are welcome to contrive other means to install
  or upgrade Setuptools using other means, such as
  pre-installing the Setuptools dependencies with pip
  or a bespoke bootstrap tool, but such usage is not
  recommended and is not supported.

  As discovered in #940, not all versions of pip will
  successfully install Setuptools from its pre-built
  wheel. If you encounter issues with "No module named
  six" or "No module named packaging", especially
  following a line "Running setup.py egg_info for package
  setuptools", then your pip is not new enough.

  There's an additional issue in pip where setuptools
  is upgraded concurrently with other source packages,
  described in pip #4253. The proposed workaround is to
  always upgrade Setuptools first prior to upgrading
  other packages that would upgrade Setuptools.

v33.1.1
-------

* #921: Correct issue where certifi fallback not being
  reached on Windows.

v33.1.0
-------

Installation via pip, as indicated in the `Python Packaging
User's Guide <https://packaging.python.org/installing/>`_,
is the officially-supported mechanism for installing
Setuptools, and this recommendation is now explicit in the
much more concise README.

Other edits and tweaks were made to the documentation. The
codebase is unchanged.

v33.0.0
-------

* #619: Removed support for the ``tag_svn_revision``
  distribution option. If Subversion tagging support is
  still desired, consider adding the functionality to
  setuptools_svn in setuptools_svn #2.

v32.3.1
-------

* #866: Use ``dis.Bytecode`` on Python 3.4 and later in
  ``setuptools.depends``.

v32.3.0
-------

* #889: Backport proposed fix for disabling interpolation in
  distutils.Distribution.parse_config_files.

v32.2.0
-------

* #884: Restore support for running the tests under
  `pytest-runner <https://github.com/pytest-dev/pytest-runner>`_
  by ensuring that PYTHONPATH is honored in tests invoking
  a subprocess.

v32.1.3
-------

* #706: Add rmtree compatibility shim for environments where
  rmtree fails when passed a unicode string.

v32.1.2
-------

* #893: Only release sdist in zip format as warehouse now
  disallows releasing two different formats.

v32.1.1
-------

* #704: More selectively ensure that 'rmtree' is not invoked with
  a byte string, enabling it to remove files that are non-ascii,
  even on Python 2.

* #712: In 'sandbox.run_setup', ensure that ``__file__`` is
  always a ``str``, modeling the behavior observed by the
  interpreter when invoking scripts and modules.

v32.1.0
-------

* #891: In 'test' command on test failure, raise DistutilsError,
  suppression invocation of subsequent commands.

v32.0.0
-------

* #890: Revert #849. ``global-exclude .foo`` will not match all
  ``*.foo`` files any more. Package authors must add an explicit
  wildcard, such as ``global-exclude *.foo``, to match all
  ``.foo`` files. See #886, #849.

v31.0.1
-------

* #885: Fix regression where 'pkg_resources._rebuild_mod_path'
  would fail when a namespace package's '__path__' was not
  a list with a sort attribute.

v31.0.0
-------

* #250: Install '-nspkg.pth' files for packages installed
  with 'setup.py develop'. These .pth files allow
  namespace packages installed by pip or develop to
  co-mingle. This change required the removal of the
  change for #805 and pip #1924, introduced in 28.3.0 and implicated
  in #870, but means that namespace packages not in a
  site packages directory will no longer work on Python
  earlier than 3.5, whereas before they would work on
  Python not earlier than 3.3.

v30.4.0
-------

* #879: For declarative config:

  - read_configuration() now accepts ignore_option_errors argument. This allows scraping tools to read metadata without a need to download entire packages. E.g. we can gather some stats right from GitHub repos just by downloading setup.cfg.

  - packages find: directive now supports fine tuning from a subsection. The same arguments as for find() are accepted.

v30.3.0
-------

* #394 via #862: Added support for `declarative package
  config in a setup.cfg file
  <https://setuptools.pypa.io/en/latest/setuptools.html#configuring-setup-using-setup-cfg-files>`_.

v30.2.1
-------

* #850: In test command, invoke unittest.main with
  indication not to exit the process.

v30.2.0
-------

* #854: Bump to vendored Packaging 16.8.

v30.1.0
-------

* #846: Also trap 'socket.error' when opening URLs in
  package_index.

* #849: Manifest processing now matches the filename
  pattern anywhere in the filename and not just at the
  start. Restores behavior found prior to 28.5.0.

v30.0.0
-------

* #864: Drop support for Python 3.2. Systems requiring
  Python 3.2 support must use 'setuptools < 30'.

* #825: Suppress warnings for single files.

* #830 via #843: Once again restored inclusion of data
  files to sdists, but now trap TypeError caused by
  techniques employed rjsmin and similar.

v29.0.1
-------

* #861: Re-release of v29.0.1 with the executable script
  launchers bundled. Now, launchers are included by default
  and users that want to disable this behavior must set the
  environment variable
  'SETUPTOOLS_INSTALL_WINDOWS_SPECIFIC_FILES' to
  a false value like "false" or "0".

v29.0.0
-------

* #841: Drop special exception for packages invoking
  win32com during the build/install process. See
  Distribute #118 for history.

v28.8.0
-------

* #629: Per the discussion, refine the sorting to use version
  value order for more accurate detection of the latest
  available version when scanning for packages. See also
  #829.

* #837: Rely on the config var "SO" for Python 3.3.0 only
  when determining the ext filename.

v28.7.1
-------

* #827: Update PyPI root for dependency links.

* #833: Backed out changes from #830 as the implementation
  seems to have problems in some cases.

v28.7.0
-------

* #832: Moved much of the namespace package handling
  functionality into a separate module for re-use in something
  like #789.
* #830: ``sdist`` command no longer suppresses the inclusion
  of data files, re-aligning with the expectation of distutils
  and addressing #274 and #521.

v28.6.1
-------

* #816: Fix manifest file list order in tests.

v28.6.0
-------

* #629: When scanning for packages, ``pkg_resources`` now
  ignores empty egg-info directories and gives precedence to
  packages whose versions are lexicographically greatest,
  a rough approximation for preferring the latest available
  version.

v28.5.0
-------

* #810: Tests are now invoked with tox and not setup.py test.
* #249 and #450 via #764: Avoid scanning the whole tree
  when building the manifest. Also fixes a long-standing bug
  where patterns in ``MANIFEST.in`` had implicit wildcard
  matching. This caused ``global-exclude .foo`` to exclude
  all ``*.foo`` files, but also ``global-exclude bar.py`` to
  exclude ``foo_bar.py``.

v28.4.0
-------

* #732: Now extras with a hyphen are honored per PEP 426.
* #811: Update to pyparsing 2.1.10.
* Updated ``setuptools.command.sdist`` to re-use most of
  the functionality directly from ``distutils.command.sdist``
  for the ``add_defaults`` method with strategic overrides.
  See #750 for rationale.
* #760 via #762: Look for certificate bundle where SUSE
  Linux typically presents it. Use ``certifi.where()`` to locate
  the bundle.

v28.3.0
-------

* #809: In ``find_packages()``, restore support for excluding
  a parent package without excluding a child package.

* #805: Disable ``-nspkg.pth`` behavior on Python 3.3+ where
  PEP-420 functionality is adequate. Fixes pip #1924.

v28.1.0
-------

* #803: Bump certifi to 2016.9.26.

v28.0.0
-------

* #733: Do not search excluded directories for packages.
  This introduced a backwards incompatible change in ``find_packages()``
  so that ``find_packages(exclude=['foo']) == []``, excluding subpackages of ``foo``.
  Previously, ``find_packages(exclude=['foo']) == ['foo.bar']``,
  even though the parent ``foo`` package was excluded.

* #795: Bump certifi.

* #719: Suppress decoding errors and instead log a warning
  when metadata cannot be decoded.

v27.3.1
-------

* #790: In MSVC monkeypatching, explicitly patch each
  function by name in the target module instead of inferring
  the module from the function's ``__module__``. Improves
  compatibility with other packages that might have previously
  patched distutils functions (i.e. NumPy).

v27.3.0
-------

* #794: In test command, add installed eggs to PYTHONPATH
  when invoking tests so that subprocesses will also have the
  dependencies available. Fixes `tox 330
  <https://github.com/tox-dev/tox/issues/330>`_.

* #795: Update vendored pyparsing 2.1.9.

v27.2.0
-------

* #520 and #513: Suppress ValueErrors in fixup_namespace_packages
  when lookup fails.

* Nicer, more consistent interfaces for msvc monkeypatching.

v27.1.2
-------

* #779 via #781: Fix circular import.

v27.1.1
-------

* #778: Fix MSVC monkeypatching.

v27.1.0
-------

* Introduce the (private) ``monkey`` module to encapsulate
  the distutils monkeypatching behavior.

v27.0.0
-------

* Now use Warehouse by default for
  ``upload``, patching ``distutils.config.PyPIRCCommand`` to
  affect default behavior.

  Any config in .pypirc should be updated to replace

    https://pypi.python.org/pypi/

  with

    https://upload.pypi.org/legacy/

  Similarly, any passwords stored in the keyring should be
  updated to use this new value for "system".

  The ``upload_docs`` command will continue to use the python.org
  site, but the command is now deprecated. Users are urged to use
  Read The Docs instead.

* #776: Use EXT_SUFFIX for py_limited_api renaming.

* #774 and #775: Use LegacyVersion from packaging when
  detecting numpy versions.

v26.1.1
-------

* Re-release of 26.1.0 with pytest pinned to allow for automated
  deployment and thus proper packaging environment variables,
  fixing issues with missing executable launchers.

v26.1.0
-------

* #763: ``pkg_resources.get_default_cache`` now defers to the
  `appdirs project <https://pypi.org/project/appdirs>`_ to
  resolve the cache directory. Adds a vendored dependency on
  appdirs to pkg_resources.

v26.0.0
-------

* #748: By default, sdists are now produced in gzipped tarfile
  format by default on all platforms, adding forward compatibility
  for the same behavior in Python 3.6 (See Python #27819).

* #459 via #736: On Windows with script launchers,
  sys.argv[0] now reflects
  the name of the entry point, consistent with the behavior in
  distlib and pip wrappers.

* #752 via #753: When indicating ``py_limited_api`` to Extension,
  it must be passed as a keyword argument.

v25.4.0
-------

* Add Extension(py_limited_api=True). When set to a truthy value,
  that extension gets a filename appropriate for code using Py_LIMITED_API.
  When used correctly this allows a single compiled extension to work on
  all future versions of CPython 3.
  The py_limited_api argument only controls the filename. To be
  compatible with multiple versions of Python 3, the C extension
  will also need to set -DPy_LIMITED_API=... and be modified to use
  only the functions in the limited API.

v25.3.0
-------

* #739 Fix unquoted libpaths by fixing compatibility between ``numpy.distutils`` and ``distutils._msvccompiler`` for numpy < 1.11.2 (Fix issue #728, error also fixed in Numpy).

* #731: Bump certifi.

* Style updates. See #740, #741, #743, #744, #742, #747.

* #735: include license file.

v25.2.0
-------

* #612 via #730: Add a LICENSE file which needs to be provided by the terms of
  the MIT license.

v25.1.6
-------

* #725: revert ``library_dir_option`` patch (Error is related to ``numpy.distutils`` and make errors on non Numpy users).

v25.1.5
-------

* #720
* #723: Improve patch for ``library_dir_option``.

v25.1.4
-------

* #717
* #713
* #707: Fix Python 2 compatibility for MSVC by catching errors properly.
* #715: Fix unquoted libpaths by patching ``library_dir_option``.

v25.1.3
-------

* #714 and #704: Revert fix as it breaks other components
  downstream that can't handle unicode. See #709, #710,
  and #712.

v25.1.2
-------

* #704: Fix errors when installing a zip sdist that contained
  files named with non-ascii characters on Windows would
  crash the install when it attempted to clean up the build.
* #646: MSVC compatibility - catch errors properly in
  RegistryInfo.lookup.
* #702: Prevent UnboundLocalError when initial working_set
  is empty.

v25.1.1
-------

* #686: Fix issue in sys.path ordering by pkg_resources when
  rewrite technique is "raw".
* #699: Fix typo in msvc support.

v25.1.0
-------

* #609: Setuptools will now try to download a distribution from
  the next possible download location if the first download fails.
  This means you can now specify multiple links as ``dependency_links``
  and all links will be tried until a working download link is encountered.

v25.0.2
-------

* #688: Fix AttributeError in setup.py when invoked not from
  the current directory.

v25.0.1
-------

* Cleanup of setup.py script.

* Fixed documentation builders by allowing setup.py
  to be imported without having bootstrapped the
  metadata.

* More style cleanup. See #677, #678, #679, #681, #685.

v25.0.0
-------

* #674: Default ``sys.path`` manipulation by easy-install.pth
  is now "raw", meaning that when writing easy-install.pth
  during any install operation, the ``sys.path`` will not be
  rewritten and will no longer give preference to easy_installed
  packages.

  To retain the old behavior when using any easy_install
  operation (including ``setup.py install`` when setuptools is
  present), set the environment variable:

    SETUPTOOLS_SYS_PATH_TECHNIQUE=rewrite

  This project hopes that that few if any environments find it
  necessary to retain the old behavior, and intends to drop
  support for it altogether in a future release. Please report
  any relevant concerns in the ticket for this change.

v24.3.1
-------

* #398: Fix shebang handling on Windows in script
  headers where spaces in ``sys.executable`` would
  produce an improperly-formatted shebang header,
  introduced in 12.0 with the fix for #188.

* #663, #670: More style updates.

v24.3.0
-------

* #516: Disable ``os.link`` to avoid hard linking
  in ``sdist.make_distribution``, avoiding errors on
  systems that support hard links but not on the
  file system in which the build is occurring.

v24.2.1
-------

* #667: Update Metadata-Version to 1.2 when
  ``python_requires`` is supplied.

v24.2.0
-------

* #631: Add support for ``python_requires`` keyword.

v24.1.1
-------

* More style updates. See #660, #661, #641.

v24.1.0
-------

* #659: ``setup.py`` now will fail fast and with a helpful
  error message when the necessary metadata is missing.
* More style updates. See #656, #635, #640,
  #644, #650, #652, and #655.

v24.0.3
-------

* Updated style in much of the codebase to match
  community expectations. See #632, #633, #634,
  #637, #639, #638, #642, #648.

v24.0.2
-------

* If MSVC++14 is needed ``setuptools.msvc`` now redirect
  user to Visual C++ Build Tools web page.

v24.0.1
-------

* #625 and #626: Fixes on ``setuptools.msvc`` mainly
  for Python 2 and Linux.

v24.0.0
-------

* Pull Request #174: Add more aggressive support for
  standalone Microsoft Visual C++ compilers in
  msvc9compiler patch.
  Particularly : Windows SDK 6.1 and 7.0
  (MSVC++ 9.0), Windows SDK 7.1 (MSVC++ 10.0),
  Visual C++ Build Tools 2015 (MSVC++14)
* Renamed ``setuptools.msvc9_support`` to
  ``setuptools.msvc``.

v23.2.1
-------

Re-release of v23.2.0, which was missing the intended
commits.

* #623: Remove used of deprecated 'U' flag when reading
  manifests.

v23.1.0
-------

* #619: Deprecated ``tag_svn_revision`` distribution
  option.

v23.0.0
-------

* #611: Removed ARM executables for CLI and GUI script
  launchers on Windows. If this was a feature you cared
  about, please comment in the ticket.
* #604: Removed docs building support. The project
  now relies on documentation hosted at
  https://setuptools.pypa.io/.

v22.0.5
-------

* #604: Restore repository for upload_docs command
  to restore publishing of docs during release.

v22.0.4
-------

* #589: Upload releases to pypi.io using the upload
  hostname and legacy path.

v22.0.3
-------

* #589: Releases are now uploaded to pypi.io (Warehouse)
  even when releases are made on Twine via Travis.

v22.0.2
-------

* #589: Releases are now uploaded to pypi.io (Warehouse).

v22.0.1
-------

* #190: On Python 2, if unicode is passed for packages to
  ``build_py`` command, it will be handled just as with
  text on Python 3.

v22.0.0
-------

Intended to be v21.3.0, but jaraco accidentally released as
a major bump.

* #598: Setuptools now lists itself first in the User-Agent
  for web requests, better following the guidelines in
  `RFC 7231
  <https://tools.ietf.org/html/rfc7231#section-5.5.3>`_.

v21.2.2
-------

* Minor fixes to changelog and docs.

v21.2.1
-------

* #261: Exclude directories when resolving globs in
  package_data.

v21.2.0
-------

* #539: In the easy_install get_site_dirs, honor all
  paths found in ``site.getsitepackages``.

v21.1.0
-------

* #572: In build_ext, now always import ``_CONFIG_VARS``
  from ``distutils`` rather than from ``sysconfig``
  to allow ``distutils.sysconfig.customize_compiler``
  configure the OS X compiler for ``-dynamiclib``.

v21.0.0
-------

* Removed ez_setup.py from Setuptools sdist. The
  bootstrap script will be maintained in its own
  branch and should be generally be retrieved from
  its canonical location at
  https://bootstrap.pypa.io/ez_setup.py.

v20.10.0
--------

* #553: egg_info section is now generated in a
  deterministic order, matching the order generated
  by earlier versions of Python. Except on Python 2.6,
  order is preserved when existing settings are present.
* #556: Update to Packaging 16.7, restoring support
  for deprecated ``python_implmentation`` marker.
* #555: Upload command now prompts for a password
  when uploading to PyPI (or other repository) if no
  password is present in .pypirc or in the keyring.

v20.9.0
-------

* #548: Update certify version to 2016.2.28
* #545: Safely handle deletion of non-zip eggs in rotate
  command.

v20.8.1
-------

* Issue #544: Fix issue with extra environment marker
  processing in WorkingSet due to refactor in v20.7.0.

v20.8.0
-------

* Issue #543: Re-release so that latest release doesn't
  cause déjà vu with distribute and setuptools 0.7 in
  older environments.

v20.7.0
-------

* Refactored extra environment marker processing
  in WorkingSet.
* Issue #533: Fixed intermittent test failures.
* Issue #536: In msvc9_support, trap additional exceptions
  that might occur when importing
  ``distutils.msvc9compiler`` in mingw environments.
* Issue #537: Provide better context when package
  metadata fails to decode in UTF-8.

v20.6.8
-------

* Issue #523: Restored support for environment markers,
  now honoring 'extra' environment markers.

v20.6.7
-------

* Issue #523: Disabled support for environment markers
  introduced in v20.5.

v20.6.6
-------

* Issue #503: Restore support for PEP 345 environment
  markers by updating to Packaging 16.6.

v20.6.0
-------

* New release process that relies on
  `bumpversion <https://github.com/peritus/bumpversion>`_
  and Travis CI for continuous deployment.
* Project versioning semantics now follow
  `semver <https://semver.org>`_ precisely.
  The 'v' prefix on version numbers now also allows
  version numbers to be referenced in the changelog,
  e.g. http://setuptools.pypa.io/en/latest/history.html#v20-6-0.

20.5
----

* BB Pull Request #185, #470: Add support for environment markers
  in requirements in install_requires, setup_requires,
  tests_require as well as adding a test for the existing
  extra_requires machinery.

20.4
----

* Issue #422: Moved hosting to
  `Github <https://github.com/pypa/setuptools>`_
  from `Bitbucket <https://bitbucket.org/pypa/setuptools>`_.
  Issues have been migrated, though all issues and comments
  are attributed to bb-migration. So if you have a particular
  issue or issues to which you've been subscribed, you will
  want to "watch" the equivalent issue in Github.
  The Bitbucket project will be retained for the indefinite
  future, but Github now hosts the canonical project repository.

20.3.1
------

* Issue #519: Remove import hook when reloading the
  ``pkg_resources`` module.
* BB Pull Request #184: Update documentation in ``pkg_resources``
  around new ``Requirement`` implementation.

20.3
----

* BB Pull Request #179: ``pkg_resources.Requirement`` objects are
  now a subclass of ``packaging.requirements.Requirement``,
  allowing any environment markers and url (if any) to be
  affiliated with the requirement
* BB Pull Request #179: Restore use of RequirementParseError
  exception unintentionally dropped in 20.2.

20.2.2
------

* Issue #502: Correct regression in parsing of multiple
  version specifiers separated by commas and spaces.

20.2.1
------

* Issue #499: Restore compatibility for legacy versions
  by bumping to packaging 16.4.

20.2
----

* Changelog now includes release dates and links to PEPs.
* BB Pull Request #173: Replace dual PEP 345 _markerlib implementation
  and PEP 426 implementation of environment marker support from
  packaging 16.1 and PEP 508. Fixes Issue #122.
  See also BB Pull Request #175, BB Pull Request #168, and
  BB Pull Request #164. Additionally:

   - ``Requirement.parse`` no longer retains the order of extras.
   - ``parse_requirements`` now requires that all versions be
     PEP-440 compliant, as revealed in #499. Packages released
     with invalid local versions should be re-released using
     the proper local version syntax, e.g. ``mypkg-1.0+myorg.1``.

20.1.1
------

* Update ``upload_docs`` command to also honor keyring
  for password resolution.

20.1
----

* Added support for using passwords from keyring in the upload
  command. See `the upload docs
  <https://setuptools.pypa.io/en/latest/setuptools.html#upload-upload-source-and-or-egg-distributions-to-pypi>`_
  for details.

20.0
----

* Issue #118: Once again omit the package metadata (egg-info)
  from the list of outputs in ``--record``. This version of setuptools
  can no longer be used to upgrade pip earlier than 6.0.

19.7
----

* Off-project PR: `0dcee79 <https://github.com/pypa/setuptools/commit/0dcee791dfdcfacddaaec79b29f30a347a147413>`_ and `f9bd9b9 <https://github.com/pypa/setuptools/commit/f9bd9b9f5df54ef5a0bf8d16c3a889ab8c640580>`_
  For FreeBSD, also `honor root certificates from ca_root_nss <https://github.com/pypa/setuptools/commit/3ae46c30225eb46e1f5aada1a19e88b79f04dc72>`_.

19.6.2
------

* Issue #491: Correct regression incurred in 19.4 where
  a double-namespace package installed using pip would
  cause a TypeError.

19.6.1
------

* Restore compatibility for PyPy 3 compatibility lost in
  19.4.1 addressing Issue #487.
* ``setuptools.launch`` shim now loads scripts in a new
  namespace, avoiding getting relative imports from
  the setuptools package on Python 2.

19.6
----

* Added a new entry script ``setuptools.launch``,
  implementing the shim found in
  ``pip.util.setuptools_build``. Use this command to launch
  distutils-only packages under setuptools in the same way that
  pip does, causing the setuptools monkeypatching of distutils
  to be invoked prior to invoking a script. Useful for debugging
  or otherwise installing a distutils-only package under
  setuptools when pip isn't available or otherwise does not
  expose the desired functionality. For example::

    $ python -m setuptools.launch setup.py develop

* Issue #488: Fix dual manifestation of Extension class in
  extension packages installed as dependencies when Cython
  is present.

19.5
----

* Issue #486: Correct TypeError when getfilesystemencoding
  returns None.
* Issue #139: Clarified the license as MIT.
* BB Pull Request #169: Removed special handling of command
  spec in scripts for Jython.

19.4.1
------

* Issue #487: Use direct invocation of ``importlib.machinery``
  in ``pkg_resources`` to avoid missing detection on relevant
  platforms.

19.4
----

* Issue #341: Correct error in path handling of package data
  files in ``build_py`` command when package is empty.
* Distribute #323, Issue #141, Issue #207, and
  BB Pull Request #167: Another implementation of
  ``pkg_resources.WorkingSet`` and ``pkg_resources.Distribution``
  that supports replacing an extant package with a new one,
  allowing for setup_requires dependencies to supersede installed
  packages for the session.

19.3
----

* Issue #229: Implement new technique for readily incorporating
  dependencies conditionally from vendored copies or primary
  locations. Adds a new dependency on six.

19.2
----

* BB Pull Request #163: Add get_command_list method to Distribution.
* BB Pull Request #162: Add missing whitespace to multiline string
  literals.

19.1.1
------

* Issue #476: Cast version to string (using default encoding)
  to avoid creating Unicode types on Python 2 clients.
* Issue #477: In Powershell downloader, use explicit rendering
  of strings, rather than rely on ``repr``, which can be
  incorrect (especially on Python 2).

19.1
----

* Issue #215: The bootstrap script ``ez_setup.py`` now
  automatically detects
  the latest version of setuptools (using PyPI JSON API) rather
  than hard-coding a particular value.
* Issue #475: Fix incorrect usage in _translate_metadata2.

19.0
----

* Issue #442: Use RawConfigParser for parsing .pypirc file.
  Interpolated values are no longer honored in .pypirc files.

18.8.1
------

* Issue #440: Prevent infinite recursion when a SandboxViolation
  or other UnpickleableException occurs in a sandbox context
  with setuptools hidden. Fixes regression introduced in Setuptools
  12.0.

18.8
----

* Deprecated ``egg_info.get_pkg_info_revision``.
* Issue #471: Don't rely on repr for an HTML attribute value in
  package_index.
* Issue #419: Avoid errors in FileMetadata when the metadata directory
  is broken.
* Issue #472: Remove deprecated use of 'U' in mode parameter
  when opening files.

18.7.1
------

* Issue #469: Refactored logic for Issue #419 fix to re-use metadata
  loading from Provider.

18.7
----

* Update dependency on certify.
* BB Pull Request #160: Improve detection of gui script in
  ``easy_install._adjust_header``.
* Made ``test.test_args`` a non-data property; alternate fix
  for the issue reported in BB Pull Request #155.
* Issue #453: In ``ez_setup`` bootstrap module, unload all
  ``pkg_resources`` modules following download.
* BB Pull Request #158: Honor PEP-488 when excluding
  files for namespace packages.
* Issue #419 and BB Pull Request #144: Add experimental support for
  reading the version info from distutils-installed metadata rather
  than using the version in the filename.

18.6.1
------

* Issue #464: Correct regression in invocation of superclass on old-style
  class on Python 2.

18.6
----

* Issue #439: When installing entry_point scripts under development,
  omit the version number of the package, allowing any version of the
  package to be used.

18.5
----

* In preparation for dropping support for Python 3.2, a warning is
  now logged when pkg_resources is imported on Python 3.2 or earlier
  Python 3 versions.
* `Add support for python_platform_implementation environment marker
  <https://github.com/pypa/setuptools/commit/94416707fd59a65f4a8f7f70541d6b3fc018b626>`_.
* `Fix dictionary mutation during iteration
  <https://github.com/pypa/setuptools/commit/57ebfa41e0f96b97e599ecd931b7ae8a143e096e>`_.

18.4
----

* Issue #446: Test command now always invokes unittest, even
  if no test suite is supplied.

18.3.2
------

* Correct another regression in setuptools.findall
  where the fix for Python #12885 was lost.

18.3.1
------

* Issue #425: Correct regression in setuptools.findall.

18.3
----

* BB Pull Request #135: Setuptools now allows disabling of
  the manipulation of the sys.path
  during the processing of the easy-install.pth file. To do so, set
  the environment variable ``SETUPTOOLS_SYS_PATH_TECHNIQUE`` to
  anything but "rewrite" (consider "raw"). During any install operation
  with manipulation disabled, setuptools packages will be appended to
  sys.path naturally.

  Future versions may change the default behavior to disable
  manipulation. If so, the default behavior can be retained by setting
  the variable to "rewrite".

* Issue #257: ``easy_install --version`` now shows more detail
  about the installation location and Python version.

* Refactor setuptools.findall in preparation for re-submission
  back to distutils.

18.2
----

* Issue #412: More efficient directory search in ``find_packages``.

18.1
----

* Upgrade to vendored packaging 15.3.

18.0.1
------

* Issue #401: Fix failure in test suite.

18.0
----

* Dropped support for builds with Pyrex. Only Cython is supported.
* Issue #288: Detect Cython later in the build process, after
  ``setup_requires`` dependencies are resolved.
  Projects backed by Cython can now be readily built
  with a ``setup_requires`` dependency. For example::

    ext = setuptools.Extension('mylib', ['src/CythonStuff.pyx', 'src/CStuff.c'])
    setuptools.setup(
        ...
        ext_modules=[ext],
        setup_requires=['cython'],
    )

  For compatibility with older versions of setuptools, packagers should
  still include ``src/CythonMod.c`` in the source distributions or
  require that Cython be present before building source distributions.
  However, for systems with this build of setuptools, Cython will be
  downloaded on demand.
* Issue #396: Fixed test failure on OS X.
* BB Pull Request #136: Remove excessive quoting from shebang headers
  for Jython.

17.1.1
------

* Backed out unintended changes to pkg_resources, restoring removal of
  deprecated imp module (`ref
  <https://bitbucket.org/pypa/setuptools/commits/f572ec9563d647fa8d4ffc534f2af8070ea07a8b#comment-1881283>`_).

17.1
----

* Issue #380: Add support for range operators on environment
  marker evaluation.

17.0
----

* Issue #378: Do not use internal importlib._bootstrap module.
* Issue #390: Disallow console scripts with path separators in
  the name. Removes unintended functionality and brings behavior
  into parity with pip.

16.0
----

* BB Pull Request #130: Better error messages for errors in
  parsed requirements.
* BB Pull Request #133: Removed ``setuptools.tests`` from the
  installed packages.
* BB Pull Request #129: Address deprecation warning due to usage
  of imp module.

15.2
----

* Issue #373: Provisionally expose
  ``pkg_resources._initialize_master_working_set``, allowing for
  imperative re-initialization of the master working set.

15.1
----

* Updated to Packaging 15.1 to address Packaging #28.
* Fix ``setuptools.sandbox._execfile()`` with Python 3.1.

15.0
----

* BB Pull Request #126: DistributionNotFound message now lists the package or
  packages that required it. E.g.::

      pkg_resources.DistributionNotFound: The 'colorama>=0.3.1' distribution was not found and is required by smlib.log.

  Note that zc.buildout once dependended on the string rendering of this
  message to determine the package that was not found. This expectation
  has since been changed, but older versions of buildout may experience
  problems. See Buildout #242 for details.

14.3.1
------

* Issue #307: Removed PEP-440 warning during parsing of versions
  in ``pkg_resources.Distribution``.
* Issue #364: Replace deprecated usage with recommended usage of
  ``EntryPoint.load``.

14.3
----

* Issue #254: When creating temporary egg cache on Unix, use mode 755
  for creating the directory to avoid the subsequent warning if
  the directory is group writable.

14.2
----

* Issue #137: Update ``Distribution.hashcmp`` so that Distributions with
  None for pyversion or platform can be compared against Distributions
  defining those attributes.

14.1.1
------

* Issue #360: Removed undesirable behavior from test runs, preventing
  write tests and installation to system site packages.

14.1
----

* BB Pull Request #125: Add ``__ne__`` to Requirement class.
* Various refactoring of easy_install.

14.0
----

* Bootstrap script now accepts ``--to-dir`` to customize save directory or
  allow for re-use of existing repository of setuptools versions. See
  BB Pull Request #112 for background.
* Issue #285: ``easy_install`` no longer will default to installing
  packages to the "user site packages" directory if it is itself installed
  there. Instead, the user must pass ``--user`` in all cases to install
  packages to the user site packages.
  This behavior now matches that of "pip install". To configure
  an environment to always install to the user site packages, consider
  using the "install-dir" and "scripts-dir" parameters to easy_install
  through an appropriate distutils config file.

13.0.2
------

* Issue #359: Include pytest.ini in the sdist so invocation of py.test on the
  sdist honors the pytest configuration.

13.0.1
------

Re-release of 13.0. Intermittent connectivity issues caused the release
process to fail and PyPI uploads no longer accept files for 13.0.

13.0
----

* Issue #356: Back out BB Pull Request #119 as it requires Setuptools 10 or later
  as the source during an upgrade.
* Removed build_py class from setup.py. According to 892f439d216e, this
  functionality was added to support upgrades from old Distribute versions,
  0.6.5 and 0.6.6.

12.4
----

* BB Pull Request #119: Restore writing of ``setup_requires`` to metadata
  (previously added in 8.4 and removed in 9.0).

12.3
----

* Documentation is now linked using the rst.linker package.
* Fix ``setuptools.command.easy_install.extract_wininst_cfg()``
  with Python 2.6 and 2.7.
* Issue #354. Added documentation on building setuptools
  documentation.

12.2
----

* Issue #345: Unload all modules under pkg_resources during
  ``ez_setup.use_setuptools()``.
* Issue #336: Removed deprecation from ``ez_setup.use_setuptools``,
  as it is clearly still used by buildout's bootstrap. ``ez_setup``
  remains deprecated for use by individual packages.
* Simplified implementation of ``ez_setup.use_setuptools``.

12.1
----

* BB Pull Request #118: Soften warning for non-normalized versions in
  Distribution.

12.0.5
------

* Issue #339: Correct Attribute reference in ``cant_write_to_target``.
* Issue #336: Deprecated ``ez_setup.use_setuptools``.

12.0.4
------

* Issue #335: Fix script header generation on Windows.

12.0.3
------

* Fixed incorrect class attribute in ``install_scripts``. Tests would be nice.

12.0.2
------

* Issue #331: Fixed ``install_scripts`` command on Windows systems corrupting
  the header.

12.0.1
------

* Restore ``setuptools.command.easy_install.sys_executable`` for pbr
  compatibility. For the future, tools should construct a CommandSpec
  explicitly.

12.0
----

* Issue #188: Setuptools now support multiple entities in the value for
  ``build.executable``, such that an executable of "/usr/bin/env my-python" may
  be specified. This means that systems with a specified executable whose name
  has spaces in the path must be updated to escape or quote that value.
* Deprecated ``easy_install.ScriptWriter.get_writer``, replaced by ``.best()``
  with slightly different semantics (no force_windows flag).

11.3.1
------

* Issue #327: Formalize and restore support for any printable character in an
  entry point name.

11.3
----

* Expose ``EntryPoint.resolve`` in place of EntryPoint._load, implementing the
  simple, non-requiring load. Deprecated all uses of ``EntryPoint._load``
  except for calling with no parameters, which is just a shortcut for
  ``ep.require(); ep.resolve();``.

  Apps currently invoking ``ep.load(require=False)`` should instead do the
  following if wanting to avoid the deprecating warning::

    getattr(ep, "resolve", lambda: ep.load(require=False))()

11.2
----

* Pip #2326: Report deprecation warning at stacklevel 2 for easier diagnosis.

11.1
----

* Issue #281: Since Setuptools 6.1 (Issue #268), a ValueError would be raised
  in certain cases where VersionConflict was raised with two arguments, which
  occurred in ``pkg_resources.WorkingSet.find``. This release adds support
  for indicating the dependent packages while maintaining support for
  a VersionConflict when no dependent package context is known. New unit tests
  now capture the expected interface.

11.0
----

* Interop #3: Upgrade to Packaging 15.0; updates to PEP 440 so that >1.7 does
  not exclude 1.7.1 but does exclude 1.7.0 and 1.7.0.post1.

10.2.1
------

* Issue #323: Fix regression in entry point name parsing.

10.2
----

* Deprecated use of EntryPoint.load(require=False). Passing a boolean to a
  function to select behavior is an anti-pattern. Instead use
  ``Entrypoint._load()``.
* Substantial refactoring of all unit tests. Tests are now much leaner and
  re-use a lot of fixtures and contexts for better clarity of purpose.

10.1
----

* Issue #320: Added a compatibility implementation of
  ``sdist._default_revctrl``
  so that systems relying on that interface do not fail (namely, Ubuntu 12.04
  and similar Debian releases).

10.0.1
------

* Issue #319: Fixed issue installing pure distutils packages.

10.0
----

* Issue #313: Removed built-in support for subversion. Projects wishing to
  retain support for subversion will need to use a third party library. The
  extant implementation is being ported to `setuptools_svn
  <https://pypi.org/project/setuptools_svn/>`_.
* Issue #315: Updated setuptools to hide its own loaded modules during
  installation of another package. This change will enable setuptools to
  upgrade (or downgrade) itself even when its own metadata and implementation
  change.

9.1
---

* Prefer vendored packaging library `as recommended
  <https://github.com/pypa/setuptools/commit/170657b68f4b92e7e1bf82f5e19a831f5744af67>`_.

9.0.1
-----

* Issue #312: Restored presence of pkg_resources API tests (doctest) to sdist.

9.0
---

* Issue #314: Disabled support for ``setup_requires`` metadata to avoid issue
  where Setuptools was unable to upgrade over earlier versions.

8.4
---

* BB Pull Request #106: Now write ``setup_requires`` metadata.

8.3
---

* Issue #311: Decoupled pkg_resources from setuptools once again.
  ``pkg_resources`` is now a package instead of a module.

8.2.1
-----

* Issue #306: Suppress warnings about Version format except in select scenarios
  (such as installation).

8.2
---

* BB Pull Request #85: Search egg-base when adding egg-info to manifest.

8.1
---

* Upgrade ``packaging`` to 14.5, giving preference to "rc" as designator for
  release candidates over "c".
* PEP-440 warnings are now raised as their own class,
  ``pkg_resources.PEP440Warning``, instead of RuntimeWarning.
* Disabled warnings on empty versions.

8.0.4
-----

* Upgrade ``packaging`` to 14.4, fixing an error where there is a
  different result for if 2.0.5 is contained within >2.0dev and >2.0.dev even
  though normalization rules should have made them equal.
* Issue #296: Add warning when a version is parsed as legacy. This warning will
  make it easier for developers to recognize deprecated version numbers.

8.0.3
-----

* Issue #296: Restored support for ``__hash__`` on parse_version results.

8.0.2
-----

* Issue #296: Restored support for ``__getitem__`` and sort operations on
  parse_version result.

8.0.1
-----

* Issue #296: Restore support for iteration over parse_version result, but
  deprecated that usage with a warning. Fixes failure with buildout.

8.0
---

* Implement PEP 440 within
  pkg_resources and setuptools. This change
  deprecates some version numbers such that they will no longer be installable
  without using the ``===`` escape hatch. See `the changes to test_resources
  <https://bitbucket.org/pypa/setuptools/commits/dcd552da643c4448056de84c73d56da6d70769d5#chg-setuptools/tests/test_resources.py>`_
  for specific examples of version numbers and specifiers that are no longer
  supported. Setuptools now "vendors" the `packaging
  <https://github.com/pypa/packaging>`_ library.

7.0
---

* Issue #80, Issue #209: Eggs that are downloaded for ``setup_requires``,
  ``test_requires``, etc. are now placed in a ``./.eggs`` directory instead of
  directly in the current directory. This choice of location means the files
  can be readily managed (removed, ignored). Additionally,
  later phases or invocations of setuptools will not detect the package as
  already installed and ignore it for permanent install (See #209).

  This change is indicated as backward-incompatible as installations that
  depend on the installation in the current directory will need to account for
  the new location. Systems that ignore ``*.egg`` will probably need to be
  adapted to ignore ``.eggs``. The files will need to be manually moved or
  will be retrieved again. Most use cases will require no attention.

6.1
---

* Issue #268: When resolving package versions, a VersionConflict now reports
  which package previously required the conflicting version.

6.0.2
-----

* Issue #262: Fixed regression in pip install due to egg-info directories
  being omitted. Re-opens Issue #118.

6.0.1
-----

* Issue #259: Fixed regression with namespace package handling on ``single
  version, externally managed`` installs.

6.0
---

* Issue #100: When building a distribution, Setuptools will no longer match
  default files using platform-dependent case sensitivity, but rather will
  only match the files if their case matches exactly. As a result, on Windows
  and other case-insensitive file systems, files with names such as
  'readme.txt' or 'README.TXT' will be omitted from the distribution and a
  warning will be issued indicating that 'README.txt' was not found. Other
  filenames affected are:

    - README.rst
    - README
    - setup.cfg
    - setup.py (or the script name)
    - test/test*.py

  Any users producing distributions with filenames that match those above
  case-insensitively, but not case-sensitively, should rename those files in
  their repository for better portability.
* BB Pull Request #72: When using ``single_version_externally_managed``, the
  exclusion list now includes Python 3.2 ``__pycache__`` entries.
* BB Pull Request #76 and BB Pull Request #78: lines in top_level.txt are now
  ordered deterministically.
* Issue #118: The egg-info directory is now no longer included in the list
  of outputs.
* Issue #258: Setuptools now patches distutils msvc9compiler to
  recognize the specially-packaged compiler package for easy extension module
  support on Python 2.6, 2.7, and 3.2.

5.8
---

* Issue #237: ``pkg_resources`` now uses explicit detection of Python 2 vs.
  Python 3, supporting environments where builtins have been patched to make
  Python 3 look more like Python 2.

5.7
---

* Issue #240: Based on real-world performance measures against 5.4, zip
  manifests are now cached in all circumstances. The
  ``PKG_RESOURCES_CACHE_ZIP_MANIFESTS`` environment variable is no longer
  relevant. The observed "memory increase" referenced in the 5.4 release
  notes and detailed in Issue #154 was likely not an increase over the status
  quo, but rather only an increase over not storing the zip info at all.

5.6
---

* Issue #242: Use absolute imports in svn_utils to avoid issues if the
  installing package adds an xml module to the path.

5.5.1
-----

* Issue #239: Fix typo in 5.5 such that fix did not take.

5.5
---

* Issue #239: Setuptools now includes the setup_requires directive on
  Distribution objects and validates the syntax just like install_requires
  and tests_require directives.

5.4.2
-----

* Issue #236: Corrected regression in execfile implementation for Python 2.6.

5.4.1
-----

* Python #7776: (ssl_support) Correct usage of host for validation when
  tunneling for HTTPS.

5.4
---

* Issue #154: ``pkg_resources`` will now cache the zip manifests rather than
  re-processing the same file from disk multiple times, but only if the
  environment variable ``PKG_RESOURCES_CACHE_ZIP_MANIFESTS`` is set. Clients
  that package many modules in the same zip file will see some improvement
  in startup time by enabling this feature. This feature is not enabled by
  default because it causes a substantial increase in memory usage.

5.3
---

* Issue #185: Make svn tagging work on the new style SVN metadata.
  Thanks cazabon!
* Prune revision control directories (e.g .svn) from base path
  as well as sub-directories.

5.2
---

* Added a `Developer Guide
  <https://setuptools.pypa.io/en/latest/developer-guide.html>`_ to the official
  documentation.
* Some code refactoring and cleanup was done with no intended behavioral
  changes.
* During install_egg_info, the generated lines for namespace package .pth
  files are now processed even during a dry run.

5.1
---

* Issue #202: Implemented more robust cache invalidation for the ZipImporter,
  building on the work in Issue #168. Special thanks to Jurko Gospodnetic and
  PJE.

5.0.2
-----

* Issue #220: Restored script templates.

5.0.1
-----

* Renamed script templates to end with .tmpl now that they no longer need
  to be processed by 2to3. Fixes spurious syntax errors during build/install.

5.0
---

* Issue #218: Re-release of 3.8.1 to signal that it supersedes 4.x.
* Incidentally, script templates were updated not to include the triple-quote
  escaping.

3.7.1 and 3.8.1 and 4.0.1
-------------------------

* Issue #213: Use legacy StringIO behavior for compatibility under pbr.
* Issue #218: Setuptools 3.8.1 superseded 4.0.1, and 4.x was removed
  from the available versions to install.

4.0
---

* Issue #210: ``setup.py develop`` now copies scripts in binary mode rather
  than text mode, matching the behavior of the ``install`` command.

3.8
---

* Extend Issue #197 workaround to include all Python 3 versions prior to
  3.2.2.

3.7
---

* Issue #193: Improved handling of Unicode filenames when building manifests.

3.6
---

* Issue #203: Honor proxy settings for Powershell downloader in the bootstrap
  routine.

3.5.2
-----

* Issue #168: More robust handling of replaced zip files and stale caches.
  Fixes ZipImportError complaining about a 'bad local header'.

3.5.1
-----

* Issue #199: Restored ``install._install`` for compatibility with earlier
  NumPy versions.

3.5
---

* Issue #195: Follow symbolic links in find_packages (restoring behavior
  broken in 3.4).
* Issue #197: On Python 3.1, PKG-INFO is now saved in a UTF-8 encoding instead
  of ``sys.getpreferredencoding`` to match the behavior on Python 2.6-3.4.
* Issue #192: Preferred bootstrap location is now
  https://bootstrap.pypa.io/ez_setup.py (mirrored from former location).

3.4.4
-----

* Issue #184: Correct failure where find_package over-matched packages
  when directory traversal isn't short-circuited.

3.4.3
-----

* Issue #183: Really fix test command with Python 3.1.

3.4.2
-----

* Issue #183: Fix additional regression in test command on Python 3.1.

3.4.1
-----

* Issue #180: Fix regression in test command not caught by py.test-run tests.

3.4
---

* Issue #176: Add parameter to the test command to support a custom test
  runner: --test-runner or -r.
* Issue #177: Now assume most common invocation to install command on
  platforms/environments without stack support (issuing a warning). Setuptools
  now installs naturally on IronPython. Behavior on CPython should be
  unchanged.

3.3
---

* Add ``include`` parameter to ``setuptools.find_packages()``.

3.2
---

* BB Pull Request #39: Add support for C++ targets from Cython ``.pyx`` files.
* Issue #162: Update dependency on certifi to 1.0.1.
* Issue #164: Update dependency on wincertstore to 0.2.

3.1
---

* Issue #161: Restore Features functionality to allow backward compatibility
  (for Features) until the uses of that functionality is sufficiently removed.

3.0.2
-----

* Correct typo in previous bugfix.

3.0.1
-----

* Issue #157: Restore support for Python 2.6 in bootstrap script where
  ``zipfile.ZipFile`` does not yet have support for context managers.

3.0
---

* Issue #125: Prevent Subversion support from creating a ~/.subversion
  directory just for checking the presence of a Subversion repository.
* Issue #12: Namespace packages are now imported lazily. That is, the mere
  declaration of a namespace package in an egg on ``sys.path`` no longer
  causes it to be imported when ``pkg_resources`` is imported. Note that this
  change means that all of a namespace package's ``__init__.py`` files must
  include a ``declare_namespace()`` call in order to ensure that they will be
  handled properly at runtime. In 2.x it was possible to get away without
  including the declaration, but only at the cost of forcing namespace
  packages to be imported early, which 3.0 no longer does.
* Issue #148: When building (bdist_egg), setuptools no longer adds
  ``__init__.py`` files to namespace packages. Any packages that rely on this
  behavior will need to create ``__init__.py`` files and include the
  ``declare_namespace()``.
* Issue #7: Setuptools itself is now distributed as a zip archive in addition to
  tar archive. ez_setup.py now uses zip archive. This approach avoids the potential
  security vulnerabilities presented by use of tar archives in ez_setup.py.
  It also leverages the security features added to ZipFile.extract in Python 2.7.4.
* Issue #65: Removed deprecated Features functionality.
* BB Pull Request #28: Remove backport of ``_bytecode_filenames`` which is
  available in Python 2.6 and later, but also has better compatibility with
  Python 3 environments.
* Issue #156: Fix spelling of __PYVENV_LAUNCHER__ variable.

2.2
---

* Issue #141: Restored fix for allowing setup_requires dependencies to
  override installed dependencies during setup.
* Issue #128: Fixed issue where only the first dependency link was honored
  in a distribution where multiple dependency links were supplied.

2.1.2
-----

* Issue #144: Read long_description using codecs module to avoid errors
  installing on systems where LANG=C.

2.1.1
-----

* Issue #139: Fix regression in re_finder for CVS repos (and maybe Git repos
  as well).

2.1
---

* Issue #129: Suppress inspection of ``*.whl`` files when searching for files
  in a zip-imported file.
* Issue #131: Fix RuntimeError when constructing an egg fetcher.

2.0.2
-----

* Fix NameError during installation with Python implementations (e.g. Jython)
  not containing parser module.
* Fix NameError in ``sdist:re_finder``.

2.0.1
-----

* Issue #124: Fixed error in list detection in upload_docs.

2.0
---

* Issue #121: Exempt lib2to3 pickled grammars from DirectorySandbox.
* Issue #41: Dropped support for Python 2.4 and Python 2.5. Clients requiring
  setuptools for those versions of Python should use setuptools 1.x.
* Removed ``setuptools.command.easy_install.HAS_USER_SITE``. Clients
  expecting this boolean variable should use ``site.ENABLE_USER_SITE``
  instead.
* Removed ``pkg_resources.ImpWrapper``. Clients that expected this class
  should use ``pkgutil.ImpImporter`` instead.

1.4.2
-----

* Issue #116: Correct TypeError when reading a local package index on Python
  3.

1.4.1
-----

* Issue #114: Use ``sys.getfilesystemencoding`` for decoding config in
  ``bdist_wininst`` distributions.

* Issue #105 and Issue #113: Establish a more robust technique for
  determining the terminal encoding::

    1. Try ``getpreferredencoding``
    2. If that returns US_ASCII or None, try the encoding from
       ``getdefaultlocale``. If that encoding was a "fallback" because Python
       could not figure it out from the environment or OS, encoding remains
       unresolved.
    3. If the encoding is resolved, then make sure Python actually implements
       the encoding.
    4. On the event of an error or unknown codec, revert to fallbacks
       (UTF-8 on Darwin, ASCII on everything else).
    5. On the encoding is 'mac-roman' on Darwin, use UTF-8 as 'mac-roman' was
       a bug on older Python releases.

    On a side note, it would seem that the encoding only matters for when SVN
    does not yet support ``--xml`` and when getting repository and svn version
    numbers. The ``--xml`` technique should yield UTF-8 according to some
    messages on the SVN mailing lists. So if the version numbers are always
    7-bit ASCII clean, it may be best to only support the file parsing methods
    for legacy SVN releases and support for SVN without the subprocess command
    would simple go away as support for the older SVNs does.

1.4
---

* Issue #27: ``easy_install`` will now use credentials from .pypirc if
  present for connecting to the package index.
* BB Pull Request #21: Omit unwanted newlines in ``package_index._encode_auth``
  when the username/password pair length indicates wrapping.

1.3.2
-----

* Issue #99: Fix filename encoding issues in SVN support.

1.3.1
-----

* Remove exuberant warning in SVN support when SVN is not used.

1.3
---

* Address security vulnerability in SSL match_hostname check as reported in
  Python #17997.
* Prefer `backports.ssl_match_hostname
  <https://pypi.org/project/backports.ssl_match_hostname/>`_ for backport
  implementation if present.
* Correct NameError in ``ssl_support`` module (``socket.error``).

1.2
---

* Issue #26: Add support for SVN 1.7. Special thanks to Philip Thiem for the
  contribution.
* Issue #93: Wheels are now distributed with every release. Note that as
  reported in Issue #108, as of Pip 1.4, scripts aren't installed properly
  from wheels. Therefore, if using Pip to install setuptools from a wheel,
  the ``easy_install`` command will not be available.
* Setuptools "natural" launcher support, introduced in 1.0, is now officially
  supported.

1.1.7
-----

* Fixed behavior of NameError handling in 'script template (dev).py' (script
  launcher for 'develop' installs).
* ``ez_setup.py`` now ensures partial downloads are cleaned up following
  a failed download.
* Distribute #363 and Issue #55: Skip an sdist test that fails on locales
  other than UTF-8.

1.1.6
-----

* Distribute #349: ``sandbox.execfile`` now opens the target file in binary
  mode, thus honoring a BOM in the file when compiled.

1.1.5
-----

* Issue #69: Second attempt at fix (logic was reversed).

1.1.4
-----

* Issue #77: Fix error in upload command (Python 2.4).

1.1.3
-----

* Fix NameError in previous patch.

1.1.2
-----

* Issue #69: Correct issue where 404 errors are returned for URLs with
  fragments in them (such as #egg=).

1.1.1
-----

* Issue #75: Add ``--insecure`` option to ez_setup.py to accommodate
  environments where a trusted SSL connection cannot be validated.
* Issue #76: Fix AttributeError in upload command with Python 2.4.

1.1
---

* Issue #71 (Distribute #333): EasyInstall now puts less emphasis on the
  condition when a host is blocked via ``--allow-hosts``.
* Issue #72: Restored Python 2.4 compatibility in ``ez_setup.py``.

1.0
---

* Issue #60: On Windows, Setuptools supports deferring to another launcher,
  such as Vinay Sajip's `pylauncher <https://bitbucket.org/pypa/pylauncher>`_
  (included with Python 3.3) to launch console and GUI scripts and not install
  its own launcher executables. This experimental functionality is currently
  only enabled if  the ``SETUPTOOLS_LAUNCHER`` environment variable is set to
  "natural". In the future, this behavior may become default, but only after
  it has matured and seen substantial adoption. The ``SETUPTOOLS_LAUNCHER``
  also accepts "executable" to force the default behavior of creating launcher
  executables.
* Issue #63: Bootstrap script (ez_setup.py) now prefers Powershell, curl, or
  wget for retrieving the Setuptools tarball for improved security of the
  install. The script will still fall back to a simple ``urlopen`` on
  platforms that do not have these tools.
* Issue #65: Deprecated the ``Features`` functionality.
* Issue #52: In ``VerifyingHTTPSConn``, handle a tunnelled (proxied)
  connection.

Backward-Incompatible Changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This release includes a couple of backward-incompatible changes, but most if
not all users will find 1.0 a drop-in replacement for 0.9.

* Issue #50: Normalized API of environment marker support. Specifically,
  removed line number and filename from SyntaxErrors when returned from
  ``pkg_resources.invalid_marker``. Any clients depending on the specific
  string representation of exceptions returned by that function may need to
  be updated to account for this change.
* Issue #50: SyntaxErrors generated by ``pkg_resources.invalid_marker`` are
  normalized for cross-implementation consistency.
* Removed ``--ignore-conflicts-at-my-risk`` and ``--delete-conflicting``
  options to easy_install. These options have been deprecated since 0.6a11.

0.9.8
-----

* Issue #53: Fix NameErrors in ``_vcs_split_rev_from_url``.

0.9.7
-----

* Issue #49: Correct AttributeError on PyPy where a hashlib.HASH object does
  not have a ``.name`` attribute.
* Issue #34: Documentation now refers to bootstrap script in code repository
  referenced by bookmark.
* Add underscore-separated keys to environment markers (markerlib).

0.9.6
-----

* Issue #44: Test failure on Python 2.4 when MD5 hash doesn't have a ``.name``
  attribute.

0.9.5
-----

* Python #17980: Fix security vulnerability in SSL certificate validation.

0.9.4
-----

* Issue #43: Fix issue (introduced in 0.9.1) with version resolution when
  upgrading over other releases of Setuptools.

0.9.3
-----

* Issue #42: Fix new ``AttributeError`` introduced in last fix.

0.9.2
-----

* Issue #42: Fix regression where blank checksums would trigger an
  ``AttributeError``.

0.9.1
-----

* Distribute #386: Allow other positional and keyword arguments to os.open.
* Corrected dependency on certifi mis-referenced in 0.9.

0.9
---

* ``package_index`` now validates hashes other than MD5 in download links.

0.8
---

* Code base now runs on Python 2.4 - Python 3.3 without Python 2to3
  conversion.

0.7.8
-----

* Distribute #375: Yet another fix for yet another regression.

0.7.7
-----

* Distribute #375: Repair AttributeError created in last release (redo).
* Issue #30: Added test for get_cache_path.

0.7.6
-----

* Distribute #375: Repair AttributeError created in last release.

0.7.5
-----

* Issue #21: Restore Python 2.4 compatibility in ``test_easy_install``.
* Distribute #375: Merged additional warning from Distribute 0.6.46.
* Now honor the environment variable
  ``SETUPTOOLS_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT`` in addition to the now
  deprecated ``DISTRIBUTE_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT``.

0.7.4
-----

* Issue #20: Fix comparison of parsed SVN version on Python 3.

0.7.3
-----

* Issue #1: Disable installation of Windows-specific files on non-Windows systems.
* Use new sysconfig module with Python 2.7 or >=3.2.

0.7.2
-----

* Issue #14: Use markerlib when the ``parser`` module is not available.
* Issue #10: ``ez_setup.py`` now uses HTTPS to download setuptools from PyPI.

0.7.1
-----

* Fix NameError (Issue #3) again - broken in bad merge.

0.7
---

* Merged Setuptools and Distribute. See docs/merge.txt for details.

Added several features that were slated for setuptools 0.6c12:

* Index URL now defaults to HTTPS.
* Added experimental environment marker support. Now clients may designate a
  PEP-426 environment marker for "extra" dependencies. Setuptools uses this
  feature in ``setup.py`` for optional SSL and certificate validation support
  on older platforms. Based on Distutils-SIG discussions, the syntax is
  somewhat tentative. There should probably be a PEP with a firmer spec before
  the feature should be considered suitable for use.
* Added support for SSL certificate validation when installing packages from
  an HTTPS service.

0.7b4
-----

* Issue #3: Fixed NameError in SSL support.

0.6.49
------

* Move warning check in ``get_cache_path`` to follow the directory creation
  to avoid errors when the cache path does not yet exist. Fixes the error
  reported in Distribute #375.

0.6.48
------

* Correct AttributeError in ``ResourceManager.get_cache_path`` introduced in
  0.6.46 (redo).

0.6.47
------

* Correct AttributeError in ``ResourceManager.get_cache_path`` introduced in
  0.6.46.

0.6.46
------

* Distribute #375: Issue a warning if the PYTHON_EGG_CACHE or otherwise
  customized egg cache location specifies a directory that's group- or
  world-writable.

0.6.45
------

* Distribute #379: ``distribute_setup.py`` now traps VersionConflict as well,
  restoring ability to upgrade from an older setuptools version.

0.6.44
------

* ``distribute_setup.py`` has been updated to allow Setuptools 0.7 to
  satisfy use_setuptools.

0.6.43
------

* Distribute #378: Restore support for Python 2.4 Syntax (regression in 0.6.42).

0.6.42
------

* External links finder no longer yields duplicate links.
* Distribute #337: Moved site.py to setuptools/site-patch.py (graft of very old
  patch from setuptools trunk which inspired PR #31).

0.6.41
------

* Distribute #27: Use public api for loading resources from zip files rather than
  the private method ``_zip_directory_cache``.
* Added a new function ``easy_install.get_win_launcher`` which may be used by
  third-party libraries such as buildout to get a suitable script launcher.

0.6.40
------

* Distribute #376: brought back cli.exe and gui.exe that were deleted in the
  previous release.

0.6.39
------

* Add support for console launchers on ARM platforms.
* Fix possible issue in GUI launchers where the subsystem was not supplied to
  the linker.
* Launcher build script now refactored for robustness.
* Distribute #375: Resources extracted from a zip egg to the file system now also
  check the contents of the file against the zip contents during each
  invocation of get_resource_filename.

0.6.38
------

* Distribute #371: The launcher manifest file is now installed properly.

0.6.37
------

* Distribute #143: Launcher scripts, including easy_install itself, are now
  accompanied by a manifest on 32-bit Windows environments to avoid the
  Installer Detection Technology and thus undesirable UAC elevation described
  in `this Microsoft article
  <http://technet.microsoft.com/en-us/library/cc709628%28WS.10%29.aspx>`_.

0.6.36
------

* BB Pull Request #35: In Buildout #64, it was reported that
  under Python 3, installation of distutils scripts could attempt to copy
  the ``__pycache__`` directory as a file, causing an error, apparently only
  under Windows. Easy_install now skips all directories when processing
  metadata scripts.

0.6.35
------


Note this release is backward-incompatible with distribute 0.6.23-0.6.34 in
how it parses version numbers.

* Distribute #278: Restored compatibility with distribute 0.6.22 and setuptools
  0.6. Updated the documentation to match more closely with the version
  parsing as intended in setuptools 0.6.

0.6.34
------

* Distribute #341: 0.6.33 fails to build under Python 2.4.

0.6.33
------

* Fix 2 errors with Jython 2.5.
* Fix 1 failure with Jython 2.5 and 2.7.
* Disable workaround for Jython scripts on Linux systems.
* Distribute #336: ``setup.py`` no longer masks failure exit code when tests fail.
* Fix issue in pkg_resources where try/except around a platform-dependent
  import would trigger hook load failures on Mercurial. See pull request 32
  for details.
* Distribute #341: Fix a ResourceWarning.

0.6.32
------

* Fix test suite with Python 2.6.
* Fix some DeprecationWarnings and ResourceWarnings.
* Distribute #335: Backed out ``setup_requires`` superseding installed requirements
  until regression can be addressed.

0.6.31
------

* Distribute #303: Make sure the manifest only ever contains UTF-8 in Python 3.
* Distribute #329: Properly close files created by tests for compatibility with
  Jython.
* Work around Jython #1980 and Jython #1981.
* Distribute #334: Provide workaround for packages that reference ``sys.__stdout__``
  such as numpy does. This change should address
  `virtualenv #359 <https://github.com/pypa/virtualenv/issues/359>`_ as long
  as the system encoding is UTF-8 or the IO encoding is specified in the
  environment, i.e.::

     PYTHONIOENCODING=utf8 pip install numpy

* Fix for encoding issue when installing from Windows executable on Python 3.
* Distribute #323: Allow ``setup_requires`` requirements to supersede installed
  requirements. Added some new keyword arguments to existing pkg_resources
  methods. Also had to updated how __path__ is handled for namespace packages
  to ensure that when a new egg distribution containing a namespace package is
  placed on sys.path, the entries in __path__ are found in the same order they
  would have been in had that egg been on the path when pkg_resources was
  first imported.

0.6.30
------

* Distribute #328: Clean up temporary directories in distribute_setup.py.
* Fix fatal bug in distribute_setup.py.

0.6.29
------

* BB Pull Request #14: Honor file permissions in zip files.
* Distribute #327: Merged pull request #24 to fix a dependency problem with pip.
* Merged pull request #23 to fix https://github.com/pypa/virtualenv/issues/301.
* If Sphinx is installed, the ``upload_docs`` command now runs ``build_sphinx``
  to produce uploadable documentation.
* Distribute #326: ``upload_docs`` provided mangled auth credentials under Python 3.
* Distribute #320: Fix check for "creatable" in distribute_setup.py.
* Distribute #305: Remove a warning that was triggered during normal operations.
* Distribute #311: Print metadata in UTF-8 independent of platform.
* Distribute #303: Read manifest file with UTF-8 encoding under Python 3.
* Distribute #301: Allow to run tests of namespace packages when using 2to3.
* Distribute #304: Prevent import loop in site.py under Python 3.3.
* Distribute #283: Re-enable scanning of ``*.pyc`` / ``*.pyo`` files on Python 3.3.
* Distribute #299: The develop command didn't work on Python 3, when using 2to3,
  as the egg link would go to the Python 2 source. Linking to the 2to3'd code
  in build/lib makes it work, although you will have to rebuild the module
  before testing it.
* Distribute #306: Even if 2to3 is used, we build in-place under Python 2.
* Distribute #307: Prints the full path when .svn/entries is broken.
* Distribute #313: Support for sdist subcommands (Python 2.7)
* Distribute #314: test_local_index() would fail an OS X.
* Distribute #310: Non-ascii characters in a namespace __init__.py causes errors.
* Distribute #218: Improved documentation on behavior of ``package_data`` and
  ``include_package_data``. Files indicated by ``package_data`` are now included
  in the manifest.
* ``distribute_setup.py`` now allows a ``--download-base`` argument for retrieving
  distribute from a specified location.

0.6.28
------

* Distribute #294: setup.py can now be invoked from any directory.
* Scripts are now installed honoring the umask.
* Added support for .dist-info directories.
* Distribute #283: Fix and disable scanning of ``*.pyc`` / ``*.pyo`` files on
  Python 3.3.

0.6.27
------

* Support current snapshots of CPython 3.3.
* Distribute now recognizes README.rst as a standard, default readme file.
* Exclude 'encodings' modules when removing modules from sys.modules.
  Workaround for #285.
* Distribute #231: Don't fiddle with system python when used with buildout
  (bootstrap.py)

0.6.26
------

* Distribute #183: Symlinked files are now extracted from source distributions.
* Distribute #227: Easy_install fetch parameters are now passed during the
  installation of a source distribution; now fulfillment of setup_requires
  dependencies will honor the parameters passed to easy_install.

0.6.25
------

* Distribute #258: Workaround a cache issue
* Distribute #260: distribute_setup.py now accepts the --user parameter for
  Python 2.6 and later.
* Distribute #262: package_index.open_with_auth no longer throws LookupError
  on Python 3.
* Distribute #269: AttributeError when an exception occurs reading Manifest.in
  on late releases of Python.
* Distribute #272: Prevent TypeError when namespace package names are unicode
  and single-install-externally-managed is used. Also fixes PIP issue
  449.
* Distribute #273: Legacy script launchers now install with Python2/3 support.

0.6.24
------

* Distribute #249: Added options to exclude 2to3 fixers

0.6.23
------

* Distribute #244: Fixed a test
* Distribute #243: Fixed a test
* Distribute #239: Fixed a test
* Distribute #240: Fixed a test
* Distribute #241: Fixed a test
* Distribute #237: Fixed a test
* Distribute #238: easy_install now uses 64bit executable wrappers on 64bit Python
* Distribute #208: Fixed parsed_versions, it now honors post-releases as noted in the documentation
* Distribute #207: Windows cli and gui wrappers pass CTRL-C to child python process
* Distribute #227: easy_install now passes its arguments to setup.py bdist_egg
* Distribute #225: Fixed a NameError on Python 2.5, 2.4

0.6.21
------

* Distribute #225: FIxed a regression on py2.4

0.6.20
------

* Distribute #135: Include url in warning when processing URLs in package_index.
* Distribute #212: Fix issue where easy_instal fails on Python 3 on windows installer.
* Distribute #213: Fix typo in documentation.

0.6.19
------

* Distribute #206: AttributeError: 'HTTPMessage' object has no attribute 'getheaders'

0.6.18
------

* Distribute #210: Fixed a regression introduced by Distribute #204 fix.

0.6.17
------

* Support 'DISTRIBUTE_DISABLE_VERSIONED_EASY_INSTALL_SCRIPT' environment
  variable to allow to disable installation of easy_install-${version} script.
* Support Python >=3.1.4 and >=3.2.1.
* Distribute #204: Don't try to import the parent of a namespace package in
  declare_namespace
* Distribute #196: Tolerate responses with multiple Content-Length headers
* Distribute #205: Sandboxing doesn't preserve working_set. Leads to setup_requires
  problems.

0.6.16
------

* Builds sdist gztar even on Windows (avoiding Distribute #193).
* Distribute #192: Fixed metadata omitted on Windows when package_dir
  specified with forward-slash.
* Distribute #195: Cython build support.
* Distribute #200: Issues with recognizing 64-bit packages on Windows.

0.6.15
------

* Fixed typo in bdist_egg
* Several issues under Python 3 has been solved.
* Distribute #146: Fixed missing DLL files after easy_install of windows exe package.

0.6.14
------

* Distribute #170: Fixed unittest failure. Thanks to Toshio.
* Distribute #171: Fixed race condition in unittests cause deadlocks in test suite.
* Distribute #143: Fixed a lookup issue with easy_install.
  Thanks to David and Zooko.
* Distribute #174: Fixed the edit mode when its used with setuptools itself

0.6.13
------

* Distribute #160: 2.7 gives ValueError("Invalid IPv6 URL")
* Distribute #150: Fixed using ~/.local even in a --no-site-packages virtualenv
* Distribute #163: scan index links before external links, and don't use the md5 when
  comparing two distributions

0.6.12
------

* Distribute #149: Fixed various failures on 2.3/2.4

0.6.11
------

* Found another case of SandboxViolation - fixed
* Distribute #15 and Distribute #48: Introduced a socket timeout of 15 seconds on url openings
* Added indexsidebar.html into MANIFEST.in
* Distribute #108: Fixed TypeError with Python3.1
* Distribute #121: Fixed --help install command trying to actually install.
* Distribute #112: Added an os.makedirs so that Tarek's solution will work.
* Distribute #133: Added --no-find-links to easy_install
* Added easy_install --user
* Distribute #100: Fixed develop --user not taking '.' in PYTHONPATH into account
* Distribute #134: removed spurious UserWarnings. Patch by VanLindberg
* Distribute #138: cant_write_to_target error when setup_requires is used.
* Distribute #147: respect the sys.dont_write_bytecode flag

0.6.10
------

* Reverted change made for the DistributionNotFound exception because
  zc.buildout uses the exception message to get the name of the
  distribution.

0.6.9
-----

* Distribute #90: unknown setuptools version can be added in the working set
* Distribute #87: setupt.py doesn't try to convert distribute_setup.py anymore
  Initial Patch by arfrever.
* Distribute #89: added a side bar with a download link to the doc.
* Distribute #86: fixed missing sentence in pkg_resources doc.
* Added a nicer error message when a DistributionNotFound is raised.
* Distribute #80: test_develop now works with Python 3.1
* Distribute #93: upload_docs now works if there is an empty sub-directory.
* Distribute #70: exec bit on non-exec files
* Distribute #99: now the standalone easy_install command doesn't uses a
  "setup.cfg" if any exists in the working directory. It will use it
  only if triggered by ``install_requires`` from a setup.py call
  (install, develop, etc).
* Distribute #101: Allowing ``os.devnull`` in Sandbox
* Distribute #92: Fixed the "no eggs" found error with MacPort
  (platform.mac_ver() fails)
* Distribute #103: test_get_script_header_jython_workaround not run
  anymore under py3 with C or POSIX local. Contributed by Arfrever.
* Distribute #104: removed the assertion when the installation fails,
  with a nicer message for the end user.
* Distribute #100: making sure there's no SandboxViolation when
  the setup script patches setuptools.

0.6.8
-----

* Added "check_packages" in dist. (added in Setuptools 0.6c11)
* Fixed the DONT_PATCH_SETUPTOOLS state.

0.6.7
-----

* Distribute #58: Added --user support to the develop command
* Distribute #11: Generated scripts now wrap their call to the script entry point
  in the standard "if name == 'main'"
* Added the 'DONT_PATCH_SETUPTOOLS' environment variable, so virtualenv
  can drive an installation that doesn't patch a global setuptools.
* Reviewed unladen-swallow specific change from
  http://code.google.com/p/unladen-swallow/source/detail?spec=svn875&r=719
  and determined that it no longer applies. Distribute should work fine with
  Unladen Swallow 2009Q3.
* Distribute #21: Allow PackageIndex.open_url to gracefully handle all cases of a
  httplib.HTTPException instead of just InvalidURL and BadStatusLine.
* Removed virtual-python.py from this distribution and updated documentation
  to point to the actively maintained virtualenv instead.
* Distribute #64: use_setuptools no longer rebuilds the distribute egg every
  time it is run
* use_setuptools now properly respects the requested version
* use_setuptools will no longer try to import a distribute egg for the
  wrong Python version
* Distribute #74: no_fake should be True by default.
* Distribute #72: avoid a bootstrapping issue with easy_install -U

0.6.6
-----

* Unified the bootstrap file so it works on both py2.x and py3k without 2to3
  (patch by Holger Krekel)

0.6.5
-----

* Distribute #65: cli.exe and gui.exe are now generated at build time,
  depending on the platform in use.

* Distribute #67: Fixed doc typo (PEP 381/PEP 382).

* Distribute no longer shadows setuptools if we require a 0.7-series
  setuptools. And an error is raised when installing a 0.7 setuptools with
  distribute.

* When run from within buildout, no attempt is made to modify an existing
  setuptools egg, whether in a shared egg directory or a system setuptools.

* Fixed a hole in sandboxing allowing builtin file to write outside of
  the sandbox.

0.6.4
-----

* Added the generation of ``distribute_setup_3k.py`` during the release.
  This closes Distribute #52.

* Added an upload_docs command to easily upload project documentation to
  PyPI's https://pythonhosted.org. This close issue Distribute #56.

* Fixed a bootstrap bug on the use_setuptools() API.

0.6.3
-----

setuptools
^^^^^^^^^^

* Fixed a bunch of calls to file() that caused crashes on Python 3.

bootstrapping
^^^^^^^^^^^^^

* Fixed a bug in sorting that caused bootstrap to fail on Python 3.

0.6.2
-----

setuptools
^^^^^^^^^^

* Added Python 3 support; see docs/python3.txt.
  This closes Old Setuptools #39.

* Added option to run 2to3 automatically when installing on Python 3.
  This closes issue Distribute #31.

* Fixed invalid usage of requirement.parse, that broke develop -d.
  This closes Old Setuptools #44.

* Fixed script launcher for 64-bit Windows.
  This closes Old Setuptools #2.

* KeyError when compiling extensions.
  This closes Old Setuptools #41.

bootstrapping
^^^^^^^^^^^^^

* Fixed bootstrap not working on Windows. This closes issue Distribute #49.

* Fixed 2.6 dependencies. This closes issue Distribute #50.

* Make sure setuptools is patched when running through easy_install
  This closes Old Setuptools #40.

0.6.1
-----

setuptools
^^^^^^^^^^

* package_index.urlopen now catches BadStatusLine and malformed url errors.
  This closes Distribute #16 and Distribute #18.

* zip_ok is now False by default. This closes Old Setuptools #33.

* Fixed invalid URL error catching. Old Setuptools #20.

* Fixed invalid bootstraping with easy_install installation (Distribute #40).
  Thanks to Florian Schulze for the help.

* Removed buildout/bootstrap.py. A new repository will create a specific
  bootstrap.py script.


bootstrapping
^^^^^^^^^^^^^

* The bootstrap process leave setuptools alone if detected in the system
  and --root or --prefix is provided, but is not in the same location.
  This closes Distribute #10.

0.6
---

setuptools
^^^^^^^^^^

* Packages required at build time where not fully present at install time.
  This closes Distribute #12.

* Protected against failures in tarfile extraction. This closes Distribute #10.

* Made Jython api_tests.txt doctest compatible. This closes Distribute #7.

* sandbox.py replaced builtin type file with builtin function open. This
  closes Distribute #6.

* Immediately close all file handles. This closes Distribute #3.

* Added compatibility with Subversion 1.6. This references Distribute #1.

pkg_resources
^^^^^^^^^^^^^

* Avoid a call to /usr/bin/sw_vers on OSX and use the official platform API
  instead. Based on a patch from ronaldoussoren. This closes issue #5.

* Fixed a SandboxViolation for mkdir that could occur in certain cases.
  This closes Distribute #13.

* Allow to find_on_path on systems with tight permissions to fail gracefully.
  This closes Distribute #9.

* Corrected inconsistency between documentation and code of add_entry.
  This closes Distribute #8.

* Immediately close all file handles. This closes Distribute #3.

easy_install
^^^^^^^^^^^^

* Immediately close all file handles. This closes Distribute #3.

0.6c9
-----

 * Fixed a missing files problem when using Windows source distributions on
   non-Windows platforms, due to distutils not handling manifest file line
   endings correctly.

 * Updated Pyrex support to work with Pyrex 0.9.6 and higher.

 * Minor changes for Jython compatibility, including skipping tests that can't
   work on Jython.

 * Fixed not installing eggs in ``install_requires`` if they were also used for
   ``setup_requires`` or ``tests_require``.

 * Fixed not fetching eggs in ``install_requires`` when running tests.

 * Allow ``ez_setup.use_setuptools()`` to upgrade existing setuptools
   installations when called from a standalone ``setup.py``.

 * Added a warning if a namespace package is declared, but its parent package
   is not also declared as a namespace.

 * Support Subversion 1.5

 * Removed use of deprecated ``md5`` module if ``hashlib`` is available

 * Fixed ``bdist_wininst upload`` trying to upload the ``.exe`` twice

 * Fixed ``bdist_egg`` putting a ``native_libs.txt`` in the source package's
   ``.egg-info``, when it should only be in the built egg's ``EGG-INFO``.

 * Ensure that _full_name is set on all shared libs before extensions are
   checked for shared lib usage.  (Fixes a bug in the experimental shared
   library build support.)

 * Fix to allow unpacked eggs containing native libraries to fail more
   gracefully under Google App Engine (with an ``ImportError`` loading the
   C-based module, instead of getting a ``NameError``).

 * Fixed ``win32.exe`` support for .pth files, so unnecessary directory nesting
   is flattened out in the resulting egg.  (There was a case-sensitivity
   problem that affected some distributions, notably ``pywin32``.)

 * Prevent ``--help-commands`` and other junk from showing under Python 2.5
   when running ``easy_install --help``.

 * Fixed GUI scripts sometimes not executing on Windows

 * Fixed not picking up dependency links from recursive dependencies.

 * Only make ``.py``, ``.dll`` and ``.so`` files executable when unpacking eggs

 * Changes for Jython compatibility

 * Improved error message when a requirement is also a directory name, but the
   specified directory is not a source package.

 * Fixed ``--allow-hosts`` option blocking ``file:`` URLs

 * Fixed HTTP SVN detection failing when the page title included a project
   name (e.g. on SourceForge-hosted SVN)

 * Fix Jython script installation to handle ``#!`` lines better when
   ``sys.executable`` is a script.

 * Removed use of deprecated ``md5`` module if ``hashlib`` is available

 * Keep site directories (e.g. ``site-packages``) from being included in
   ``.pth`` files.

0.6c7
-----

 * Fixed ``distutils.filelist.findall()`` crashing on broken symlinks, and
   ``egg_info`` command failing on new, uncommitted SVN directories.

 * Fix import problems with nested namespace packages installed via
   ``--root`` or ``--single-version-externally-managed``, due to the
   parent package not having the child package as an attribute.

 * ``ftp:`` download URLs now work correctly.

 * The default ``--index-url`` is now ``https://pypi.python.org/simple``, to use
   the Python Package Index's new simpler (and faster!) REST API.

0.6c6
-----

 * Added ``--egg-path`` option to ``develop`` command, allowing you to force
   ``.egg-link`` files to use relative paths (allowing them to be shared across
   platforms on a networked drive).

 * Fix not building binary RPMs correctly.

 * Fix "eggsecutables" (such as setuptools' own egg) only being runnable with
   bash-compatible shells.

 * Fix ``#!`` parsing problems in Windows ``.exe`` script wrappers, when there
   was whitespace inside a quoted argument or at the end of the ``#!`` line
   (a regression introduced in 0.6c4).

 * Fix ``test`` command possibly failing if an older version of the project
   being tested was installed on ``sys.path`` ahead of the test source
   directory.

 * Fix ``find_packages()`` treating ``ez_setup`` and directories with ``.`` in
   their names as packages.

 * EasyInstall no longer aborts the installation process if a URL it wants to
   retrieve can't be downloaded, unless the URL is an actual package download.
   Instead, it issues a warning and tries to keep going.

 * Fixed distutils-style scripts originally built on Windows having their line
   endings doubled when installed on any platform.

 * Added ``--local-snapshots-ok`` flag, to allow building eggs from projects
   installed using ``setup.py develop``.

 * Fixed not HTML-decoding URLs scraped from web pages

0.6c5
-----

 * Fix uploaded ``bdist_rpm`` packages being described as ``bdist_egg``
   packages under Python versions less than 2.5.

 * Fix uploaded ``bdist_wininst`` packages being described as suitable for
   "any" version by Python 2.5, even if a ``--target-version`` was specified.

 * Fixed ``.dll`` files on Cygwin not having executable permissions when an egg
   is installed unzipped.

0.6c4
-----

 * Overhauled Windows script wrapping to support ``bdist_wininst`` better.
   Scripts installed with ``bdist_wininst`` will always use ``#!python.exe`` or
   ``#!pythonw.exe`` as the executable name (even when built on non-Windows
   platforms!), and the wrappers will look for the executable in the script's
   parent directory (which should find the right version of Python).

 * Fix ``upload`` command not uploading files built by ``bdist_rpm`` or
   ``bdist_wininst`` under Python 2.3 and 2.4.

 * Add support for "eggsecutable" headers: a ``#!/bin/sh`` script that is
   prepended to an ``.egg`` file to allow it to be run as a script on Unix-ish
   platforms.  (This is mainly so that setuptools itself can have a single-file
   installer on Unix, without doing multiple downloads, dealing with firewalls,
   etc.)

 * Fix problem with empty revision numbers in Subversion 1.4 ``entries`` files

 * Use cross-platform relative paths in ``easy-install.pth`` when doing
   ``develop`` and the source directory is a subdirectory of the installation
   target directory.

 * Fix a problem installing eggs with a system packaging tool if the project
   contained an implicit namespace package; for example if the ``setup()``
   listed a namespace package ``foo.bar`` without explicitly listing ``foo``
   as a namespace package.

 * Added support for HTTP "Basic" authentication using ``http://user:pass@host``
   URLs.  If a password-protected page contains links to the same host (and
   protocol), those links will inherit the credentials used to access the
   original page.

 * Removed all special support for Sourceforge mirrors, as Sourceforge's
   mirror system now works well for non-browser downloads.

 * Fixed not recognizing ``win32.exe`` installers that included a custom
   bitmap.

 * Fixed not allowing ``os.open()`` of paths outside the sandbox, even if they
   are opened read-only (e.g. reading ``/dev/urandom`` for random numbers, as
   is done by ``os.urandom()`` on some platforms).

 * Fixed a problem with ``.pth`` testing on Windows when ``sys.executable``
   has a space in it (e.g., the user installed Python to a ``Program Files``
   directory).

0.6c3
-----

 * Fixed breakages caused by Subversion 1.4's new "working copy" format

 * You can once again use "python -m easy_install" with Python 2.4 and above.

 * Python 2.5 compatibility fixes added.

0.6c2
-----

 * The ``ez_setup`` module displays the conflicting version of setuptools (and
   its installation location) when a script requests a version that's not
   available.

 * Running ``setup.py develop`` on a setuptools-using project will now install
   setuptools if needed, instead of only downloading the egg.

 * Windows script wrappers now support quoted arguments and arguments
   containing spaces.  (Patch contributed by Jim Fulton.)

 * The ``ez_setup.py`` script now actually works when you put a setuptools
   ``.egg`` alongside it for bootstrapping an offline machine.

 * A writable installation directory on ``sys.path`` is no longer required to
   download and extract a source distribution using ``--editable``.

 * Generated scripts now use ``-x`` on the ``#!`` line when ``sys.executable``
   contains non-ASCII characters, to prevent deprecation warnings about an
   unspecified encoding when the script is run.

0.6c1
-----

 * Fixed ``AttributeError`` when trying to download a ``setup_requires``
   dependency when a distribution lacks a ``dependency_links`` setting.

 * Made ``zip-safe`` and ``not-zip-safe`` flag files contain a single byte, so
   as to play better with packaging tools that complain about zero-length
   files.

 * Made ``setup.py develop`` respect the ``--no-deps`` option, which it
   previously was ignoring.

 * Support ``extra_path`` option to ``setup()`` when ``install`` is run in
   backward-compatibility mode.

 * Source distributions now always include a ``setup.cfg`` file that explicitly
   sets ``egg_info`` options such that they produce an identical version number
   to the source distribution's version number.  (Previously, the default
   version number could be different due to the use of ``--tag-date``, or if
   the version was overridden on the command line that built the source
   distribution.)

 * EasyInstall now includes setuptools version information in the
   ``User-Agent`` string sent to websites it visits.

0.6b4
-----

 * Fix ``register`` not obeying name/version set by ``egg_info`` command, if
   ``egg_info`` wasn't explicitly run first on the same command line.

 * Added ``--no-date`` and ``--no-svn-revision`` options to ``egg_info``
   command, to allow suppressing tags configured in ``setup.cfg``.

 * Fixed redundant warnings about missing ``README`` file(s); it should now
   appear only if you are actually a source distribution.

 * Fix creating Python wrappers for non-Python scripts

 * Fix ``ftp://`` directory listing URLs from causing a crash when used in the
   "Home page" or "Download URL" slots on PyPI.

 * Fix ``sys.path_importer_cache`` not being updated when an existing zipfile
   or directory is deleted/overwritten.

 * Fix not recognizing HTML 404 pages from package indexes.

 * Allow ``file://`` URLs to be used as a package index.  URLs that refer to
   directories will use an internally-generated directory listing if there is
   no ``index.html`` file in the directory.

 * Allow external links in a package index to be specified using
   ``rel="homepage"`` or ``rel="download"``, without needing the old
   PyPI-specific visible markup.

 * Suppressed warning message about possibly-misspelled project name, if an egg
   or link for that project name has already been seen.

0.6b3
-----

 * Fix ``bdist_egg`` not including files in subdirectories of ``.egg-info``.

 * Allow ``.py`` files found by the ``include_package_data`` option to be
   automatically included. Remove duplicate data file matches if both
   ``include_package_data`` and ``package_data`` are used to refer to the same
   files.

 * Fix local ``--find-links`` eggs not being copied except with
   ``--always-copy``.

 * Fix sometimes not detecting local packages installed outside of "site"
   directories.

 * Fix mysterious errors during initial ``setuptools`` install, caused by
   ``ez_setup`` trying to run ``easy_install`` twice, due to a code fallthru
   after deleting the egg from which it's running.

0.6b2
-----

 * Don't install or update a ``site.py`` patch when installing to a
   ``PYTHONPATH`` directory with ``--multi-version``, unless an
   ``easy-install.pth`` file is already in use there.

 * Construct ``.pth`` file paths in such a way that installing an egg whose
   name begins with ``import`` doesn't cause a syntax error.

 * Fixed a bogus warning message that wasn't updated since the 0.5 versions.

0.6b1
-----

 * Strip ``module`` from the end of compiled extension modules when computing
   the name of a ``.py`` loader/wrapper.  (Python's import machinery ignores
   this suffix when searching for an extension module.)

 * Better ambiguity management: accept ``#egg`` name/version even if processing
   what appears to be a correctly-named distutils file, and ignore ``.egg``
   files with no ``-``, since valid Python ``.egg`` files always have a version
   number (but Scheme eggs often don't).

 * Support ``file://`` links to directories in ``--find-links``, so that
   easy_install can build packages from local source checkouts.

 * Added automatic retry for Sourceforge mirrors.  The new download process is
   to first just try dl.sourceforge.net, then randomly select mirror IPs and
   remove ones that fail, until something works.  The removed IPs stay removed
   for the remainder of the run.

 * Ignore bdist_dumb distributions when looking at download URLs.

0.6a11
------

 * Added ``test_loader`` keyword to support custom test loaders

 * Added ``setuptools.file_finders`` entry point group to allow implementing
   revision control plugins.

 * Added ``--identity`` option to ``upload`` command.

 * Added ``dependency_links`` to allow specifying URLs for ``--find-links``.

 * Enhanced test loader to scan packages as well as modules, and call
   ``additional_tests()`` if present to get non-unittest tests.

 * Support namespace packages in conjunction with system packagers, by omitting
   the installation of any ``__init__.py`` files for namespace packages, and
   adding a special ``.pth`` file to create a working package in
   ``sys.modules``.

 * Made ``--single-version-externally-managed`` automatic when ``--root`` is
   used, so that most system packagers won't require special support for
   setuptools.

 * Fixed ``setup_requires``, ``tests_require``, etc. not using ``setup.cfg`` or
   other configuration files for their option defaults when installing, and
   also made the install use ``--multi-version`` mode so that the project
   directory doesn't need to support .pth files.

 * ``MANIFEST.in`` is now forcibly closed when any errors occur while reading
   it. Previously, the file could be left open and the actual error would be
   masked by problems trying to remove the open file on Windows systems.

 * Process ``dependency_links.txt`` if found in a distribution, by adding the
   URLs to the list for scanning.

 * Use relative paths in ``.pth`` files when eggs are being installed to the
   same directory as the ``.pth`` file.  This maximizes portability of the
   target directory when building applications that contain eggs.

 * Added ``easy_install-N.N`` script(s) for convenience when using multiple
   Python versions.

 * Added automatic handling of installation conflicts.  Eggs are now shifted to
   the front of sys.path, in an order consistent with where they came from,
   making EasyInstall seamlessly co-operate with system package managers.

   The ``--delete-conflicting`` and ``--ignore-conflicts-at-my-risk`` options
   are now no longer necessary, and will generate warnings at the end of a
   run if you use them.

 * Don't recursively traverse subdirectories given to ``--find-links``.

0.6a10
------

 * Fixed the ``develop`` command ignoring ``--find-links``.

 * Added exhaustive testing of the install directory, including a spawn test
   for ``.pth`` file support, and directory writability/existence checks.  This
   should virtually eliminate the need to set or configure ``--site-dirs``.

 * Added ``--prefix`` option for more do-what-I-mean-ishness in the absence of
   RTFM-ing.  :)

 * Enhanced ``PYTHONPATH`` support so that you don't have to put any eggs on it
   manually to make it work.  ``--multi-version`` is no longer a silent
   default; you must explicitly use it if installing to a non-PYTHONPATH,
   non-"site" directory.

 * Expand ``$variables`` used in the ``--site-dirs``, ``--build-directory``,
   ``--install-dir``, and ``--script-dir`` options, whether on the command line
   or in configuration files.

 * Improved SourceForge mirror processing to work faster and be less affected
   by transient HTML changes made by SourceForge.

 * PyPI searches now use the exact spelling of requirements specified on the
   command line or in a project's ``install_requires``.  Previously, a
   normalized form of the name was used, which could lead to unnecessary
   full-index searches when a project's name had an underscore (``_``) in it.

 * EasyInstall can now download bare ``.py`` files and wrap them in an egg,
   as long as you include an ``#egg=name-version`` suffix on the URL, or if
   the ``.py`` file is listed as the "Download URL" on the project's PyPI page.
   This allows third parties to "package" trivial Python modules just by
   linking to them (e.g. from within their own PyPI page or download links
   page).

 * The ``--always-copy`` option now skips "system" and "development" eggs since
   they can't be reliably copied.  Note that this may cause EasyInstall to
   choose an older version of a package than what you expected, or it may cause
   downloading and installation of a fresh version of what's already installed.

 * The ``--find-links`` option previously scanned all supplied URLs and
   directories as early as possible, but now only directories and direct
   archive links are scanned immediately.  URLs are not retrieved unless a
   package search was already going to go online due to a package not being
   available locally, or due to the use of the ``--update`` or ``-U`` option.

 * Fixed the annoying ``--help-commands`` wart.

0.6a9
-----

 * The ``sdist`` command no longer uses the traditional ``MANIFEST`` file to
   create source distributions.  ``MANIFEST.in`` is still read and processed,
   as are the standard defaults and pruning. But the manifest is built inside
   the project's ``.egg-info`` directory as ``SOURCES.txt``, and it is rebuilt
   every time the ``egg_info`` command is run.

 * Added the ``include_package_data`` keyword to ``setup()``, allowing you to
   automatically include any package data listed in revision control or
   ``MANIFEST.in``

 * Added the ``exclude_package_data`` keyword to ``setup()``, allowing you to
   trim back files included via the ``package_data`` and
   ``include_package_data`` options.

 * Fixed ``--tag-svn-revision`` not working when run from a source
   distribution.

 * Added warning for namespace packages with missing ``declare_namespace()``

 * Added ``tests_require`` keyword to ``setup()``, so that e.g. packages
   requiring ``nose`` to run unit tests can make this dependency optional
   unless the ``test`` command is run.

 * Made all commands that use ``easy_install`` respect its configuration
   options, as this was causing some problems with ``setup.py install``.

 * Added an ``unpack_directory()`` driver to ``setuptools.archive_util``, so
   that you can process a directory tree through a processing filter as if it
   were a zipfile or tarfile.

 * Added an internal ``install_egg_info`` command to use as part of old-style
   ``install`` operations, that installs an ``.egg-info`` directory with the
   package.

 * Added a ``--single-version-externally-managed`` option to the ``install``
   command so that you can more easily wrap a "flat" egg in a system package.

 * Enhanced ``bdist_rpm`` so that it installs single-version eggs that
   don't rely on a ``.pth`` file. The ``--no-egg`` option has been removed,
   since all RPMs are now built in a more backwards-compatible format.

 * Support full roundtrip translation of eggs to and from ``bdist_wininst``
   format. Running ``bdist_wininst`` on a setuptools-based package wraps the
   egg in an .exe that will safely install it as an egg (i.e., with metadata
   and entry-point wrapper scripts), and ``easy_install`` can turn the .exe
   back into an ``.egg`` file or directory and install it as such.

 * Fixed ``.pth`` file processing picking up nested eggs (i.e. ones inside
   "baskets") when they weren't explicitly listed in the ``.pth`` file.

 * If more than one URL appears to describe the exact same distribution, prefer
   the shortest one.  This helps to avoid "table of contents" CGI URLs like the
   ones on effbot.org.

 * Quote arguments to python.exe (including python's path) to avoid problems
   when Python (or a script) is installed in a directory whose name contains
   spaces on Windows.

 * Support full roundtrip translation of eggs to and from ``bdist_wininst``
   format.  Running ``bdist_wininst`` on a setuptools-based package wraps the
   egg in an .exe that will safely install it as an egg (i.e., with metadata
   and entry-point wrapper scripts), and ``easy_install`` can turn the .exe
   back into an ``.egg`` file or directory and install it as such.

0.6a8
-----

 * Fixed some problems building extensions when Pyrex was installed, especially
   with Python 2.4 and/or packages using SWIG.

 * Made ``develop`` command accept all the same options as ``easy_install``,
   and use the ``easy_install`` command's configuration settings as defaults.

 * Made ``egg_info --tag-svn-revision`` fall back to extracting the revision
   number from ``PKG-INFO`` in case it is being run on a source distribution of
   a snapshot taken from a Subversion-based project.

 * Automatically detect ``.dll``, ``.so`` and ``.dylib`` files that are being
   installed as data, adding them to ``native_libs.txt`` automatically.

 * Fixed some problems with fresh checkouts of projects that don't include
   ``.egg-info/PKG-INFO`` under revision control and put the project's source
   code directly in the project directory. If such a package had any
   requirements that get processed before the ``egg_info`` command can be run,
   the setup scripts would fail with a "Missing 'Version:' header and/or
   PKG-INFO file" error, because the egg runtime interpreted the unbuilt
   metadata in a directory on ``sys.path`` (i.e. the current directory) as
   being a corrupted egg. Setuptools now monkeypatches the distribution
   metadata cache to pretend that the egg has valid version information, until
   it has a chance to make it actually be so (via the ``egg_info`` command).

 * Update for changed SourceForge mirror format

 * Fixed not installing dependencies for some packages fetched via Subversion

 * Fixed dependency installation with ``--always-copy`` not using the same
   dependency resolution procedure as other operations.

 * Fixed not fully removing temporary directories on Windows, if a Subversion
   checkout left read-only files behind

 * Fixed some problems building extensions when Pyrex was installed, especially
   with Python 2.4 and/or packages using SWIG.

0.6a7
-----

 * Fixed not being able to install Windows script wrappers using Python 2.3

0.6a6
-----

 * Added support for "traditional" PYTHONPATH-based non-root installation, and
   also the convenient ``virtual-python.py`` script, based on a contribution
   by Ian Bicking.  The setuptools egg now contains a hacked ``site`` module
   that makes the PYTHONPATH-based approach work with .pth files, so that you
   can get the full EasyInstall feature set on such installations.

 * Added ``--no-deps`` and ``--allow-hosts`` options.

 * Improved Windows ``.exe`` script wrappers so that the script can have the
   same name as a module without confusing Python.

 * Changed dependency processing so that it's breadth-first, allowing a
   depender's preferences to override those of a dependee, to prevent conflicts
   when a lower version is acceptable to the dependee, but not the depender.
   Also, ensure that currently installed/selected packages aren't given
   precedence over ones desired by a package being installed, which could
   cause conflict errors.

0.6a5
-----

 * Fixed missing gui/cli .exe files in distribution. Fixed bugs in tests.

0.6a3
-----

 * Added ``gui_scripts`` entry point group to allow installing GUI scripts
   on Windows and other platforms.  (The special handling is only for Windows;
   other platforms are treated the same as for ``console_scripts``.)

 * Improved error message when trying to use old ways of running
   ``easy_install``.  Removed the ability to run via ``python -m`` or by
   running ``easy_install.py``; ``easy_install`` is the command to run on all
   supported platforms.

 * Improved wrapper script generation and runtime initialization so that a
   VersionConflict doesn't occur if you later install a competing version of a
   needed package as the default version of that package.

 * Fixed a problem parsing version numbers in ``#egg=`` links.

0.6a2
-----

 * Added ``console_scripts`` entry point group to allow installing scripts
   without the need to create separate script files. On Windows, console
   scripts get an ``.exe`` wrapper so you can just type their name. On other
   platforms, the scripts are written without a file extension.

 * EasyInstall can now install "console_scripts" defined by packages that use
   ``setuptools`` and define appropriate entry points.  On Windows, console
   scripts get an ``.exe`` wrapper so you can just type their name.  On other
   platforms, the scripts are installed without a file extension.

 * Using ``python -m easy_install`` or running ``easy_install.py`` is now
   DEPRECATED, since an ``easy_install`` wrapper is now available on all
   platforms.

0.6a1
-----

 * Added support for building "old-style" RPMs that don't install an egg for
   the target package, using a ``--no-egg`` option.

 * The ``build_ext`` command now works better when using the ``--inplace``
   option and multiple Python versions. It now makes sure that all extensions
   match the current Python version, even if newer copies were built for a
   different Python version.

 * The ``upload`` command no longer attaches an extra ``.zip`` when uploading
   eggs, as PyPI now supports egg uploads without trickery.

 * The ``ez_setup`` script/module now displays a warning before downloading
   the setuptools egg, and attempts to check the downloaded egg against an
   internal MD5 checksum table.

 * Fixed the ``--tag-svn-revision`` option of ``egg_info`` not finding the
   latest revision number; it was using the revision number of the directory
   containing ``setup.py``, not the highest revision number in the project.

 * Added ``eager_resources`` setup argument

 * The ``sdist`` command now recognizes Subversion "deleted file" entries and
   does not include them in source distributions.

 * ``setuptools`` now embeds itself more thoroughly into the distutils, so that
   other distutils extensions (e.g. py2exe, py2app) will subclass setuptools'
   versions of things, rather than the native distutils ones.

 * Added ``entry_points`` and ``setup_requires`` arguments to ``setup()``;
   ``setup_requires`` allows you to automatically find and download packages
   that are needed in order to *build* your project (as opposed to running it).

 * ``setuptools`` now finds its commands, ``setup()`` argument validators, and
   metadata writers using entry points, so that they can be extended by
   third-party packages. See `Creating distutils Extensions
   <https://setuptools.pypa.io/en/latest/setuptools.html#creating-distutils-extensions>`_
   for more details.

 * The vestigial ``depends`` command has been removed. It was never finished
   or documented, and never would have worked without EasyInstall - which it
   pre-dated and was never compatible with.

 * EasyInstall now does MD5 validation of downloads from PyPI, or from any link
   that has an "#md5=..." trailer with a 32-digit lowercase hex md5 digest.

 * EasyInstall now handles symlinks in target directories by removing the link,
   rather than attempting to overwrite the link's destination.  This makes it
   easier to set up an alternate Python "home" directory (as described in
   the Non-Root Installation section of the docs).

 * Added support for handling MacOS platform information in ``.egg`` filenames,
   based on a contribution by Kevin Dangoor.  You may wish to delete and
   reinstall any eggs whose filename includes "darwin" and "Power_Macintosh",
   because the format for this platform information has changed so that minor
   OS X upgrades (such as 10.4.1 to 10.4.2) do not cause eggs built with a
   previous OS version to become obsolete.

 * easy_install's dependency processing algorithms have changed.  When using
   ``--always-copy``, it now ensures that dependencies are copied too.  When
   not using ``--always-copy``, it tries to use a single resolution loop,
   rather than recursing.

 * Fixed installing extra ``.pyc`` or ``.pyo`` files for scripts with ``.py``
   extensions.

 * Added ``--site-dirs`` option to allow adding custom "site" directories.
   Made ``easy-install.pth`` work in platform-specific alternate site
   directories (e.g. ``~/Library/Python/2.x/site-packages`` on Mac OS X).

 * If you manually delete the current version of a package, the next run of
   EasyInstall against the target directory will now remove the stray entry
   from the ``easy-install.pth`` file.

 * EasyInstall now recognizes URLs with a ``#egg=project_name`` fragment ID
   as pointing to the named project's source checkout.  Such URLs have a lower
   match precedence than any other kind of distribution, so they'll only be
   used if they have a higher version number than any other available
   distribution, or if you use the ``--editable`` option.  The ``#egg``
   fragment can contain a version if it's formatted as ``#egg=proj-ver``,
   where ``proj`` is the project name, and ``ver`` is the version number.  You
   *must* use the format for these values that the ``bdist_egg`` command uses;
   i.e., all non-alphanumeric runs must be condensed to single underscore
   characters.

 * Added the ``--editable`` option; see Editing and Viewing Source Packages
   in the docs.  Also, slightly changed the behavior of the
   ``--build-directory`` option.

 * Fixed the setup script sandbox facility not recognizing certain paths as
   valid on case-insensitive platforms.

0.5a12
------

 * The zip-safety scanner now checks for modules that might be used with
   ``python -m``, and marks them as unsafe for zipping, since Python 2.4 can't
   handle ``-m`` on zipped modules.

 * Fix ``python -m easy_install`` not working due to setuptools being installed
   as a zipfile.  Update safety scanner to check for modules that might be used
   as ``python -m`` scripts.

 * Misc. fixes for win32.exe support, including changes to support Python 2.4's
   changed ``bdist_wininst`` format.

0.5a11
------

 * Fix breakage of the "develop" command that was caused by the addition of
   ``--always-unzip`` to the ``easy_install`` command.

0.5a10
------

 * Put the ``easy_install`` module back in as a module, as it's needed for
   ``python -m`` to run it!

 * Allow ``--find-links/-f`` to accept local directories or filenames as well
   as URLs.

0.5a9
-----

 * Include ``svn:externals`` directories in source distributions as well as
   normal subversion-controlled files and directories.

 * Added ``exclude=patternlist`` option to ``setuptools.find_packages()``

 * Changed --tag-svn-revision to include an "r" in front of the revision number
   for better readability.

 * Added ability to build eggs without including source files (except for any
   scripts, of course), using the ``--exclude-source-files`` option to
   ``bdist_egg``.

 * ``setup.py install`` now automatically detects when an "unmanaged" package
   or module is going to be on ``sys.path`` ahead of a package being installed,
   thereby preventing the newer version from being imported. If this occurs,
   a warning message is output to ``sys.stderr``, but installation proceeds
   anyway. The warning message informs the user what files or directories
   need deleting, and advises them they can also use EasyInstall (with the
   ``--delete-conflicting`` option) to do it automatically.

 * The ``egg_info`` command now adds a ``top_level.txt`` file to the metadata
   directory that lists all top-level modules and packages in the distribution.
   This is used by the ``easy_install`` command to find possibly-conflicting
   "unmanaged" packages when installing the distribution.

 * Added ``zip_safe`` and ``namespace_packages`` arguments to ``setup()``.
   Added package analysis to determine zip-safety if the ``zip_safe`` flag
   is not given, and advise the author regarding what code might need changing.

 * Fixed the swapped ``-d`` and ``-b`` options of ``bdist_egg``.

 * EasyInstall now automatically detects when an "unmanaged" package or
   module is going to be on ``sys.path`` ahead of a package you're installing,
   thereby preventing the newer version from being imported.  By default, it
   will abort installation to alert you of the problem, but there are also
   new options (``--delete-conflicting`` and ``--ignore-conflicts-at-my-risk``)
   available to change the default behavior.  (Note: this new feature doesn't
   take effect for egg files that were built with older ``setuptools``
   versions, because they lack the new metadata file required to implement it.)

 * The ``easy_install`` distutils command now uses ``DistutilsError`` as its
   base error type for errors that should just issue a message to stderr and
   exit the program without a traceback.

 * EasyInstall can now be given a path to a directory containing a setup
   script, and it will attempt to build and install the package there.

 * EasyInstall now performs a safety analysis on module contents to determine
   whether a package is likely to run in zipped form, and displays
   information about what modules may be doing introspection that would break
   when running as a zipfile.

 * Added the ``--always-unzip/-Z`` option, to force unzipping of packages that
   would ordinarily be considered safe to unzip, and changed the meaning of
   ``--zip-ok/-z`` to "always leave everything zipped".

0.5a8
-----

 * The "egg_info" command now always sets the distribution metadata to "safe"
   forms of the distribution name and version, so that distribution files will
   be generated with parseable names (i.e., ones that don't include '-' in the
   name or version). Also, this means that if you use the various ``--tag``
   options of "egg_info", any distributions generated will use the tags in the
   version, not just egg distributions.

 * Added support for defining command aliases in distutils configuration files,
   under the "[aliases]" section. To prevent recursion and to allow aliases to
   call the command of the same name, a given alias can be expanded only once
   per command-line invocation. You can define new aliases with the "alias"
   command, either for the local, global, or per-user configuration.

 * Added "rotate" command to delete old distribution files, given a set of
   patterns to match and the number of files to keep.  (Keeps the most
   recently-modified distribution files matching each pattern.)

 * Added "saveopts" command that saves all command-line options for the current
   invocation to the local, global, or per-user configuration file. Useful for
   setting defaults without having to hand-edit a configuration file.

 * Added a "setopt" command that sets a single option in a specified distutils
   configuration file.

 * There is now a separate documentation page for setuptools; revision
   history that's not specific to EasyInstall has been moved to that page.

0.5a7
-----

 * Added "upload" support for egg and source distributions, including a bug
   fix for "upload" and a temporary workaround for lack of .egg support in
   PyPI.

0.5a6
-----

 * Beefed up the "sdist" command so that if you don't have a MANIFEST.in, it
   will include all files under revision control (CVS or Subversion) in the
   current directory, and it will regenerate the list every time you create a
   source distribution, not just when you tell it to. This should make the
   default "do what you mean" more often than the distutils' default behavior
   did, while still retaining the old behavior in the presence of MANIFEST.in.

 * Fixed the "develop" command always updating .pth files, even if you
   specified ``-n`` or ``--dry-run``.

 * Slightly changed the format of the generated version when you use
   ``--tag-build`` on the "egg_info" command, so that you can make tagged
   revisions compare *lower* than the version specified in setup.py (e.g. by
   using ``--tag-build=dev``).

0.5a5
-----

 * Added ``develop`` command to ``setuptools``-based packages. This command
   installs an ``.egg-link`` pointing to the package's source directory, and
   script wrappers that ``execfile()`` the source versions of the package's
   scripts. This lets you put your development checkout(s) on sys.path without
   having to actually install them.  (To uninstall the link, use
   use ``setup.py develop --uninstall``.)

 * Added ``egg_info`` command to ``setuptools``-based packages. This command
   just creates or updates the "projectname.egg-info" directory, without
   building an egg.  (It's used by the ``bdist_egg``, ``test``, and ``develop``
   commands.)

 * Enhanced the ``test`` command so that it doesn't install the package, but
   instead builds any C extensions in-place, updates the ``.egg-info``
   metadata, adds the source directory to ``sys.path``, and runs the tests
   directly on the source. This avoids an "unmanaged" installation of the
   package to ``site-packages`` or elsewhere.

 * Made ``easy_install`` a standard ``setuptools`` command, moving it from
   the ``easy_install`` module to ``setuptools.command.easy_install``. Note
   that if you were importing or extending it, you must now change your imports
   accordingly.  ``easy_install.py`` is still installed as a script, but not as
   a module.

0.5a4
-----

 * Setup scripts using setuptools can now list their dependencies directly in
   the setup.py file, without having to manually create a ``depends.txt`` file.
   The ``install_requires`` and ``extras_require`` arguments to ``setup()``
   are used to create a dependencies file automatically. If you are manually
   creating ``depends.txt`` right now, please switch to using these setup
   arguments as soon as practical, because ``depends.txt`` support will be
   removed in the 0.6 release cycle. For documentation on the new arguments,
   see the ``setuptools.dist.Distribution`` class.

 * Setup scripts using setuptools now always install using ``easy_install``
   internally, for ease of uninstallation and upgrading.

 * Added ``--always-copy/-a`` option to always copy needed packages to the
   installation directory, even if they're already present elsewhere on
   sys.path. (In previous versions, this was the default behavior, but now
   you must request it.)

 * Added ``--upgrade/-U`` option to force checking PyPI for latest available
   version(s) of all packages requested by name and version, even if a matching
   version is available locally.

 * Added automatic installation of dependencies declared by a distribution
   being installed.  These dependencies must be listed in the distribution's
   ``EGG-INFO`` directory, so the distribution has to have declared its
   dependencies by using setuptools.  If a package has requirements it didn't
   declare, you'll still have to deal with them yourself.  (E.g., by asking
   EasyInstall to find and install them.)

 * Added the ``--record`` option to ``easy_install`` for the benefit of tools
   that run ``setup.py install --record=filename`` on behalf of another
   packaging system.)

0.5a3
-----

 * Fixed not setting script permissions to allow execution.

 * Improved sandboxing so that setup scripts that want a temporary directory
   (e.g. pychecker) can still run in the sandbox.

0.5a2
-----

 * Fix stupid stupid refactoring-at-the-last-minute typos.  :(

0.5a1
-----

 * Added support for "self-installation" bootstrapping. Packages can now
   include ``ez_setup.py`` in their source distribution, and add the following
   to their ``setup.py``, in order to automatically bootstrap installation of
   setuptools as part of their setup process::

    from ez_setup import use_setuptools
    use_setuptools()

    from setuptools import setup
    # etc...

 * Added support for converting ``.win32.exe`` installers to eggs on the fly.
   EasyInstall will now recognize such files by name and install them.

 * Fixed a problem with picking the "best" version to install (versions were
   being sorted as strings, rather than as parsed values)

0.4a4
-----

 * Added support for the distutils "verbose/quiet" and "dry-run" options, as
   well as the "optimize" flag.

 * Support downloading packages that were uploaded to PyPI (by scanning all
   links on package pages, not just the homepage/download links).

0.4a3
-----

 * Add progress messages to the search/download process so that you can tell
   what URLs it's reading to find download links.  (Hopefully, this will help
   people report out-of-date and broken links to package authors, and to tell
   when they've asked for a package that doesn't exist.)

0.4a2
-----

 * Added ``ez_setup.py`` installer/bootstrap script to make initial setuptools
   installation easier, and to allow distributions using setuptools to avoid
   having to include setuptools in their source distribution.

 * All downloads are now managed by the ``PackageIndex`` class (which is now
   subclassable and replaceable), so that embedders can more easily override
   download logic, give download progress reports, etc. The class has also
   been moved to the new ``setuptools.package_index`` module.

 * The ``Installer`` class no longer handles downloading, manages a temporary
   directory, or tracks the ``zip_ok`` option. Downloading is now handled
   by ``PackageIndex``, and ``Installer`` has become an ``easy_install``
   command class based on ``setuptools.Command``.

 * There is a new ``setuptools.sandbox.run_setup()`` API to invoke a setup
   script in a directory sandbox, and a new ``setuptools.archive_util`` module
   with an ``unpack_archive()`` API. These were split out of EasyInstall to
   allow reuse by other tools and applications.

 * ``setuptools.Command`` now supports reinitializing commands using keyword
   arguments to set/reset options. Also, ``Command`` subclasses can now set
   their ``command_consumes_arguments`` attribute to ``True`` in order to
   receive an ``args`` option containing the rest of the command line.

 * Added support for installing scripts

 * Added support for setting options via distutils configuration files, and
   using distutils' default options as a basis for EasyInstall's defaults.

 * Renamed ``--scan-url/-s`` to ``--find-links/-f`` to free up ``-s`` for the
   script installation directory option.

 * Use ``urllib2`` instead of ``urllib``, to allow use of ``https:`` URLs if
   Python includes SSL support.

0.4a1
-----

 * Added ``--scan-url`` and ``--index-url`` options, to scan download pages
   and search PyPI for needed packages.

0.3a4
-----

 * Restrict ``--build-directory=DIR/-b DIR`` option to only be used with single
   URL installs, to avoid running the wrong setup.py.

0.3a3
-----

 * Added ``--build-directory=DIR/-b DIR`` option.

 * Added "installation report" that explains how to use 'require()' when doing
   a multiversion install or alternate installation directory.

 * Added SourceForge mirror auto-select (Contributed by Ian Bicking)

 * Added "sandboxing" that stops a setup script from running if it attempts to
   write to the filesystem outside of the build area

 * Added more workarounds for packages with quirky ``install_data`` hacks

0.3a2
-----

 * Added new options to ``bdist_egg`` to allow tagging the egg's version number
   with a subversion revision number, the current date, or an explicit tag
   value. Run ``setup.py bdist_egg --help`` to get more information.

 * Added subversion download support for ``svn:`` and ``svn+`` URLs, as well as
   automatic recognition of HTTP subversion URLs (Contributed by Ian Bicking)

 * Misc. bug fixes

0.3a1
-----

 * Initial release.

