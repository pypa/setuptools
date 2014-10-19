# From http://stackoverflow.com/questions/19622133/python-set-hide-attribute-on-folders-in-windows-os

import ctypes


def hide_file(path):
    """Sets the hidden attribute on a file or directory

    `path` must be unicode; be careful that you escape backslashes or use raw
    string literals - e.g.: `u'G:\\Dir\\folder1'` or `ur'G:\Dir\folder1'`.
    """

    SetFileAttributesW = ctypes.windll.kernel32.SetFileAttributesW

    FILE_ATTRIBUTE_HIDDEN = 0x02

    ret = SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)
    if not ret:
        raise ctypes.WinError()
