import sys

if sys.version_info[:2] >= (3, 8):  # pragma: no cover
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version
else:  # pragma: no cover
    try:
        from importlib_metadata import PackageNotFoundError, version
    except ImportError:
        from pkg_resources import DistributionNotFound as PackageNotFoundError

        def version(name):
            import pkg_resources

            return pkg_resources.get_distribution(name).version


try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
