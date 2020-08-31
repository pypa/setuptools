# flake8: noqa

import contextlib
import builtins

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


# From Python 3.9
@contextlib.contextmanager
def _save_restore_warnings_filters():
    old_filters = warnings.filters[:]
    try:
        yield
    finally:
        warnings.filters[:] = old_filters


try:
    from test.support.warnings_helper import save_restore_warnings_filters
except (ModuleNotFoundError, ImportError):
    save_restore_warnings_filters = _save_restore_warnings_filters
