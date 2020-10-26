Python Module Distribution Utilities extracted from the Python Standard Library

Synchronizing
=============

This project is kept in sync with the code still in stdlib.

From CPython
------------

The original history and attribution of all changes contributed to CPython can be found in the `cpython branch <https://github.com/pypa/distutils/tree/cpython>`_. If new commits are added to CPython, they should be synchronized back to this project.

First, create a clone of CPython that only includes the distutils changes. Due to the large size of the CPython repository, this operation is fairly expensive.

::

    git clone https://github.com/python/cpython python-distutils
    cd python-distutils
    git filter-branch --prune-empty --subdirectory-filter Lib/distutils master

Then, pull those changes into the repository at the cpython branch.

::

    cd $distutils
    git checkout cpython
    git fetch $python_distutils
    git merge FETCH_HEAD

Finally, merge the changes from cpython into master (possibly as a pull request).

To CPython
----------

Merging changes from this repository is easier.

From the CPython repo, cherry-pick the changes from this project.

::

    git -C $distutils format-patch HEAD~2 --stdout | git am --directory Lib

To Setuptools
-------------

Simply merge the changes directly into setuptools' repo.
