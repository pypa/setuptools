"""Timestamp comparison of files and groups of files."""

import os.path
import stat

from .errors import DistutilsFileError


def _newer(source, target):
    if not os.path.exists(target):
        return True

    mtime1 = os.stat(source)[stat.ST_MTIME]
    mtime2 = os.stat(target)[stat.ST_MTIME]

    return mtime1 > mtime2


def newer(source, target):
    """
    Is source modified more recently than target.

    Returns True if 'source' is modified more recently than
    'target' or if 'target' does not exist.

    Raises DistutilsFileError if 'source' does not exist.
    """
    if not os.path.exists(source):
        raise DistutilsFileError("file '%s' does not exist" % os.path.abspath(source))

    return _newer(source, target)


def newer_pairwise(sources, targets):
    """
    Filter filenames where sources are newer than targets.

    Walk two filename lists in parallel, testing if each source is newer
    than its corresponding target.  Returns a pair of lists (sources,
    targets) where source is newer than target, according to the semantics
    of 'newer()'.
    """
    if len(sources) != len(targets):
        raise ValueError("'sources' and 'targets' must be same length")

    # build a pair of lists (sources, targets) where source is newer
    n_sources = []
    n_targets = []
    for i in range(len(sources)):
        if newer(sources[i], targets[i]):
            n_sources.append(sources[i])
            n_targets.append(targets[i])

    return (n_sources, n_targets)


def newer_group(sources, target, missing='error'):
    """
    Is target out-of-date with respect to any file in sources.

    Return True if 'target' is out-of-date with respect to any file
    listed in 'sources'. In other words, if 'target' exists and is newer
    than every file in 'sources', return False; otherwise return True.
    ``missing`` controls how to handle a missing source file:

    - error (default): allow the ``stat()`` call to fail.
    - ignore: silently disregard any missing source files.
    - newer: treat missing source files as "target out of date". This
      mode is handy in "dry-run" mode: it will pretend to carry out
      commands that wouldn't work because inputs are missing, but
      that doesn't matter because dry-run won't run the commands.
    """

    def missing_as_newer(source):
        return missing == 'newer' and not os.path.exists(source)

    ignored = os.path.exists if missing == 'ignore' else None
    return any(
        missing_as_newer(source) or _newer(source, target)
        for source in filter(ignored, sources)
    )
