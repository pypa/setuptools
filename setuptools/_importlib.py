import sys


def disable_importlib_metadata_finder(metadata):
    """
    Ensure importlib_metadata doesn't provide older, incompatible
    Distributions.

    Workaround for #3102.
    """
    try:
        import importlib_metadata
    except ImportError:
        return
    except AttributeError:
        import warnings

        msg = (
            "`importlib-metadata` version is incompatible with `setuptools`.\n"
            "This problem is likely to be solved by installing an updated version of "
            "`importlib-metadata`."
        )
        warnings.warn(msg)  # Ensure a descriptive message is shown.
        raise  # This exception can be suppressed by _distutils_hack

    if importlib_metadata is metadata:
        return
    to_remove = [
        ob
        for ob in sys.meta_path
        if isinstance(ob, importlib_metadata.MetadataPathFinder)
    ]
    for item in to_remove:
        sys.meta_path.remove(item)


def check_old_importlib_metadata(metadata):
    """
    Warn the user if an old importlib_metadata is present and might
    cause problems.

    Workaround for #3452. Remove this check after 2022-12-31.
    """
    try:
        version = metadata.version('importlib_metadata')
        parsed = tuple(map(int, version.split('.')))
    except Exception:
        return

    if parsed > (4, 3):
        return

    msg = (
        "`importlib_metadata` version is incompatible with the stdlib "
        "importlib.metadata and may cause problems if plugins import "
        "importlib_metadata. See pypa/setuptools#3452 for details. "
        "Consider updating to importlib_metadata 4.3 or later."
    )
    import warnings
    warnings.warn(msg)


if sys.version_info < (3, 10):
    from setuptools.extern import importlib_metadata as metadata
    disable_importlib_metadata_finder(metadata)
else:
    import importlib.metadata as metadata  # noqa: F401
    check_old_importlib_metadata(metadata)


if sys.version_info < (3, 9):
    from setuptools.extern import importlib_resources as resources
else:
    import importlib.resources as resources  # noqa: F401
