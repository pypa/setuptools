import os
import errno
import sys


PY32 = sys.version_info >= (3, 2)


def _makedirs_31(path, exist_ok=False):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


makedirs = os.makedirs if PY32 else _makedirs_31
