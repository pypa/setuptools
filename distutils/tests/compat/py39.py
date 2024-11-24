import sys

if sys.version_info >= (3, 10):
    from test.support.import_helper import (
        CleanImport as CleanImport,
        DirsOnSysPath as DirsOnSysPath,
    )
    from test.support.os_helper import (
        EnvironmentVarGuard as EnvironmentVarGuard,
        rmtree as rmtree,
        skip_unless_symlink as skip_unless_symlink,
        unlink as unlink,
    )
else:
    from test.support import (
        CleanImport as CleanImport,
        DirsOnSysPath as DirsOnSysPath,
        EnvironmentVarGuard as EnvironmentVarGuard,
        rmtree as rmtree,
        skip_unless_symlink as skip_unless_symlink,
        unlink as unlink,
    )
