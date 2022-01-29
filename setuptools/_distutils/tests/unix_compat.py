import sys
import unittest

try:
    import grp
    import pwd
except ImportError:
    grp = pwd = None


UNIX_ID_SUPPORT = grp and pwd
UID_0_SUPPORT = UNIX_ID_SUPPORT and sys.platform != "cygwin"

require_unix_id = unittest.skipUnless(
    UNIX_ID_SUPPORT, "Requires grp and pwd support")
require_uid_0 = unittest.skipUnless(UID_0_SUPPORT, "Requires UID 0 support")
