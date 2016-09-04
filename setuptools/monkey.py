"""
Monkey patching of distutils.
"""


__all__ = []
"everything is private"


def _get_unpatched(cls):
    """Protect against re-patching the distutils if reloaded

    Also ensures that no other distutils extension monkeypatched the distutils
    first.
    """
    while cls.__module__.startswith('setuptools'):
        cls, = cls.__bases__
    if not cls.__module__.startswith('distutils'):
        raise AssertionError(
            "distutils has already been patched by %r" % cls
        )
    return cls
