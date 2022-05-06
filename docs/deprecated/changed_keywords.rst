New and Changed ``setup()`` Keywords
====================================

This document tracks historical differences between ``setuptools`` and
``distutils``.

Since ``distutils`` was scheduled for removal from the standard library in
Python 3.12, and ``setuptools`` started its adoption, these differences became less
relevant.
Please check :doc:`/references/keywords` for a complete list of keyword
arguments that can be passed to the ``setuptools.setup()`` function and
a their full description.

.. tab:: Supported by both ``distutils`` and ``setuptoools``

    ``name`` string

    ``version`` string

    ``description`` string

    ``long_description`` string

    ``long_description_content_type`` string

    ``author`` string

    ``author_email`` string

    ``maintainer`` string

    ``maintainer_email`` string

    ``url`` string

    ``download_url`` string

    ``packages`` list

    ``py_modules`` list

    ``scripts`` list

    ``ext_package`` string

    ``ext_modules`` list

    ``classifiers`` list

    ``distclass`` Distribution subclass

    ``script_name`` string

    ``script_args`` list

    ``options`` dictionary

    ``license`` string

    ``license_file`` string **deprecated**

    ``license_files`` list

    ``keywords`` string or list

    ``platforms`` list

    ``cmdclass`` dictionary

    ``data_files`` list **deprecated**

    ``package_dir`` dictionary

    ``requires`` string or list **deprecated**

    ``obsoletes`` list **deprecated**

    ``provides`` list

.. tab:: Added or changed by ``setuptoools``

    ``include_package_data`` bool

    ``exclude_package_data`` dictionary

    ``package_data`` dictionary

    ``zip_safe`` bool

    ``install_requires`` string or list

    ``entry_points`` dictionary

    ``extras_require`` dictionary

    ``python_requires`` string

    ``setup_requires`` string or list **deprecated**

    ``dependency_links`` list **deprecated**

    ``namespace_packages`` list

    ``test_suite`` string or function **deprecated**

    ``tests_require`` string or list **deprecated**

    ``test_loader`` class **deprecated**

    ``eager_resources`` list

    ``project_urls`` dictionary
