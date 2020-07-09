import re
import pathlib
import contextlib


# from jaraco.context
class suppress(contextlib.suppress, contextlib.ContextDecorator):
    """
    A version of contextlib.suppress with decorator support.

    >>> @suppress(KeyError)
    ... def key_error():
    ...     {}['']
    >>> key_error()
    """


@suppress(Exception)
def is_debian():
    issue = pathlib.Path('/etc/issue').read_text()
    return bool(re.search('(debian|buntu|mint)', issue, re.IGNORE_CASE))
