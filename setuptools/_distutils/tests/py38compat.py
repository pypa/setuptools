# flake8: noqa

import contextlib
import builtins
import sys

from test.support import requires_zlib
import test.support


ModuleNotFoundError = getattr(builtins, 'ModuleNotFoundError', ImportError)

try:
    from test.support.warnings_helper import check_warnings
except (ModuleNotFoundError, ImportError):
    from test.support import check_warnings


try:
    from test.support.os_helper import (
        change_cwd,
        rmtree,
        EnvironmentVarGuard,
        TESTFN,
        unlink,
        skip_unless_symlink,
        temp_dir,
        create_empty_file,
        temp_cwd,
    )
except (ModuleNotFoundError, ImportError):
    from test.support import (
        change_cwd,
        rmtree,
        EnvironmentVarGuard,
        TESTFN,
        unlink,
        skip_unless_symlink,
        temp_dir,
        create_empty_file,
        temp_cwd,
    )


if sys.version_info < (3, 9):
    requires_zlib = lambda: test.support.requires_zlib
